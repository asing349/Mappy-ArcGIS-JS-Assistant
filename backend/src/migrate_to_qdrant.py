#!/usr/bin/env python3
"""
Migration script to upload existing Vertex AI embeddings to Qdrant Cloud
Migrates 33,079 vectors from local JSON to Qdrant Cloud storage
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Qdrant imports
from qdrant_client import QdrantClient, models

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantMigration:
    """Migrates Vertex AI embeddings from local JSON to Qdrant Cloud"""
    
    def __init__(self):
        # Qdrant Cloud connection
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.api_key = os.getenv("QDRANT_API_KEY")
        
        if not self.api_key:
            raise ValueError("QDRANT_API_KEY not found in backend/.env file")
        
        # File paths
        self.embeddings_file = Path("data/embeddings/embeddings_vertex_ai_1758745786.json")
        self.chunks_file = Path("data/processed/all_chunks.json")
        
        # Collection settings
        self.collection_name = "arcgis_docs"
        self.vector_size = 768  # Vertex AI text-embedding-004 dimensions
        self.batch_size = 100   # Upload in batches of 100
        
        # Initialize Qdrant client
        self.client = None
        
    def connect_to_qdrant(self):
        """Connect to Qdrant Cloud and test connection"""
        logger.info(f"Connecting to Qdrant Cloud at: {self.qdrant_url}")
        
        try:
            self.client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.api_key,
            )
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"✅ Connected successfully! Found {len(collections.collections)} existing collections")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            return False
    
    def load_embeddings(self):
        """Load embeddings from JSON file"""
        logger.info(f"Loading embeddings from: {self.embeddings_file}")
        
        if not self.embeddings_file.exists():
            raise FileNotFoundError(f"Embeddings file not found: {self.embeddings_file}")
        
        with open(self.embeddings_file, 'r') as f:
            data = json.load(f)
        
        # Handle nested structure: {"metadata": {...}, "embeddings": [...]}
        if isinstance(data, dict) and 'embeddings' in data:
            embeddings = data['embeddings']
            metadata = data.get('metadata', {})
            logger.info(f"📊 File metadata: {metadata.get('total_chunks', 'unknown')} total chunks, {metadata.get('successful_embeddings', 'unknown')} successful")
        else:
            # Fallback for flat array structure
            embeddings = data
        
        logger.info(f"✅ Loaded {len(embeddings)} embeddings from JSON")
        return embeddings
    
    def load_chunks(self):
        """Load chunk metadata for payload"""
        logger.info(f"Loading chunk metadata from: {self.chunks_file}")
        
        if not self.chunks_file.exists():
            raise FileNotFoundError(f"Chunks file not found: {self.chunks_file}")
        
        with open(self.chunks_file, 'r') as f:
            chunks = json.load(f)
        
        # Create lookup dictionary by chunk ID
        chunk_lookup = {}
        for chunk in chunks:
            chunk_lookup[chunk['id']] = chunk
        
        logger.info(f"✅ Loaded metadata for {len(chunk_lookup)} chunks")
        return chunk_lookup
    
    def create_collection(self):
        """Create Qdrant collection with proper configuration"""
        logger.info(f"Creating collection: {self.collection_name}")
        
        try:
            # Check if collection already exists
            existing_collections = self.client.get_collections()
            collection_names = [col.name for col in existing_collections.collections]
            
            if self.collection_name in collection_names:
                logger.warning(f"⚠️ Collection '{self.collection_name}' already exists!")
                response = input("Delete existing collection and recreate? (y/N): ")
                if response.lower() == 'y':
                    self.client.delete_collection(self.collection_name)
                    logger.info("🗑️ Deleted existing collection")
                else:
                    logger.info("Using existing collection")
                    return True
            
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE  # Use cosine similarity like ChromaDB
                )
            )
            
            logger.info(f"✅ Created collection '{self.collection_name}' with {self.vector_size} dimensions")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection: {e}")
            return False
    
    def prepare_points(self, embeddings_data, chunk_lookup):
        """Prepare data points for Qdrant upload"""
        logger.info("Preparing data points for upload...")
        
        points = []
        skipped = 0
        
        for item in tqdm(embeddings_data, desc="Preparing points"):
            chunk_id = item['id']
            embedding = item['embedding']
            
            # Get chunk metadata
            chunk_metadata = chunk_lookup.get(chunk_id, {})
            
            # Skip if no metadata found
            if not chunk_metadata:
                skipped += 1
                continue
            
            # Prepare payload (flatten metadata like ChromaDB version)
            payload = {
                'chunk_id': chunk_id,
                'content': chunk_metadata.get('content', ''),
                'doc_type': chunk_metadata.get('doc_type', ''),
                'chunk_type': chunk_metadata.get('chunk_type', ''),
                'parent_doc_id': chunk_metadata.get('parent_doc_id', ''),
                'token_count': chunk_metadata.get('token_count', 0),
            }
            
            # Add metadata fields
            metadata = chunk_metadata.get('metadata', {})
            if metadata:
                payload.update({
                    'metadata_title': metadata.get('title', ''),
                    'metadata_url': metadata.get('url', ''),
                    'metadata_example_count': metadata.get('example_count', 0),
                })
            
            # Create Qdrant point
            point = models.PointStruct(
                id=len(points),  # Sequential ID
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        logger.info(f"✅ Prepared {len(points)} points for upload")
        if skipped > 0:
            logger.warning(f"⚠️ Skipped {skipped} points due to missing metadata")
        
        return points
    
    def upload_points(self, points):
        """Upload points to Qdrant Cloud in batches"""
        logger.info(f"Uploading {len(points)} points in batches of {self.batch_size}...")
        
        total_batches = (len(points) + self.batch_size - 1) // self.batch_size
        successful_uploads = 0
        failed_uploads = 0
        
        for i in tqdm(range(0, len(points), self.batch_size), 
                     desc="Uploading batches", total=total_batches):
            batch = points[i:i + self.batch_size]
            
            try:
                # Upload batch
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                successful_uploads += len(batch)
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Failed to upload batch {i//self.batch_size + 1}: {e}")
                failed_uploads += len(batch)
                
                # Wait longer on error
                time.sleep(1.0)
        
        logger.info(f"✅ Upload complete!")
        logger.info(f"📊 Successful uploads: {successful_uploads}")
        logger.info(f"❌ Failed uploads: {failed_uploads}")
        logger.info(f"✅ Success rate: {successful_uploads/(successful_uploads + failed_uploads)*100:.1f}%")
        
        return successful_uploads, failed_uploads
    
    def verify_upload(self):
        """Verify the upload by checking collection info"""
        logger.info("Verifying upload...")
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            vector_count = collection_info.vectors_count
            
            logger.info(f"✅ Collection '{self.collection_name}' contains {vector_count} vectors")
            
            # Test a sample search
            sample_vector = [0.1] * self.vector_size
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=sample_vector,
                limit=3
            )
            
            logger.info(f"✅ Sample search returned {len(search_result)} results")
            logger.info("🎉 Migration verification successful!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

def main():
    """Main migration process"""
    logger.info("🚀 Starting Qdrant Cloud migration...")
    logger.info("=" * 60)
    
    # Initialize migration
    migration = QdrantMigration()
    
    # Step 1: Connect to Qdrant
    if not migration.connect_to_qdrant():
        logger.error("❌ Migration failed: Could not connect to Qdrant")
        return
    
    # Step 2: Load data
    try:
        embeddings_data = migration.load_embeddings()
        chunk_lookup = migration.load_chunks()
    except FileNotFoundError as e:
        logger.error(f"❌ Migration failed: {e}")
        return
    
    # Step 3: Create collection
    if not migration.create_collection():
        logger.error("❌ Migration failed: Could not create collection")
        return
    
    # Step 4: Prepare points
    points = migration.prepare_points(embeddings_data, chunk_lookup)
    if not points:
        logger.error("❌ Migration failed: No points to upload")
        return
    
    # Step 5: Upload points
    successful, failed = migration.upload_points(points)
    if successful == 0:
        logger.error("❌ Migration failed: No points uploaded successfully")
        return
    
    # Step 6: Verify upload
    migration.verify_upload()
    
    logger.info("=" * 60)
    logger.info("🎉 Qdrant Cloud migration completed successfully!")
    logger.info(f"📊 Final Stats:")
    logger.info(f"   • Total vectors uploaded: {successful}")
    logger.info(f"   • Collection name: {migration.collection_name}")
    logger.info(f"   • Vector dimensions: {migration.vector_size}")
    logger.info(f"   • Qdrant URL: {migration.qdrant_url}")

if __name__ == "__main__":
    main()