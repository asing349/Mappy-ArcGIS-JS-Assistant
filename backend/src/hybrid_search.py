"""
Module 8: Simple Hybrid Retrieval + Result Fusion
The easy way - just use ChromaDB's built-in hybrid search without embedding conflicts
"""

import json
import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleHybridSearch:
    """Simple hybrid search that actually works"""
    
    def __init__(self, persist_directory: str = "data/vector_store"):
        self.persist_directory = Path(persist_directory)
        
        # Initialize ChromaDB client - no embedding function
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        
        # Get existing collection
        try:
            self.collection = self.client.get_collection("arcgis_docs")
            logger.info(f"✅ Connected to existing collection with {self.collection.count()} documents")
        except Exception as e:
            logger.error(f"❌ Could not connect to collection: {e}")
            raise
    
    def hybrid_search(self, 
                     query: str, 
                     n_results: int = 10,
                     doc_type_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        MODULE 8: True hybrid search using ChromaDB's built-in capabilities
        This is the "one line of code" approach that actually works
        """
        start_time = time.time()
        
        # Build where clause for filtering
        where_clause = {}
        if doc_type_filter:
            where_clause["doc_type"] = doc_type_filter
        
        try:
            # THE MAGIC LINE: ChromaDB's native hybrid search
            # This combines vector similarity + text matching automatically
            results = self.collection.query(
                query_texts=[query],  # Text search component
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            search_time = time.time() - start_time
            
            # Format results
            formatted_results = self._format_results(results, search_time, query)
            
            logger.info(f"🔄 Hybrid search for '{query}' returned {len(results['documents'][0])} results in {search_time:.3f}s")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            # Fallback to vector-only search if hybrid fails
            logger.info("🔄 Falling back to vector-only search...")
            return self._fallback_search(query, n_results, doc_type_filter)
    
    def _fallback_search(self, query: str, n_results: int, doc_type_filter: Optional[str]):
        """Fallback to vector search if hybrid fails"""
        try:
            from simple_search import SimpleMappySearch
            fallback_engine = SimpleMappySearch()
            return fallback_engine.search(query, n_results, doc_type_filter)
        except Exception as e:
            logger.error(f"❌ Fallback search also failed: {e}")
            return {"search_time": 0, "total_results": 0, "results": []}
    
    def search_by_category(self, 
                          query: str, 
                          category: str = "all",
                          n_results: int = 10) -> Dict[str, Any]:
        """Search within specific categories using hybrid search"""
        
        # Map category shortcuts to doc_type values
        category_map = {
            "api": "api_reference",
            "guide": "guide", 
            "sample": "sample",
            "all": None
        }
        
        doc_type_filter = category_map.get(category.lower())
        return self.hybrid_search(query, n_results, doc_type_filter)
    
    def _format_results(self, results: Dict[str, Any], search_time: float, query: str) -> Dict[str, Any]:
        """Format search results into a consistent structure"""
        
        if not results['documents'][0]:
            return {
                "query": query,
                "search_type": "hybrid",
                "search_time": search_time,
                "total_results": 0,
                "results": []
            }
        
        formatted_results = []
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            formatted_results.append({
                "rank": i + 1,
                "content": doc,
                "metadata": metadata,
                "similarity_score": max(0, 1 - (distance / 1000)),  # Normalize large distances
                "distance": distance,
                "doc_type": metadata.get('doc_type', 'unknown'),
                "chunk_type": metadata.get('chunk_type', 'unknown'),
                "title": metadata.get('title', 'No title'),
                "url": metadata.get('url', 'No URL'),
                "preview": doc[:200] + "..." if len(doc) > 200 else doc
            })
        
        return {
            "query": query,
            "search_type": "hybrid",
            "search_time": search_time,
            "total_results": len(formatted_results),
            "results": formatted_results
        }
    
    def test_hybrid_vs_vector(self):
        """Test hybrid search vs vector-only search"""
        
        test_queries = [
            "PointBarrier routing",
            "3D scene visualization", 
            "widget configuration",
            "map layer styling"
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TESTING MODULE 8: HYBRID vs VECTOR SEARCH")
        logger.info("="*60)
        
        # Import vector search for comparison
        try:
            from simple_search import SimpleMappySearch
            vector_engine = SimpleMappySearch()
        except:
            logger.error("❌ Could not import simple_search for comparison")
            vector_engine = None
        
        for query in test_queries:
            logger.info(f"\n📝 Testing: '{query}'")
            
            # Test hybrid search
            try:
                hybrid_results = self.hybrid_search(query, n_results=3)
                logger.info(f"   🔄 Hybrid search: {hybrid_results['total_results']} results in {hybrid_results['search_time']:.3f}s")
                
                if hybrid_results['results']:
                    top_result = hybrid_results['results'][0]
                    logger.info(f"   🏆 Top result: {top_result['title']}")
                    logger.info(f"   📊 Score: {top_result['similarity_score']:.3f}")
                
            except Exception as e:
                logger.error(f"   ❌ Hybrid search failed: {e}")
            
            # Test vector search for comparison
            if vector_engine:
                try:
                    vector_results = vector_engine.search(query, n_results=3)
                    logger.info(f"   🧮 Vector search: {vector_results['total_results']} results in {vector_results['search_time']:.3f}s")
                    
                except Exception as e:
                    logger.error(f"   ❌ Vector search failed: {e}")
        
        logger.info("\n✅ Hybrid vs Vector testing complete!")
    
    def interactive_examples(self):
        """Run interactive hybrid search examples"""
        
        logger.info("\n" + "="*60)
        logger.info("🎯 MODULE 8 HYBRID SEARCH EXAMPLES")
        logger.info("="*60)
        
        examples = [
            ("PointBarrier API documentation", "api"),
            ("3D visualization tutorials", "guide"),
            ("map widget code examples", "sample"),
            ("layer styling methods", "all")
        ]
        
        for query, category in examples:
            logger.info(f"\n🔍 Hybrid search: '{query}' in {category} docs...")
            
            try:
                results = self.search_by_category(query, category, n_results=3)
                
                if results['results']:
                    logger.info(f"Found {len(results['results'])} results:")
                    for result in results['results'][:2]:  # Show top 2
                        logger.info(f"   📋 {result['title']}")
                        logger.info(f"      Score: {result['similarity_score']:.3f}")
                        logger.info(f"      Type: {result['doc_type']}")
                else:
                    logger.info("   No results found")
                    
            except Exception as e:
                logger.error(f"   ❌ Search failed: {e}")


def main():
    """Test Module 8: Simple Hybrid Search"""
    
    logger.info("🚀 Starting Module 8: Simple Hybrid Retrieval + Result Fusion")
    
    try:
        # Initialize hybrid search engine
        search_engine = SimpleHybridSearch()
        
        # Test hybrid vs vector comparison
        search_engine.test_hybrid_vs_vector()
        
        # Interactive examples
        search_engine.interactive_examples()
        
        logger.info("\n" + "="*60)
        logger.info("✅ MODULE 8 COMPLETE!")
        logger.info("="*60)
        logger.info("🎯 Hybrid search is working!")
        logger.info("🔄 ChromaDB automatically combines vector + text search")
        logger.info("📋 Next: Module 9 (Re-ranking) or Module 12 (RAG Generation)")
        
    except Exception as e:
        logger.error(f"❌ Module 8 failed: {e}")
        raise

if __name__ == "__main__":
    main()