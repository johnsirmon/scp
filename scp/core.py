"""
Core SCP (Support Context Protocol) manager.
Main orchestration layer that coordinates memory, search, and parsing.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
import json

from .models import (
    SupportCase, CaseQuery, CaseUpdate, SearchResult, 
    SCPStats, Priority, Status
)
from .memory import MemoryStore
from .parsers import ICMParser, LogParser
from .search import VectorSearchEngine, SimpleSearchEngine, FAISS_AVAILABLE


class SCPManager:
    """
    Main SCP manager that orchestrates all components.
    Provides high-level interface for case management and search.
    """
    
    def __init__(self, 
                 data_dir: str = "./scp_data",
                 use_vector_search: bool = True,
                 vector_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the SCP manager.
        
        Args:
            data_dir: Directory for persistent storage
            use_vector_search: Whether to use vector search (requires FAISS)
            vector_model: Sentence transformer model for vector search
        """
        self.data_dir = data_dir
        
        # Initialize components
        self.memory = MemoryStore(data_dir)
        self.icm_parser = ICMParser()
        self.log_parser = LogParser()
        
        # Initialize search engine
        if use_vector_search and FAISS_AVAILABLE:
            try:
                self.search_engine = VectorSearchEngine(
                    model_name=vector_model, 
                    data_dir=data_dir
                )
                self.vector_search_enabled = True
            except Exception as e:
                print(f"Failed to initialize vector search: {e}")
                self.search_engine = SimpleSearchEngine()
                self.vector_search_enabled = False
        else:
            self.search_engine = SimpleSearchEngine()
            self.vector_search_enabled = False
        
        # Rebuild search index with existing cases
        self._sync_search_index()
    
    def add_case(self, case_data: Union[SupportCase, Dict[str, Any], str]) -> SupportCase:
        """
        Add a new case to the SCP system.
        
        Args:
            case_data: Case data as SupportCase object, dict, or raw text
            
        Returns:
            The created/updated SupportCase object
        """
        # Parse input data
        if isinstance(case_data, str):
            case = self.icm_parser.parse_icm_text(case_data)
        elif isinstance(case_data, dict):
            case = self.icm_parser.parse_json_data(case_data)
        elif isinstance(case_data, SupportCase):
            case = case_data
        else:
            raise ValueError("Invalid case_data type")
        
        # Store in memory
        self.memory.add_case(case)
        
        # Update search index
        self.search_engine.add_case(case)
        
        return case
    
    def get_case(self, case_id: str) -> Optional[SupportCase]:
        """
        Retrieve a case by ID.
        
        Args:
            case_id: Case identifier
            
        Returns:
            SupportCase object or None if not found
        """
        return self.memory.get_case(case_id)
    
    def update_case(self, case_id: str, updates: Union[CaseUpdate, Dict[str, Any]]) -> Optional[SupportCase]:
        """
        Update an existing case.
        
        Args:
            case_id: Case identifier
            updates: Updates to apply (CaseUpdate object or dict)
            
        Returns:
            Updated SupportCase object or None if not found
        """
        case = self.memory.get_case(case_id)
        if not case:
            return None
        
        # Convert updates to dict if needed
        if isinstance(updates, CaseUpdate):
            update_dict = updates.dict(exclude_unset=True)
        else:
            update_dict = updates
        
        # Apply updates
        for field, value in update_dict.items():
            if hasattr(case, field):
                # Handle list fields (append instead of replace)
                if field in ['symptoms', 'error_messages', 'reproduction_steps', 'notes']:
                    if isinstance(value, list):
                        current_list = getattr(case, field, [])
                        current_list.extend(value)
                        setattr(case, field, current_list)
                else:
                    setattr(case, field, value)
        
        # Update timestamp
        case.updated_at = datetime.utcnow()
        
        # Store updated case
        self.memory.add_case(case)
        
        # Update search index
        self.search_engine.update_case(case)
        
        return case
    
    def delete_case(self, case_id: str) -> bool:
        """
        Delete a case from the system.
        
        Args:
            case_id: Case identifier
            
        Returns:
            True if case was deleted, False if not found
        """
        # Remove from memory
        deleted = self.memory.delete_case(case_id)
        
        if deleted:
            # Remove from search index
            self.search_engine.remove_case(case_id)
        
        return deleted
    
    def search_cases(self, query: Union[str, CaseQuery]) -> List[SearchResult]:
        """
        Search for cases using text query and filters.
        
        Args:
            query: Search query (string or CaseQuery object)
            
        Returns:
            List of SearchResult objects
        """
        if isinstance(query, str):
            query_obj = CaseQuery(query=query)
        else:
            query_obj = query
        
        # Get cases from memory with basic filters
        cases = self.memory.search_cases(
            query=query_obj.query,
            status_filter=query_obj.status_filter,
            priority_filter=query_obj.priority_filter,
            case_ids=query_obj.case_ids
        )
        
        # Apply date filters
        if query_obj.date_from or query_obj.date_to:
            filtered_cases = []
            for case in cases:
                if query_obj.date_from and case.created_at < query_obj.date_from:
                    continue
                if query_obj.date_to and case.created_at > query_obj.date_to:
                    continue
                filtered_cases.append(case)
            cases = filtered_cases
        
        # Apply tag filters
        if query_obj.tags:
            tag_set = set(query_obj.tags)
            filtered_cases = []
            for case in cases:
                case_tags = {tag.name for tag in case.tags}
                if tag_set & case_tags:  # Any tag matches
                    filtered_cases.append(case)
            cases = filtered_cases
        
        # Use vector search for ranking if available
        if self.vector_search_enabled and query_obj.query:
            # Get similarity scores from vector search
            vector_results = self.search_engine.search(
                query_obj.query, 
                k=len(cases) if cases else 100
            )
            
            # Create case ID to score mapping
            score_map = {case_id: score for case_id, score in vector_results}
            
            # Create search results with scores
            search_results = []
            for case in cases:
                similarity_score = score_map.get(case.case_id, 0.0)
                result = SearchResult(
                    case=case,
                    similarity_score=similarity_score,
                    matched_fields=[]  # TODO: implement field matching
                )
                search_results.append(result)
            
            # Sort by similarity score
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
        else:
            # Simple search results without scoring
            search_results = [
                SearchResult(case=case, similarity_score=1.0, matched_fields=[])
                for case in cases
            ]
        
        # Apply limit
        return search_results[:query_obj.limit]
    
    def find_similar_cases(self, 
                          case_id: str, 
                          limit: int = 5,
                          threshold: float = 0.1) -> List[SearchResult]:
        """
        Find cases similar to the given case.
        
        Args:
            case_id: Case ID to find similarities for
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of SearchResult objects
        """
        case = self.memory.get_case(case_id)
        if not case:
            return []
        
        # Get similar case IDs from search engine
        similar_results = self.search_engine.find_similar_cases(
            case, k=limit, threshold=threshold
        )
        
        # Convert to SearchResult objects
        search_results = []
        for similar_case_id, score in similar_results:
            if similar_case_id != case_id:  # Exclude self
                similar_case = self.memory.get_case(similar_case_id)
                if similar_case:
                    result = SearchResult(
                        case=similar_case,
                        similarity_score=score,
                        matched_fields=[]
                    )
                    search_results.append(result)
        
        return search_results
    
    def add_case_logs(self, 
                     case_id: str, 
                     log_content: str,
                     source: str = "manual",
                     log_format: str = "text") -> bool:
        """
        Add log entries to a case.
        
        Args:
            case_id: Case identifier
            log_content: Raw log content
            source: Log source identifier
            log_format: Format of logs ("text" or "json")
            
        Returns:
            True if logs were added successfully
        """
        case = self.memory.get_case(case_id)
        if not case:
            return False
        
        # Parse logs based on format
        if log_format == "json":
            try:
                log_data = json.loads(log_content)
                if isinstance(log_data, list):
                    log_entries = self.log_parser.parse_structured_logs(log_data, source)
                else:
                    log_entries = self.log_parser.parse_structured_logs([log_data], source)
            except json.JSONDecodeError:
                return False
        else:
            log_entries = self.log_parser.parse_log_content(log_content, source)
        
        # Add logs to case
        case.logs.extend(log_entries)
        case.updated_at = datetime.utcnow()
        
        # Update case in memory
        self.memory.add_case(case)
        
        # Update search index
        self.search_engine.update_case(case)
        
        return True
    
    def get_case_context(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get structured context for a case suitable for LLM injection.
        
        Args:
            case_id: Case identifier
            
        Returns:
            Dictionary with structured case context
        """
        case = self.memory.get_case(case_id)
        if not case:
            return None
        
        # Find related cases
        similar_cases = self.find_similar_cases(case_id, limit=3)
        
        context = {
            "case": case.dict(),
            "similar_cases": [
                {
                    "case_id": result.case.case_id,
                    "title": result.case.title,
                    "similarity_score": result.similarity_score,
                    "status": result.case.status,
                    "solution": result.case.solution
                }
                for result in similar_cases
            ],
            "summary": {
                "total_logs": len(case.logs),
                "tag_count": len(case.tags),
                "escalation_flags": len(case.escalation_flags),
                "days_open": (datetime.utcnow() - case.created_at).days
            }
        }
        
        return context
    
    def get_stats(self) -> SCPStats:
        """
        Get system statistics.
        
        Returns:
            SCPStats object with system metrics
        """
        return self.memory.get_stats()
    
    def export_data(self, filepath: Optional[str] = None) -> str:
        """
        Export all case data to JSON.
        
        Args:
            filepath: Optional file path to save data
            
        Returns:
            JSON string of exported data
        """
        return self.memory.export_to_json(filepath)
    
    def import_data(self, json_data: str) -> int:
        """
        Import case data from JSON.
        
        Args:
            json_data: JSON string containing case data
            
        Returns:
            Number of cases imported
        """
        imported_count = self.memory.import_from_json(json_data)
        
        # Rebuild search index after import
        self._sync_search_index()
        
        return imported_count
    
    def save_all(self) -> None:
        """Save all data to disk."""
        self.memory.save_to_disk()
        self.search_engine.save_index()
    
    def _sync_search_index(self) -> None:
        """Synchronize the search index with memory store."""
        all_cases = self.memory.get_all_cases()
        if all_cases:
            self.search_engine.rebuild_index(all_cases)
    
    def get_case_ids(self) -> List[str]:
        """
        Get all case IDs in the system.
        
        Returns:
            List of case IDs
        """
        return [case.case_id for case in self.memory.get_all_cases()]
    
    def bulk_update_tags(self, tag_mappings: Dict[str, List[str]]) -> int:
        """
        Bulk update tags for multiple cases.
        
        Args:
            tag_mappings: Dict mapping case_ids to lists of tag names
            
        Returns:
            Number of cases updated
        """
        updated_count = 0
        
        for case_id, tags in tag_mappings.items():
            case = self.memory.get_case(case_id)
            if case:
                for tag_name in tags:
                    case.add_tag(tag_name, source="bulk_update")
                case.updated_at = datetime.utcnow()
                self.memory.add_case(case)
                self.search_engine.update_case(case)
                updated_count += 1
        
        return updated_count
