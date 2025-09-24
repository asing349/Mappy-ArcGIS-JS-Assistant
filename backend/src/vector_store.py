"""
Module 6: Vector Store + Metadata Schema
Production-grade vector storage using ChromaDB (free, local, scalable)
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import logging
from tqdm import tqdm
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArcGISVectorStore:
    """Production-grade vector store for ArcGIS documentation"""
    
    def __init__(self, 
                 persist_directory: str = "data/vector_store",
                 collection_name: str = "arcgis_docs"):
        
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False  # Privacy
            )
        )
        
        logger.info(f"✅ Initialized ChromaDB at {self.persist_directory}")
    
    def create_collection(self, reset_if_exists: bool = False) -> chromadb.Collection:
        """Create or get collection with metadata schema"""
        
        try:
            if reset_if_exists:
                try:
                    self.client.delete_collection(name=self.collection_name)
                    logger.info(f"🗑️  Deleted existing collection: {self.collection_name}")
                except:
                    pass
            
            # Create collection with distance function
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "description": "ArcGIS JavaScript SDK Documentation",
                    "embedding_model": "nomic-embed-text", 
                    "dimensions": 768,
                    "created_at": time.time()
                }
            )
            
            logger.info(f"✅ Created collection: {self.collection_name}")
            return collection
            
        except Exception as e:
            # Collection might already exist
            logger.info(f"📂 Using existing collection: {self.collection_name}")
            return self.client.get_collection(name=self.collection_name)
    
    def load_embeddings_from_file(self, embeddings_file: str) -> Dict[str, Any]:
        """Load embeddings from JSON file"""
        logger.info(f"📂 Loading embeddings from {embeddings_file}")
        
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        embeddings_count = len(data['embeddings'])
        dimensions = data['metadata']['dimensions']
        
        logger.info(f"📊 Loaded {embeddings_count:,} embeddings ({dimensions} dimensions)")
        return data
    
    def prepare_chroma_data(self, embeddings_data: Dict[str, Any]) -> Dict[str, List]:
        """Convert embeddings data to ChromaDB format"""
        logger.info("🔄 Preparing data for ChromaDB...")
        
        embeddings = []
        documents = []  # Full text content
        metadatas = []  # Searchable metadata
        ids = []
        
        for item in tqdm(embeddings_data['embeddings'], desc="Processing embeddings"):
            chunk_meta = item['chunk_metadata']
            
            # Extract content from the actual chunk content
            content = chunk_meta.get('content', '')
            if not content:
                # Fallback to title if no content
                content = chunk_meta.get('metadata', {}).get('title', 'No content')
            
            # Truncate content if too long (ChromaDB has limits)
            if len(content) > 8000:
                content = content[:8000] + "..."
            
            # Create rich, searchable metadata
            metadata = {
                # Core classification
                'doc_type': chunk_meta.get('doc_type', 'unknown'),
                'chunk_type': chunk_meta.get('chunk_type', 'unknown'),
                
                # Content metadata
                'title': chunk_meta.get('metadata', {}).get('title', ''),
                'url': chunk_meta.get('metadata', {}).get('url', ''),
                'class_name': chunk_meta.get('metadata', {}).get('class_name', ''),
                'parent_doc_id': chunk_meta.get('parent_doc_id', ''),
                
                # Metrics
                'token_count': chunk_meta.get('token_count', 0),
                'content_length': len(content),
                
                # Additional searchable fields
                'has_code_examples': 'code' in content.lower() or 'import' in content.lower(),
                'is_api_reference': chunk_meta.get('doc_type') == 'api_reference',
                'is_sample': chunk_meta.get('doc_type') == 'sample',
                'is_guide': chunk_meta.get('doc_type') == 'guide',
            }
            
            # Add domain-specific metadata
            if chunk_meta.get('metadata', {}).get('example_index') is not None:
                metadata['example_index'] = chunk_meta['metadata']['example_index']
            
            if chunk_meta.get('metadata', {}).get('member_name'):
                metadata['member_name'] = chunk_meta['metadata']['member_name']
            
            embeddings.append(item['embedding'])
            documents.append(content)
            metadatas.append(metadata)
            ids.append(item['chunk_id'])
        
        logger.info(f"✅ Prepared {len(embeddings):,} items for storage")
        
        return {
            'embeddings': embeddings,
            'documents': documents,
            'metadatas': metadatas,
            'ids': ids
        }
    
    def store_embeddings(self, 
                        embeddings_file: str,
                        batch_size: int = 1000,
                        reset_collection: bool = False) -> chromadb.Collection:
        """Store embeddings in ChromaDB with batching"""
        
        # Create collection
        collection = self.create_collection(reset_if_exists=reset_collection)
        
        # Load embeddings
        embeddings_data = self.load_embeddings_from_file(embeddings_file)
        
        # Prepare for ChromaDB
        chroma_data = self.prepare_chroma_data(embeddings_data)
        
        # Store in batches
        total_items = len(chroma_data['ids'])
        logger.info(f"🔄 Storing {total_items:,} embeddings in batches of {batch_size}")
        
        for i in tqdm(range(0, total_items, batch_size), desc="Storing batches"):
            end_idx = min(i + batch_size, total_items)
            
            batch_data = {
                'embeddings': chroma_data['embeddings'][i:end_idx],
                'documents': chroma_data['documents'][i:end_idx],
                'metadatas': chroma_data['metadatas'][i:end_idx],
                'ids': chroma_data['ids'][i:end_idx]
            }
            
            try:
                collection.add(**batch_data)
            except Exception as e:
                logger.error(f"❌ Failed to store batch {i//batch_size + 1}: {e}")
                raise
        
        # Verify storage
        stored_count = collection.count()
        logger.info(f"✅ Successfully stored {stored_count:,} embeddings")
        
        return collection
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for query using same Ollama model"""
        import requests
        
        try:
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": query
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result['embedding']
            
        except Exception as e:
            logger.error(f"❌ Failed to get query embedding: {e}")
            raise
    
    def test_search(self, collection: chromadb.Collection, query: str = "How do I create a map?"):
        """Test the vector store with a sample query"""
        logger.info(f"🔍 Testing search with query: '{query}'")
        
        try:
            # Get query embedding using same model as stored embeddings
            query_embedding = self._get_query_embedding(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],  # Use pre-computed embedding
                n_results=5,
                include=['documents', 'metadatas', 'distances']
            )
            
            logger.info("📋 Search Results:")
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )):
                logger.info(f"  {i+1}. [{metadata['doc_type']}] {metadata['title']}")
                logger.info(f"     Similarity: {1-distance:.3f} | URL: {metadata['url'][:60]}...")
                logger.info(f"     Preview: {doc[:100]}...")
                logger.info("")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search test failed: {e}")
            raise
    
    def test_filtered_search(self, collection: chromadb.Collection, 
                           query: str = "widget", doc_type: str = "api_reference"):
        """Test filtered search by document type"""
        logger.info(f"🔍 Testing filtered search: '{query}' in {doc_type}")
        
        try:
            # Get query embedding using same model as stored embeddings
            query_embedding = self._get_query_embedding(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],  # Use pre-computed embedding
                where={"doc_type": doc_type},
                n_results=3,
                include=['documents', 'metadatas', 'distances']
            )
            
            logger.info(f"📋 Filtered Results ({doc_type}):")
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                logger.info(f"  {i+1}. {metadata['title']}")
                logger.info(f"     Score: {1-distance:.3f} | Type: {metadata['doc_type']}")
                logger.info(f"     Preview: {doc[:80]}...")
                logger.info("")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Filtered search test failed: {e}")
            raise
    
    def get_collection_stats(self, collection: chromadb.Collection) -> Dict[str, Any]:
        """Get comprehensive collection statistics"""
        
        # Basic stats
        total_count = collection.count()
        
        # Sample some metadata to analyze
        sample_results = collection.get(limit=1000, include=['metadatas'])
        sample_metadata = sample_results['metadatas']
        
        # Analyze distribution
        doc_types = {}
        chunk_types = {}
        has_code = 0
        
        for meta in sample_metadata:
            # Document types
            doc_type = meta.get('doc_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            # Chunk types
            chunk_type = meta.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            # Code examples
            if meta.get('has_code_examples', False):
                has_code += 1
        
        stats = {
            'total_documents': total_count,
            'sample_size': len(sample_metadata),
            'doc_type_distribution': doc_types,
            'chunk_type_distribution': chunk_types,
            'code_examples_percentage': (has_code / len(sample_metadata)) * 100 if sample_metadata else 0,
            'collection_metadata': collection.metadata
        }
        
        return stats

def main():
    """Main vector store setup function"""
    
    # Configuration
    embeddings_file = "data/embeddings/embeddings_nomic-embed-text.json"
    vector_store_dir = "data/vector_store"
    
    # Initialize vector store
    vector_store = ArcGISVectorStore(
        persist_directory=vector_store_dir,
        collection_name="arcgis_docs"
    )
    
    try:
        # Store embeddings
        logger.info("🚀 Starting vector store creation...")
        collection = vector_store.store_embeddings(
            embeddings_file=embeddings_file,
            batch_size=1000,
            reset_collection=True  # Fresh start
        )
        
        # Test search functionality
        vector_store.test_search(collection, "How do I create a PointBarrier?")
        vector_store.test_search(collection, "3D scene visualization")
        vector_store.test_search(collection, "widget configuration")
        
        # Test filtered searches
        vector_store.test_filtered_search(collection, "map widget", "api_reference")
        vector_store.test_filtered_search(collection, "tutorial", "guide")
        
        # Get statistics
        stats = vector_store.get_collection_stats(collection)
        
        logger.info("\n" + "="*60)
        logger.info("📊 VECTOR STORE STATISTICS")
        logger.info("="*60)
        logger.info(f"Total documents: {stats['total_documents']:,}")
        logger.info(f"Doc types: {stats['doc_type_distribution']}")
        logger.info(f"Chunk types: {stats['chunk_type_distribution']}")
        logger.info(f"Code examples: {stats['code_examples_percentage']:.1f}%")
        logger.info("="*60)
        
        logger.info("✅ Vector store creation complete!")
        logger.info(f"📁 Stored at: {vector_store_dir}")
        logger.info("🎯 Ready for Module 7: Lexical/FTS indexing")
        
    except Exception as e:
        logger.error(f"❌ Vector store creation failed: {e}")
        raise

if __name__ == "__main__":
    main()