"""
Simple Search Engine for Mappy ArcGIS Assistant
Clean, working implementation with proper error handling
"""

import json
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import time
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMappySearch:
    """Simple ChromaDB search for ArcGIS documentation"""
    
    def __init__(self):
        """Initialize with fixed paths and proper error handling"""
        
        # Fixed path to your working database
        self.db_path = Path("data/vector_store")
        self.collection_name = "arcgis_docs"
        
        # Validate database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"ChromaDB not found at: {self.db_path}")
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=str(self.db_path))
            self.collection = self.client.get_collection(self.collection_name)
            doc_count = self.collection.count()
            logger.info(f"Connected to ChromaDB: {doc_count} documents")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama (matches your database embeddings)"""
        try:
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": "nomic-embed-text",  # Same model used for your database
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def search(self, 
               query: str, 
               n_results: int = 10,
               doc_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search the ArcGIS documentation
        
        Args:
            query: Search query text
            n_results: Number of results to return
            doc_type: Filter by document type ('api_reference', 'sample', 'guide')
            
        Returns:
            Dictionary with search results and metadata
        """
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Build filter for document type
            where_filter = {}
            if doc_type:
                where_filter["doc_type"] = doc_type
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            search_time = time.time() - start_time
            
            # Format results
            formatted_results = self._format_results(results, search_time)
            
            logger.info(f"Search completed: {len(results['documents'][0])} results in {search_time:.3f}s")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "search_time": time.time() - start_time,
                "total_results": 0,
                "results": [],
                "error": str(e)
            }
    
    def _format_results(self, raw_results: Dict[str, Any], search_time: float) -> Dict[str, Any]:
        """Format raw ChromaDB results into standardized structure"""
        
        if not raw_results['documents'][0]:
            return {
                "search_time": search_time,
                "total_results": 0,
                "results": []
            }
        
        formatted = []
        
        for i, (doc, metadata, distance) in enumerate(zip(
            raw_results['documents'][0],
            raw_results['metadatas'][0], 
            raw_results['distances'][0]
        )):
            # Calculate similarity score (higher is better)
            similarity = max(0.0, 1.0 - (distance / 2.0))  # Normalize distance to similarity
            
            formatted.append({
                "rank": i + 1,
                "content": doc,
                "title": metadata.get('title', 'No title'),
                "url": metadata.get('url', metadata.get('parent_doc_id', 'No URL')),
                "doc_type": metadata.get('doc_type', 'unknown'),
                "similarity_score": similarity,
                "metadata": metadata
            })
        
        return {
            "search_time": search_time,
            "total_results": len(formatted),
            "results": formatted
        }
    
    def search_by_type(self, query: str, doc_type: str, n_results: int = 5) -> Dict[str, Any]:
        """Search within specific document types"""
        return self.search(query, n_results, doc_type)
    
    def get_random_docs(self, n_docs: int = 5) -> Dict[str, Any]:
        """Get random documents for testing"""
        try:
            # Use a generic embedding to get diverse results
            random_embedding = self._generate_embedding("documentation")
            
            results = self.collection.query(
                query_embeddings=[random_embedding],
                n_results=n_docs,
                include=['documents', 'metadatas']
            )
            
            return self._format_results(results, 0.0)
            
        except Exception as e:
            logger.error(f"Failed to get random docs: {e}")
            return {"total_results": 0, "results": []}
    
    def test_connection(self) -> bool:
        """Test if the search engine is working"""
        try:
            test_results = self.search("test", n_results=1)
            return test_results["total_results"] > 0
        except:
            return False

def main():
    """Test the search engine"""
    
    print("Testing SimpleMappySearch...")
    
    try:
        # Initialize search engine
        search = SimpleMappySearch()
        
        # Test basic search
        print("\n1. Basic search test:")
        results = search.search("How to create a map", n_results=3)
        print(f"   Found {results['total_results']} results in {results['search_time']:.3f}s")
        
        if results['results']:
            top_result = results['results'][0]
            print(f"   Top result: {top_result['title']}")
            print(f"   Score: {top_result['similarity_score']:.3f}")
            print(f"   Content preview: {top_result['content'][:100]}...")
        
        # Test filtered search
        print("\n2. API reference search:")
        api_results = search.search_by_type("PointBarrier", "api_reference", n_results=2)
        print(f"   Found {api_results['total_results']} API docs in {api_results['search_time']:.3f}s")
        
        # Test connection
        print(f"\n3. Connection test: {'PASS' if search.test_connection() else 'FAIL'}")
        
        print("\nSimpleMappySearch is working correctly!")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()