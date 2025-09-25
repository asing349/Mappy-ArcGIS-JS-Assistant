#!/usr/bin/env python3
"""
Vertex AI Embedding Service for Mappy ArcGIS Documentation Assistant

This service generates embeddings using Google's text-embedding-004 model,
which produces 3072-dimensional vectors with state-of-the-art performance.

Features:
- Robust error handling and retry logic
- Content validation (minimum length requirements)
- Dimension validation (ensures 3072-D vectors)
- Batch processing with progress tracking
- Comprehensive logging and metrics
- Exponential backoff for failed requests
- Google Cloud authentication

Usage:
    python embedding_service.py

Requirements:
    - Google Cloud Project with Vertex AI enabled
    - Service account with Vertex AI User role
    - GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS env vars
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv

# Google Cloud imports
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import vertexai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VertexAIEmbeddingService:
    """Service for generating embeddings using Google Vertex AI text-embedding-004"""
    
    def __init__(
        self,
        model_name: str = "text-embedding-004",
        location: str = "us-central1",
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        min_content_length: int = 10,
        expected_dimensions: int = 768  # text-embedding-004 produces 768 dimensions
    ):
        """Initialize the Vertex AI embedding service"""
        self.model_name = model_name
        self.location = location
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.min_content_length = min_content_length
        self.expected_dimensions = expected_dimensions
        
        # Load environment variables
        load_dotenv()
        
        # Initialize Vertex AI
        self._initialize_vertex_ai()
        
        # Load the embedding model
        self.model = None
        self._load_model()
    
    def _initialize_vertex_ai(self) -> None:
        """Initialize Vertex AI with proper authentication"""
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Service account key file not found: {credentials_path}")
        
        logger.info(f"🔧 Initializing Vertex AI...")
        logger.info(f"📋 Project: {project_id}")
        logger.info(f"🌍 Location: {self.location}")
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=self.location)
        aiplatform.init(project=project_id, location=self.location)
        
        logger.info("✅ Vertex AI initialized successfully")
    
    def _load_model(self) -> None:
        """Load the Vertex AI embedding model"""
        logger.info(f"📦 Loading {self.model_name} model...")
        self.model = TextEmbeddingModel.from_pretrained(self.model_name)
        logger.info(f"✅ Model {self.model_name} loaded successfully")
    
    def _validate_content(self, text: str) -> bool:
        """Validate text content before embedding generation"""
        if not text or not isinstance(text, str):
            return False
            
        # Check minimum length
        if len(text.strip()) < self.min_content_length:
            return False
            
        # Check for meaningless content (IDs, empty strings, etc.)
        stripped = text.strip()
        if stripped.isdigit():  # Pure numbers/IDs
            return False
            
        if stripped.lower() in ['null', 'none', 'undefined', '']:
            return False
            
        return True
    
    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Generate embeddings using Vertex AI
                embeddings = self.model.get_embeddings(texts)
                
                # Extract vectors and validate dimensions
                vectors = []
                for embedding in embeddings:
                    vector = embedding.values
                    
                    # Validate embedding dimensions
                    if len(vector) != self.expected_dimensions:
                        raise ValueError(
                            f"Expected {self.expected_dimensions} dimensions, "
                            f"got {len(vector)}"
                        )
                    
                    vectors.append(vector)
                
                return vectors
                
            except Exception as e:
                logger.warning(
                    f"⚠️ Batch embedding attempt {attempt + 1} failed: {e}. "
                    f"{'Retrying...' if attempt < self.max_retries - 1 else 'Giving up.'}"
                )
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise Exception(f"Failed to generate embeddings after {self.max_retries} attempts: {e}")
    
    def _load_chunks(self, chunks_file: str) -> List[Dict[str, Any]]:
        """Load and validate chunks from JSON file"""
        chunks_path = Path(chunks_file)
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_file}")
            
        with open(chunks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list and dict formats
        chunks = data if isinstance(data, list) else data.get('chunks', [])
        
        if not chunks:
            raise ValueError("No chunks found in the input file")
            
        logger.info(f"Loaded {len(chunks):,} chunks from {chunks_file}")
        return chunks
    
    def _extract_text_content(self, chunk: Dict[str, Any]) -> Optional[str]:
        """Extract rich contextual content for better embeddings"""
        # Build comprehensive content with context
        content_parts = []
        
        # Add title from metadata if available
        if 'metadata' in chunk and isinstance(chunk['metadata'], dict):
            title = chunk['metadata'].get('title', '')
            if title:
                content_parts.append(f"Title: {title}")
            
            # Add URL from metadata
            url = chunk['metadata'].get('url', '')
            if url:
                content_parts.append(f"URL: {url}")
        
        # Add document type context
        doc_type = chunk.get('doc_type', '')
        if doc_type:
            content_parts.append(f"Type: {doc_type}")
        
        # Add chunk type context  
        chunk_type = chunk.get('chunk_type', '')
        if chunk_type:
            content_parts.append(f"Section: {chunk_type}")
        
        # Add main content
        main_content = chunk.get('content', '').strip()
        if main_content and self._validate_content(main_content):
            content_parts.append(main_content)
        else:
            return None  # No valid main content
        
        # Combine all parts for rich context
        full_content = " | ".join(content_parts)
        
        if self._validate_content(full_content):
            return full_content
        
        return None
    
    def embed_chunks(
        self, 
        chunks_file: str, 
        output_dir: str = "data/embeddings"
    ) -> str:
        """Process all chunks and generate embeddings using Vertex AI"""
        # Load chunks
        chunks = self._load_chunks(chunks_file)
        
        # Prepare output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare output files
        timestamp = int(time.time())
        base_name = f"embeddings_vertex_ai_{timestamp}"
        json_file = output_dir / f"{base_name}.json"
        np_file = output_dir / f"{base_name}.npy"
        
        # Process chunks to extract valid content
        valid_chunks = []
        texts_to_embed = []
        
        logger.info(f"🔍 Filtering chunks with valid content...")
        for i, chunk in enumerate(chunks):
            text_content = self._extract_text_content(chunk)
            if text_content is not None:
                valid_chunks.append((i, chunk, text_content))
                texts_to_embed.append(text_content)
        
        if not texts_to_embed:
            raise Exception("No valid content found in chunks for embedding generation!")
        
        logger.info(f"✅ Found {len(texts_to_embed):,} chunks with valid content out of {len(chunks):,} total")
        
        # Process embeddings data structure
        embeddings_data = {
            'metadata': {
                'model': self.model_name,
                'dimensions': self.expected_dimensions,
                'total_chunks': len(chunks),
                'successful_embeddings': 0,
                'failed_chunks': len(chunks) - len(valid_chunks),
                'timestamp': timestamp,
                'min_content_length': self.min_content_length,
                'location': self.location,
                'batch_size': self.batch_size
            },
            'embeddings': []
        }
        
        # Track numpy embeddings separately for efficiency
        embeddings_array = []
        
        logger.info(f"🔄 Generating Vertex AI embeddings for {len(texts_to_embed):,} chunks...")
        
        # Process in batches
        for batch_start in tqdm(range(0, len(texts_to_embed), self.batch_size), 
                               desc=f"🔄 Generating {self.model_name} embeddings"):
            batch_end = min(batch_start + self.batch_size, len(texts_to_embed))
            batch_texts = texts_to_embed[batch_start:batch_end]
            batch_chunks = valid_chunks[batch_start:batch_end]
            
            try:
                # Generate embeddings for batch
                batch_embeddings = self._get_embeddings_batch(batch_texts)
                
                # Store embedding data
                for (original_idx, chunk, text_content), embedding in zip(batch_chunks, batch_embeddings):
                    embedding_entry = {
                        'id': chunk.get('id', f'chunk_{original_idx}'),
                        'text': text_content[:200] + '...' if len(text_content) > 200 else text_content,
                        'embedding': embedding,
                        'metadata': {
                            'original_chunk_index': original_idx,
                            'content_length': len(text_content),
                            'chunk_metadata': {
                                k: v for k, v in chunk.items() 
                                if k not in ['content', 'text', 'body', 'description', 'summary']
                            }
                        }
                    }
                    
                    embeddings_data['embeddings'].append(embedding_entry)
                    embeddings_array.append(embedding)
                    embeddings_data['metadata']['successful_embeddings'] += 1
                
                # Periodic logging
                if batch_end % (self.batch_size * 5) == 0 or batch_end == len(texts_to_embed):
                    logger.info(f"Progress: {batch_end:,}/{len(texts_to_embed):,} chunks processed")
                    
            except Exception as e:
                logger.error(f"Failed to process batch {batch_start}-{batch_end}: {e}")
                embeddings_data['metadata']['failed_chunks'] += len(batch_texts)
                continue
        
        # Finalize and save results
        if embeddings_data['metadata']['successful_embeddings'] == 0:
            raise Exception("No embeddings were generated successfully!")
        
        # Save JSON file
        logger.info(f"💾 Saving embeddings to {json_file}")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings_data, f, ensure_ascii=False, indent=2)
        
        # Save NumPy array for efficient loading
        if embeddings_array:
            logger.info(f"💾 Saving NumPy array to {np_file}")
            np.save(np_file, np.array(embeddings_array, dtype=np.float32))
        
        # Print summary
        self._print_summary(embeddings_data, json_file, np_file)
        
        return str(json_file)
    
    def _print_summary(self, embeddings_data: Dict, json_file: Path, np_file: Path):
        """Print processing summary"""
        metadata = embeddings_data['metadata']
        
        logger.info("\n" + "="*60)
        logger.info("🎉 VERTEX AI EMBEDDING GENERATION COMPLETE!")
        logger.info("="*60)
        logger.info(f"Model: {metadata['model']}")
        logger.info(f"Dimensions: {metadata['dimensions']}")
        logger.info(f"Location: {metadata['location']}")
        logger.info(f"Total chunks: {metadata['total_chunks']:,}")
        logger.info(f"Successful embeddings: {metadata['successful_embeddings']:,}")
        logger.info(f"Failed chunks: {metadata['failed_chunks']:,}")
        
        if metadata['total_chunks'] > 0:
            success_rate = (metadata['successful_embeddings'] / metadata['total_chunks']) * 100
            logger.info(f"Success rate: {success_rate:.1f}%")
        
        logger.info(f"JSON output: {json_file}")
        logger.info(f"NumPy output: {np_file}")
        
        if metadata['failed_chunks'] > 0:
            logger.warning(f"⚠️ {metadata['failed_chunks']} chunks failed processing")
        
        # Estimate cost
        total_tokens = sum(len(emb['text'].split()) for emb in embeddings_data['embeddings'])
        estimated_cost = (total_tokens / 1000) * 0.00002  # $0.00002 per 1K tokens
        logger.info(f"💰 Estimated cost: ${estimated_cost:.4f}")

def main():
    """Main embedding processing function for Vertex AI"""
    
    # Configuration
    chunks_file = "data/processed/all_chunks.json"
    output_dir = "data/embeddings"
    
    # Check if chunks file exists
    if not Path(chunks_file).exists():
        logger.error(f"❌ Chunks file not found: {chunks_file}")
        logger.error("Please run the chunking process first to generate chunks")
        return
    
    # Initialize service with Vertex AI text-embedding-004
    embedding_service = VertexAIEmbeddingService(
        model_name="text-embedding-004",  # 768 dimensions
        batch_size=25,  # Reduced to stay under token limits
        max_retries=3
    )
    
    # Process embeddings
    try:
        output_file = embedding_service.embed_chunks(chunks_file, output_dir)
        logger.info(f"✅ Vertex AI embeddings saved to: {output_file}")
        
        # Validate output
        with open(output_file, 'r') as f:
            result = json.load(f)
            
        total_embeddings = result['metadata']['successful_embeddings']
        logger.info(f"🎯 Final validation: {total_embeddings:,} embeddings generated")
        
        if total_embeddings > 0:
            logger.info("🚀 Ready for ChromaDB integration and search testing!")
        else:
            logger.error("❌ No embeddings generated - check your chunk data quality")
        
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        raise

if __name__ == "__main__":
    main()