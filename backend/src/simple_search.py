"""
Production search service for Mappy ArcGIS Assistant using Qdrant Cloud
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Qdrant imports
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Vertex AI imports
from vertexai.language_models import TextEmbeddingModel
import vertexai

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleMappySearch:
    """Production Qdrant search service using Vertex AI embeddings"""
    
    def __init__(self):
        """Initialize search service with Qdrant Cloud and Vertex AI"""
        
        # Initialize Vertex AI
        self._initialize_vertex_ai()
        
        # Load embedding model
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        # Qdrant configuration
        self.qdrant_url = os.getenv("QDRANT_URL", "https://7c22af82-0689-41e8-86d2-705b20cac60a.us-west-1-0.aws.cloud.qdrant.io")
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = "arcgis_docs"
        
        if not self.api_key:
            raise ValueError("QDRANT_API_KEY not found in environment variables")
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.api_key,
        )
        
        # Test connection and get collection info
        try:
            collection_info = self.client.get_collection(self.collection_name)
            vector_count = collection_info.vectors_count or 0
            logger.info(f"Connected to Qdrant: {vector_count} documents")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI with project credentials"""
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        credentials_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT not found in environment variables")
        
        # Handle JSON credentials string for deployment
        if credentials_json:
            import json
            import tempfile
            try:
                credentials_dict = json.loads(credentials_json)
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                    json.dump(credentials_dict, f)
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
                logger.info("Using JSON credentials from environment variable")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
                raise
        elif credentials_file:
            # If credentials file path is set, make sure it exists
            if not os.path.exists(credentials_file):
                # Try relative to project root
                relative_path = os.path.join(os.getcwd(), credentials_file)
                if os.path.exists(relative_path):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = relative_path
                    logger.info(f"Using credentials file: {relative_path}")
                else:
                    logger.error(f"Credentials file not found: {credentials_file}")
                    raise FileNotFoundError(f"Credentials file not found: {credentials_file}")
            else:
                logger.info(f"Using credentials file: {credentials_file}")
        else:
            logger.error("No Google Cloud credentials found. Set either GOOGLE_APPLICATION_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS")
            raise ValueError("No Google Cloud credentials found")
        
        try:
            vertexai.init(project=project_id, location="us-central1")
            logger.info(f"Initialized Vertex AI for project: {project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query using Vertex AI"""
        try:
            # Generate embedding using same model as documents
            embeddings = self.embedding_model.get_embeddings([query])
            embedding_vector = embeddings[0].values
            
            logger.debug(f"Generated query embedding: {len(embedding_vector)} dimensions")
            return embedding_vector
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
    
    def search(self, 
               query: str, 
               limit: int = 10,
               n_results: Optional[int] = None,  # Backward compatibility
               score_threshold: float = 0.0,
               doc_type_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for similar documents using Qdrant
        
        Args:
            query: Search query text
            limit: Maximum number of results
            n_results: Backward compatibility alias for limit
            score_threshold: Minimum similarity score
            doc_type_filter: Filter by document type (e.g., 'sample', 'api_reference')
        
        Returns:
            Dictionary with results and metadata (same format as original ChromaDB version)
        """
        # Handle backward compatibility
        if n_results is not None:
            limit = n_results
            
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = self._get_query_embedding(query)
            
            # Build filter if specified
            query_filter = None
            if doc_type_filter:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="doc_type",
                            match=MatchValue(value=doc_type_filter)
                        )
                    ]
                )
            
            # Perform search
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results to match original ChromaDB format
            results = []
            for result in search_results.points:
                # Extract metadata
                payload = result.payload or {}
                
                # Calculate similarity score (Qdrant returns distance, convert to similarity)
                similarity_score = max(0.0, min(1.0, result.score))
                
                formatted_result = {
                    'id': str(result.id),
                    'content': payload.get('content', ''),
                    'similarity_score': similarity_score,
                    'metadata': {
                        'title': payload.get('metadata_title', 'No title'),
                        'url': payload.get('metadata_url', ''),
                        'doc_type': payload.get('doc_type', ''),
                        'chunk_type': payload.get('chunk_type', ''),
                        'parent_doc_id': payload.get('parent_doc_id', ''),
                        'token_count': payload.get('token_count', 0),
                        'example_count': payload.get('metadata_example_count', 0),
                    }
                }
                results.append(formatted_result)
            
            search_time = time.time() - start_time
            logger.info(f"Search completed: {len(results)} results in {search_time:.3f}s")
            
            # Return in original ChromaDB format that RAG engine expects
            return {
                'results': results,
                'total_results': len(results),
                'search_time': search_time,
                'query': query,
                'limit': limit
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'vectors_count': collection_info.vectors_count,
                'indexed_vectors_count': collection_info.indexed_vectors_count,
                'points_count': collection_info.points_count,
                'status': collection_info.status,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}


# Test function
def test_search():
    """Test search functionality"""
    try:
        search = SimpleMappySearch()
        
        test_queries = [
            "how to create a map with ArcGIS",
            "elevation layer 3D",
            "JavaScript SDK sample code",
            "add markers to map",
            "popup configuration"
        ]
        
        print("Testing search with Qdrant Cloud...")
        print("=" * 60)
        
        for query in test_queries:
            print(f"Query: '{query}'")
            print("-" * 40)
            
            search_response = search.search(query, limit=3)
            results = search_response['results']
            
            for i, result in enumerate(results, 1):
                print(f"Rank {i}: {result['metadata']['title']}")
                print(f"Score: {result['similarity_score']:.3f}")
                print(f"Type: {result['metadata']['doc_type']}")
                print(f"Content: {result['content'][:100]}...")
                print()
            
            print(f"Search time: {search_response['search_time']:.3f}s")
            print("=" * 40)
            print()
    
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    test_search()