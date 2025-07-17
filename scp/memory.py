"""
In-memory storage system for the SCP with persistence capabilities.
Handles case data storage, retrieval, and JSON serialization.
"""

import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import Lock

from .models import SupportCase, SCPStats, Status, Priority


class MemoryStore:
    """
    Thread-safe in-memory storage for support cases.
    Provides persistence through JSON export/import and pickle serialization.
    """
    
    def __init__(self, data_dir: str = "./scp_data"):
        """
        Initialize the memory store.
        
        Args:
            data_dir: Directory for persistent storage files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # In-memory storage
        self._cases: Dict[str, SupportCase] = {}
        self._lock = Lock()
        
        # Persistence files
        self._json_file = self.data_dir / "cases.json"
        self._pickle_file = self.data_dir / "cases.pkl"
        
        # Load existing data
        self._load_data()
    
    def add_case(self, case: SupportCase) -> None:
        """
        Add or update a case in memory.
        
        Args:
            case: SupportCase instance to store
        """
        with self._lock:
            case.updated_at = datetime.utcnow()
            self._cases[case.case_id] = case
    
    def get_case(self, case_id: str) -> Optional[SupportCase]:
        """
        Retrieve a case by ID.
        
        Args:
            case_id: Case identifier
            
        Returns:
            SupportCase instance or None if not found
        """
        with self._lock:
            return self._cases.get(case_id)
    
    def get_all_cases(self) -> List[SupportCase]:
        """
        Get all cases from memory.
        
        Returns:
            List of all SupportCase instances
        """
        with self._lock:
            return list(self._cases.values())
    
    def get_cases_by_status(self, status: Status) -> List[SupportCase]:
        """
        Get all cases with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of matching SupportCase instances
        """
        with self._lock:
            return [case for case in self._cases.values() 
                   if case.status == status]
    
    def get_cases_by_priority(self, priority: Priority) -> List[SupportCase]:
        """
        Get all cases with a specific priority.
        
        Args:
            priority: Priority to filter by
            
        Returns:
            List of matching SupportCase instances
        """
        with self._lock:
            return [case for case in self._cases.values() 
                   if case.priority == priority]
    
    def delete_case(self, case_id: str) -> bool:
        """
        Delete a case from memory.
        
        Args:
            case_id: Case identifier to delete
            
        Returns:
            True if case was deleted, False if not found
        """
        with self._lock:
            if case_id in self._cases:
                del self._cases[case_id]
                return True
            return False
    
    def case_exists(self, case_id: str) -> bool:
        """
        Check if a case exists in memory.
        
        Args:
            case_id: Case identifier to check
            
        Returns:
            True if case exists, False otherwise
        """
        with self._lock:
            return case_id in self._cases
    
    def get_case_count(self) -> int:
        """
        Get total number of cases in memory.
        
        Returns:
            Number of cases
        """
        with self._lock:
            return len(self._cases)
    
    def search_cases(self, 
                    query: str = "", 
                    status_filter: Optional[List[Status]] = None,
                    priority_filter: Optional[List[Priority]] = None,
                    case_ids: Optional[List[str]] = None) -> List[SupportCase]:
        """
        Search cases based on text query and filters.
        
        Args:
            query: Text to search for in case content
            status_filter: List of statuses to filter by
            priority_filter: List of priorities to filter by
            case_ids: Specific case IDs to search within
            
        Returns:
            List of matching SupportCase instances
        """
        with self._lock:
            cases = list(self._cases.values())
            
            # Filter by case IDs if specified
            if case_ids:
                cases = [case for case in cases if case.case_id in case_ids]
            
            # Filter by status
            if status_filter:
                cases = [case for case in cases if case.status in status_filter]
            
            # Filter by priority
            if priority_filter:
                cases = [case for case in cases 
                        if case.priority in priority_filter]
            
            # Text search
            if query:
                query_lower = query.lower()
                filtered_cases = []
                for case in cases:
                    case_text = case.get_text_content().lower()
                    if query_lower in case_text:
                        filtered_cases.append(case)
                cases = filtered_cases
            
            return cases
    
    def get_stats(self) -> SCPStats:
        """
        Generate statistics about the stored cases.
        
        Returns:
            SCPStats instance with system statistics
        """
        with self._lock:
            cases = list(self._cases.values())
            
            # Count by status
            status_counts = {}
            for status in Status:
                status_counts[status] = sum(1 for case in cases 
                                          if case.status == status)
            
            # Count by priority
            priority_counts = {}
            for priority in Priority:
                priority_counts[priority] = sum(1 for case in cases 
                                              if case.priority == priority)
            
            # Calculate average resolution time
            resolved_cases = [case for case in cases 
                            if case.status == Status.RESOLVED]
            avg_resolution_time = None
            if resolved_cases:
                total_time = sum(
                    case.metrics.resolution_time_hours or 0 
                    for case in resolved_cases
                )
                avg_resolution_time = total_time / len(resolved_cases)
            
            # Top tags
            tag_counts = {}
            for case in cases:
                for tag in case.tags:
                    tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
            
            top_tags = [
                {"name": name, "count": count}
                for name, count in sorted(tag_counts.items(), 
                                        key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Memory usage estimation (rough)
            memory_usage_mb = (
                len(pickle.dumps(self._cases)) / (1024 * 1024)
            )
            
            return SCPStats(
                total_cases=len(cases),
                cases_by_status=status_counts,
                cases_by_priority=priority_counts,
                avg_resolution_time_hours=avg_resolution_time,
                top_tags=top_tags,
                memory_usage_mb=memory_usage_mb
            )
    
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """
        Export all cases to JSON format.
        
        Args:
            filepath: Optional path to save JSON file
            
        Returns:
            JSON string representation of all cases
        """
        with self._lock:
            cases_data = [case.dict() for case in self._cases.values()]
            
            json_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_cases": len(cases_data),
                "cases": cases_data
            }
            
            json_str = json.dumps(json_data, indent=2, default=str)
            
            if filepath:
                with open(filepath, 'w') as f:
                    f.write(json_str)
            
            return json_str
    
    def import_from_json(self, json_data: str) -> int:
        """
        Import cases from JSON data.
        
        Args:
            json_data: JSON string containing case data
            
        Returns:
            Number of cases imported
        """
        data = json.loads(json_data)
        cases_data = data.get("cases", [])
        
        imported_count = 0
        for case_data in cases_data:
            try:
                case = SupportCase(**case_data)
                self.add_case(case)
                imported_count += 1
            except Exception as e:
                print(f"Error importing case {case_data.get('case_id', 'unknown')}: {e}")
        
        return imported_count
    
    def save_to_disk(self) -> None:
        """Save current state to disk (both JSON and pickle)."""
        # Save as JSON
        self.export_to_json(str(self._json_file))
        
        # Save as pickle for faster loading
        with self._lock:
            with open(self._pickle_file, 'wb') as f:
                pickle.dump(self._cases, f)
    
    def _load_data(self) -> None:
        """Load data from disk during initialization."""
        # Try pickle first (faster)
        if self._pickle_file.exists():
            try:
                with open(self._pickle_file, 'rb') as f:
                    self._cases = pickle.load(f)
                return
            except Exception:
                pass  # Fall back to JSON
        
        # Try JSON
        if self._json_file.exists():
            try:
                with open(self._json_file, 'r') as f:
                    json_data = f.read()
                self.import_from_json(json_data)
            except Exception as e:
                print(f"Error loading JSON data: {e}")
    
    def clear_all(self) -> None:
        """Clear all cases from memory (use with caution)."""
        with self._lock:
            self._cases.clear()
    
    def backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of current data.
        
        Args:
            backup_name: Optional backup name, defaults to timestamp
            
        Returns:
            Path to backup file
        """
        if not backup_name:
            backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.data_dir / f"{backup_name}.json"
        self.export_to_json(str(backup_path))
        return str(backup_path)
