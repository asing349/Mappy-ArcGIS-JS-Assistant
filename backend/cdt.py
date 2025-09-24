import json
from pathlib import Path
from collections import Counter

def check_document_types():
    """Check what 'type' values actually exist in the documents"""
    
    data_dir = Path("data/raw")
    
    for json_file in data_dir.glob("*.json"):
        if "summary" in json_file.name.lower():
            continue
            
        print(f"\n=== {json_file.name} ===")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        if not isinstance(documents, list):
            print(f"Not a list: {type(documents)}")
            continue
            
        # Count document types
        type_counts = Counter()
        sample_docs = []
        
        for i, doc in enumerate(documents[:5]):  # Check first 5 docs
            if isinstance(doc, dict):
                doc_type = doc.get('doc_type', 'NO_DOC_TYPE')  # Check doc_type field
                type_field = doc.get('type', 'NO_TYPE')  # Also check type field
                type_counts[doc_type] += 1
                sample_docs.append({
                    'index': i,
                    'doc_type': doc_type,
                    'type': type_field,
                    'title': doc.get('title', 'NO_TITLE')[:50],
                    'url': doc.get('url', 'NO_URL')[:80],
                    'has_content': 'content' in doc,
                    'keys': list(doc.keys())
                })
            else:
                type_counts['NOT_DICT'] += 1
        
        print(f"Total documents: {len(documents)}")
        print(f"Type distribution (first 5): {dict(type_counts)}")
        
        print(f"\nSample documents:")
        for sample in sample_docs:
            print(f"  [{sample['index']}] doc_type: '{sample['doc_type']}' | type: '{sample['type']}'")
            print(f"       Title: {sample['title']}...")
            print(f"       URL: {sample['url']}")
            print(f"       Has content: {sample['has_content']}")
            print()

if __name__ == "__main__":
    check_document_types()