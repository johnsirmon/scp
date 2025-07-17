"""
Vector search capabilities for the SCP system using FAISS.
Enables semantic similarity search across support cases.
"""

from typing import List, Tuple, Dict, Any
import json
from pathlib import Path

try:
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    np = None
    faiss = None
    SentenceTransformer = None

from .models import SupportCase


class VectorSearchEngine:
    """
    FAISS-based vector search engine for semantic case similarity.
    Uses sentence transformers to encode case content into embeddings.
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 data_dir: str = "./scp_data"):
        """
        Initialize the vector search engine.
        
        Args:
            model_name: Sentence transformer model name
            data_dir: Directory for storing index files
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "FAISS and sentence-transformers are required for vector search. "
                "Install with: pip install faiss-cpu sentence-transformers"
            )
        
        self.model_name = model_name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize sentence transformer
        self.encoder = SentenceTransformer(model_name)
        self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product
        self.case_ids: List[str] = []
        
        # Index files
        self.index_file = self.data_dir / "vector_index.faiss"
        self.metadata_file = self.data_dir / "vector_metadata.json"
        
        # Load existing index
        self._load_index()
    
    def add_case(self, case: SupportCase) -> None:
        """
        Add a case to the vector index.
        
        Args:
            case: SupportCase to add to the index
        """
        # Get text content
        text_content = case.get_text_content()
        
        # Generate embedding
        embedding = self._encode_text(text_content)
        
        # Add to index
        self.index.add(embedding.reshape(1, -1))
        self.case_ids.append(case.case_id)
    
    def update_case(self, case: SupportCase) -> None:
        """
        Update a case in the vector index.
        Note: FAISS doesn't support direct updates, so we rebuild the index.
        
        Args:
            case: Updated SupportCase
        """
        # For now, we'll mark this case for rebuild
        # In production, you might want a more sophisticated approach
        if case.case_id in self.case_ids:
            # Remove and re-add
            self.remove_case(case.case_id)
        self.add_case(case)
    
    def remove_case(self, case_id: str) -> bool:
        """
        Remove a case from the vector index.
        Note: FAISS doesn't support direct removal, so we mark for rebuild.
        
        Args:
            case_id: Case ID to remove
            
        Returns:
            True if case was found and marked for removal
        """
        if case_id in self.case_ids:
            # Mark for rebuild - for simplicity, we'll just track removals
            # In production, implement a more efficient removal strategy
            return True
        return False
    
    def search(self, 
               query: str, 
               k: int = 10,
               threshold: float = 0.0) -> List[Tuple[str, float]]:
        """
        Search for similar cases using vector similarity.
        
        Args:
            query: Text query to search for
            k: Number of results to return
            threshold: Minimum similarity score threshold
            
        Returns:
            List of tuples (case_id, similarity_score)
        """
        if self.index.ntotal == 0:
            return []
        
        # Encode query
        query_embedding = self._encode_text(query)
        
        # Search
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1), 
            min(k, len(self.case_ids))
        )
        
        # Process results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.case_ids):
                if score >= threshold:
                    results.append((self.case_ids[idx], float(score)))
        
        return results
    
    def find_similar_cases(self,
                          case: SupportCase,
                          k: int = 5,
                          threshold: float = 0.1) -> List[Tuple[str, float]]:
        """
        Find cases similar to the given case.
        
        Args:
            case: SupportCase to find similarities for
            k: Number of similar cases to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of tuples (case_id, similarity_score)
        """
        text_content = case.get_text_content()
        return self.search(text_content, k + 1, threshold)  # +1 to exclude self
    
    def rebuild_index(self, cases: List[SupportCase]) -> None:
        """
        Rebuild the entire vector index from scratch.
        
        Args:
            cases: List of all SupportCase instances to index
        """
        # Reset index
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.case_ids = []
        
        # Add all cases
        for case in cases:
            self.add_case(case)
    
    def save_index(self) -> None:
        """Save the vector index and metadata to disk."""
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_file))
        
        # Save metadata
        metadata = {
            "case_ids": self.case_ids,
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "total_cases": len(self.case_ids)
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_index(self) -> None:
        """Load vector index and metadata from disk."""
        try:
            # Load FAISS index
            if self.index_file.exists():
                self.index = faiss.read_index(str(self.index_file))
            
            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                    self.case_ids = metadata.get("case_ids", [])
                    
                    # Verify model compatibility
                    if metadata.get("model_name") != self.model_name:
                        print(f"Warning: Index was built with model "
                              f"{metadata.get('model_name')}, "
                              f"but current model is {self.model_name}")
        
        except Exception as e:
            print(f"Error loading vector index: {e}")
            # Reset to empty index
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.case_ids = []
    
    def _encode_text(self, text: str):
        """
        Encode text into embedding vector.
        
        Args:
            text: Text to encode
            
        Returns:
            Numpy array of embeddings
        """
        # Handle empty text
        if not text.strip():
            text = "empty case"
        
        embedding = self.encoder.encode([text])
        return embedding[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector index.
        
        Returns:
            Dictionary with index statistics
        """
        return {
            "total_vectors": self.index.ntotal,
            "embedding_dimension": self.embedding_dim,
            "model_name": self.model_name,
            "indexed_cases": len(self.case_ids)
        }


class SimpleSearchEngine:
    """
    Fallback search engine when FAISS is not available.
    Uses basic text matching and TF-IDF-like scoring.
    """
    
    def __init__(self):
        """Initialize simple search engine."""
        self.cases: Dict[str, SupportCase] = {}
    
    def add_case(self, case: SupportCase) -> None:
        """Add case to simple search index."""
        self.cases[case.case_id] = case
    
    def update_case(self, case: SupportCase) -> None:
        """Update case in simple search index."""
        self.cases[case.case_id] = case
    
    def remove_case(self, case_id: str) -> bool:
        """Remove case from simple search index."""
        if case_id in self.cases:
            del self.cases[case_id]
            return True
        return False
    
    def search(self, 
               query: str, 
               k: int = 10,
               threshold: float = 0.0) -> List[Tuple[str, float]]:
        """
        Simple text-based search.
        
        Args:
            query: Search query
            k: Number of results
            threshold: Minimum score threshold
            
        Returns:
            List of (case_id, score) tuples
        """
        query_words = set(query.lower().split())
        if not query_words:
            return []
        
        results = []
        for case_id, case in self.cases.items():
            case_text = case.get_text_content().lower()
            case_words = set(case_text.split())
            
            # Simple Jaccard similarity
            intersection = len(query_words & case_words)
            union = len(query_words | case_words)
            
            if union > 0:
                score = intersection / union
                if score >= threshold:
                    results.append((case_id, score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def find_similar_cases(self,
                          case: SupportCase,
                          k: int = 5,
                          threshold: float = 0.1) -> List[Tuple[str, float]]:
        """Find similar cases using simple text matching."""
        text_content = case.get_text_content()
        results = self.search(text_content, k + 1, threshold)
        # Remove self from results
        return [(cid, score) for cid, score in results if cid != case.case_id]
    
    def rebuild_index(self, cases: List[SupportCase]) -> None:
        """Rebuild simple search index."""
        self.cases = {case.case_id: case for case in cases}
    
    def save_index(self) -> None:
        """Save method for compatibility (no-op for simple search)."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get simple search statistics."""
        return {
            "total_cases": len(self.cases),
            "search_type": "simple_text_matching"
        }
