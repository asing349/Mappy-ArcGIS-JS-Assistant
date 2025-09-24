"""
Simple corpus loader without Pydantic - just load and go!
"""

import ujson
from pathlib import Path
from typing import List, Dict, Any
import logging
from tqdm import tqdm

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleCorpusLoader:
    """Simple loader that adapts to your actual JSON structure."""
    
    def __init__(self):
        self.stats = {
            'files_processed': 0,
            'total_documents': 0,
            'total_size_mb': 0.0,
            'api_docs': 0,
            'guide_docs': 0, 
            'sample_docs': 0,
            'errors': []
        }
    
    def load_json_file(self, file_path: Path) -> Any:
        """Load JSON file - no validation, just load it."""
        size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"Loading {file_path.name} ({size_mb:.1f} MB)")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = ujson.load(f)
            logger.info(f"✅ Loaded {file_path.name}")
            return data
        except Exception as e:
            logger.error(f"❌ Failed to load {file_path.name}: {e}")
            return None
    
    def normalize_document(self, doc: Dict[str, Any], file_name: str) -> Dict[str, Any]:
        """Convert whatever structure we get into a standard format."""
        
        # Handle different possible structures
        normalized = {}
        
        # Extract ID (try different possible field names)
        normalized['id'] = doc.get('id') or doc.get('url_path') or doc.get('url') or f"doc_{hash(str(doc))}"
        
        # Extract title
        normalized['title'] = doc.get('title', 'Untitled')
        
        # Extract content 
        normalized['content'] = doc.get('content', '')
        
        # Extract URL
        normalized['url'] = doc.get('url') or doc.get('url_path', '')
        
        # Determine document type based on file name or content
        if 'api_reference' in file_name:
            normalized['type'] = 'api_reference'
        elif 'guide' in file_name:
            normalized['type'] = 'guide'
        elif 'sample' in file_name:
            normalized['type'] = 'sample'
        else:
            # Try to guess from content or URL
            if any(word in normalized['title'].lower() for word in ['class', 'method', 'property']):
                normalized['type'] = 'api_reference'
            elif any(word in normalized['title'].lower() for word in ['tutorial', 'guide', 'getting started']):
                normalized['type'] = 'guide'
            else:
                normalized['type'] = 'sample'
        
        # Keep all original fields as metadata
        normalized['metadata'] = {k: v for k, v in doc.items() if k not in ['id', 'title', 'content', 'url']}
        
        return normalized
    
    def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a single file and return normalized documents."""
        
        # Skip the summary file
        if 'summary' in file_path.name.lower():
            logger.info(f"Skipping summary file: {file_path.name}")
            return []
        
        data = self.load_json_file(file_path)
        if not data:
            return []
        
        documents = []
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Direct list of documents
            raw_docs = data
        elif isinstance(data, dict):
            if 'documents' in data:
                # Corpus format with metadata
                raw_docs = data['documents']
            elif len(data) == 1 and isinstance(list(data.values())[0], list):
                # Single key with list of documents
                raw_docs = list(data.values())[0]
            else:
                # Single document
                raw_docs = [data]
        else:
            logger.error(f"Unknown data structure in {file_path.name}")
            return []
        
        # Process each document
        logger.info(f"Processing {len(raw_docs)} documents from {file_path.name}")
        
        for i, doc in enumerate(tqdm(raw_docs, desc=f"Processing {file_path.name}")):
            try:
                if not doc or not isinstance(doc, dict):
                    continue
                
                # Skip metadata-only documents (like summary info)
                if not doc.get('content') and not doc.get('title'):
                    continue
                
                normalized = self.normalize_document(doc, file_path.name)
                
                # Basic quality checks
                if len(normalized['content']) < 10:
                    continue
                
                documents.append(normalized)
                
                # Update stats
                doc_type = normalized['type']
                if doc_type == 'api_reference':
                    self.stats['api_docs'] += 1
                elif doc_type == 'guide':
                    self.stats['guide_docs'] += 1
                elif doc_type == 'sample':
                    self.stats['sample_docs'] += 1
                
            except Exception as e:
                self.stats['errors'].append(f"Error processing doc {i} in {file_path.name}: {e}")
                continue
        
        logger.info(f"✅ Processed {len(documents)} valid documents from {file_path.name}")
        return documents
    
    def load_corpus(self) -> List[Dict[str, Any]]:
        """Load the entire corpus."""
        
        logger.info(f"🚀 Starting corpus loading from {config.RAW_DATA_DIR}")
        
        # Find JSON files
        json_files = [f for f in config.RAW_DATA_DIR.glob("*.json") if 'summary' not in f.name.lower()]
        
        if not json_files:
            logger.error("❌ No JSON files found")
            return []
        
        logger.info(f"Found {len(json_files)} files to process:")
        for file_path in json_files:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            logger.info(f"  📁 {file_path.name}: {size_mb:.1f} MB")
        
        # Process all files
        all_documents = []
        
        for file_path in json_files:
            documents = self.process_file(file_path)
            all_documents.extend(documents)
            
            self.stats['files_processed'] += 1
            self.stats['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)
        
        self.stats['total_documents'] = len(all_documents)
        
        # Print summary
        self.print_summary()
        
        return all_documents
    
    def print_summary(self):
        """Print loading summary."""
        logger.info("\n" + "="*50)
        logger.info("📊 CORPUS LOADING SUMMARY")
        logger.info("="*50)
        logger.info(f"Files processed: {self.stats['files_processed']}")
        logger.info(f"Total size: {self.stats['total_size_mb']:.1f} MB")
        logger.info(f"Total documents: {self.stats['total_documents']}")
        logger.info(f"  📄 API Reference: {self.stats['api_docs']}")
        logger.info(f"  📚 Guides: {self.stats['guide_docs']}")
        logger.info(f"  🎯 Samples: {self.stats['sample_docs']}")
        
        if self.stats['errors']:
            logger.warning(f"⚠️  Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:3]:
                logger.warning(f"  - {error}")
        else:
            logger.info("✅ No errors!")
        
        logger.info("="*50)


def main():
    """Test the simple loader."""
    loader = SimpleCorpusLoader()
    documents = loader.load_corpus()
    
    if documents:
        logger.info(f"\n🎉 SUCCESS! Loaded {len(documents)} documents")
        
        # Show a sample document
        sample = documents[0]
        logger.info(f"\nSample document:")
        logger.info(f"  ID: {sample['id']}")
        logger.info(f"  Type: {sample['type']}")
        logger.info(f"  Title: {sample['title'][:60]}...")
        logger.info(f"  Content length: {len(sample['content'])} chars")
        logger.info(f"  URL: {sample['url']}")
        
        return documents
    else:
        logger.error("❌ Failed to load any documents")
        return None


if __name__ == "__main__":
    main()