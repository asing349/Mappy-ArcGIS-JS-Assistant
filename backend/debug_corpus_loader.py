"""
Debug version of corpus loader to diagnose issues
"""

import sys
import os
from pathlib import Path

print("=== DEBUG CORPUS LOADER ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Check if we can import our modules
try:
    print("\n1. Testing imports...")
    from src.config import config
    print("✓ Config imported successfully")
    
    from src.simple_corpus_loader import SimpleCorpusLoader as CorpusLoader
    print("✓ SimpleCorpusLoader imported successfully")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Check paths
print(f"\n2. Checking paths...")
print(f"Project root: {config.PROJECT_ROOT}")
print(f"Data dir: {config.DATA_DIR}")
print(f"Raw data dir: {config.RAW_DATA_DIR}")
print(f"Raw data dir exists: {config.RAW_DATA_DIR.exists()}")

# Check for JSON files
print(f"\n3. Looking for JSON files...")
if config.RAW_DATA_DIR.exists():
    json_files = list(config.RAW_DATA_DIR.glob("*.json"))
    print(f"JSON files found: {len(json_files)}")
    for file in json_files:
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  - {file.name}: {size_mb:.1f} MB")
    
    if not json_files:
        print("✗ No JSON files found in data/raw/")
        print("Please copy your JSON files to data/raw/ directory")
        sys.exit(1)
        
else:
    print("✗ Raw data directory doesn't exist")
    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {config.RAW_DATA_DIR}")

# Test loader creation
print(f"\n4. Testing loader...")
try:
    loader = CorpusLoader()
    print("✓ Loader created successfully")
except Exception as e:
    print(f"✗ Loader creation error: {e}")
    sys.exit(1)

# Test loading
print(f"\n5. Testing corpus loading...")
try:
    documents = loader.load_corpus()
    if documents:
        print(f"✓ Successfully loaded {len(documents)} documents")
        
        # Show sample document structure
        sample = documents[0]
        print(f"\nSample document structure:")
        print(f"  ID: {sample.get('id', 'N/A')}")
        print(f"  Type: {sample.get('type', 'N/A')}")
        print(f"  Title: {sample.get('title', 'N/A')[:50]}...")
        print(f"  Content length: {len(sample.get('content', ''))} chars")
        print(f"  URL: {sample.get('url', 'N/A')}")
        
    else:
        print("✗ No documents loaded")
        print("Check the error messages above")
except Exception as e:
    print(f"✗ Loading error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== DEBUG COMPLETE ===")