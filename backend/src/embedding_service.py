"""
Module 5: Embedding Service
Production-grade vector generation using Ollama (free, local)
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import requests
import time
from tqdm import tqdm
from dataclasses import dataclass
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """Single embedding result with metadata"""
    chunk_id: str
    embedding: List[float]
    model: str
    dimensions: int
    chunk_metadata: Dict[str, Any]

class OllamaEmbeddingService:
    """Production-grade embedding service using Ollama"""
    
    def __init__(self, 
                 model_name: str = "nomic-embed-text",
                 ollama_host: str = "http://localhost:11434",
                 batch_size: int = 16,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Validate Ollama connection
        self._validate_ollama_connection()
        self._ensure_model_available()
    
    def _validate_ollama_connection(self):
        """Verify Ollama server is running"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("✅ Ollama server connection successful")
        except Exception as e:
            raise ConnectionError(f"❌ Cannot connect to Ollama at {self.ollama_host}: {e}")
    
    def _ensure_model_available(self):
        """Check if embedding model is available, pull if needed"""
        try:
            # Check if model exists
            response = requests.get(f"{self.ollama_host}/api/tags")
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if self.model_name not in model_names:
                logger.info(f"🔄 Model {self.model_name} not found. Pulling...")
                self._pull_model()
            else:
                logger.info(f"✅ Model {self.model_name} is available")
                
        except Exception as e:
            logger.error(f"❌ Error checking model availability: {e}")
            raise
    
    def _pull_model(self):
        """Pull the embedding model from Ollama"""
        try:
            logger.info(f"📥 Pulling {self.model_name} model...")
            response = requests.post(
                f"{self.ollama_host}/api/pull",
                json={"name": self.model_name},
                stream=True,
                timeout=300
            )
            
            # Stream the download progress
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'status' in data:
                            print(f"\r{data['status']}", end='', flush=True)
                        if data.get('status') == 'success':
                            print(f"\n✅ Successfully pulled {self.model_name}")
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Failed to pull model {self.model_name}: {e}")
            raise
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text with retries"""
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                return result['embedding']
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠️  Embedding attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to get embedding after {self.max_retries} attempts: {e}")
                    raise
    
    def embed_chunks(self, chunks_file: str, output_dir: str = "data/embeddings") -> str:
        """
        Process all chunks and generate embeddings
        
        Args:
            chunks_file: Path to chunks JSON file
            output_dir: Directory to save embeddings
            
        Returns:
            Path to embeddings file
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load chunks
        logger.info(f"📂 Loading chunks from {chunks_file}")
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        logger.info(f"📊 Found {len(chunks)} chunks to process")
        
        # Process chunks in batches
        embedding_results = []
        failed_chunks = []
        
        # Progress tracking
        total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
        
        with tqdm(total=len(chunks), desc="🔄 Generating embeddings") as pbar:
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i:i + self.batch_size]
                batch_results = []
                
                for chunk in batch:
                    try:
                        # Extract text content for embedding
                        text_content = chunk.get('content', '')
                        
                        # Skip empty chunks
                        if not text_content.strip():
                            logger.warning(f"⚠️  Skipping empty chunk: {chunk.get('id', 'unknown')}")
                            failed_chunks.append(chunk['id'])
                            pbar.update(1)
                            continue
                        
                        # Get embedding
                        embedding = self._get_embedding(text_content)
                        
                        # Create result
                        result = EmbeddingResult(
                            chunk_id=chunk['id'],
                            embedding=embedding,
                            model=self.model_name,
                            dimensions=len(embedding),
                            chunk_metadata={
                                'doc_type': chunk.get('doc_type'),
                                'chunk_type': chunk.get('chunk_type'),
                                'token_count': chunk.get('token_count'),
                                'parent_doc_id': chunk.get('parent_doc_id'),
                                'metadata': chunk.get('metadata', {})
                            }
                        )
                        
                        batch_results.append(result)
                        pbar.update(1)
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to process chunk {chunk.get('id', 'unknown')}: {e}")
                        failed_chunks.append(chunk.get('id', 'unknown'))
                        pbar.update(1)
                        continue
                
                embedding_results.extend(batch_results)
                
                # Small delay between batches to avoid overwhelming Ollama
                if i + self.batch_size < len(chunks):
                    time.sleep(0.1)
        
        # Save results
        output_file = output_path / f"embeddings_{self.model_name.replace(':', '_')}.json"
        
        # Convert to serializable format
        embeddings_data = {
            'metadata': {
                'model': self.model_name,
                'total_chunks': len(chunks),
                'successful_embeddings': len(embedding_results),
                'failed_chunks': len(failed_chunks),
                'dimensions': embedding_results[0].dimensions if embedding_results else 0,
                'timestamp': time.time()
            },
            'embeddings': [
                {
                    'chunk_id': result.chunk_id,
                    'embedding': result.embedding,
                    'chunk_metadata': result.chunk_metadata
                }
                for result in embedding_results
            ],
            'failed_chunk_ids': failed_chunks
        }
        
        # Save embeddings
        logger.info(f"💾 Saving embeddings to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings_data, f, indent=2)
        
        # Also save as NumPy arrays for fast loading
        embeddings_array = np.array([result.embedding for result in embedding_results])
        chunk_ids = [result.chunk_id for result in embedding_results]
        
        np_file = output_path / f"embeddings_{self.model_name.replace(':', '_')}.npz"
        np.savez_compressed(
            np_file,
            embeddings=embeddings_array,
            chunk_ids=chunk_ids,
            metadata=embeddings_data['metadata']
        )
        
        # Print summary
        self._print_summary(embeddings_data, output_file, np_file)
        
        return str(output_file)
    
    def _print_summary(self, embeddings_data: Dict, json_file: Path, np_file: Path):
        """Print processing summary"""
        metadata = embeddings_data['metadata']
        
        logger.info("\n" + "="*50)
        logger.info("🎉 EMBEDDING GENERATION COMPLETE!")
        logger.info("="*50)
        logger.info(f"Model: {metadata['model']}")
        logger.info(f"Dimensions: {metadata['dimensions']}")
        logger.info(f"Total chunks: {metadata['total_chunks']:,}")
        logger.info(f"Successful embeddings: {metadata['successful_embeddings']:,}")
        logger.info(f"Failed chunks: {metadata['failed_chunks']:,}")
        logger.info(f"Success rate: {(metadata['successful_embeddings']/metadata['total_chunks']*100):.1f}%")
        logger.info(f"JSON output: {json_file}")
        logger.info(f"NumPy output: {np_file}")
        
        if metadata['failed_chunks'] > 0:
            logger.warning(f"⚠️  {metadata['failed_chunks']} chunks failed processing")

def main():
    """Main embedding processing function"""
    
    # Configuration
    chunks_file = "data/processed/all_chunks.json"
    output_dir = "data/embeddings"
    
    # Initialize service
    embedding_service = OllamaEmbeddingService(
        model_name="nomic-embed-text",
        batch_size=16,  # Adjust based on your hardware
        max_retries=3
    )
    
    # Process embeddings
    try:
        output_file = embedding_service.embed_chunks(chunks_file, output_dir)
        logger.info(f"✅ Embeddings saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        raise

if __name__ == "__main__":
    main()