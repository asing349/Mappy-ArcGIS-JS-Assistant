"""
Inspect raw scraped content before any processing
"""

import json
from pathlib import Path

def inspect_raw_files():
    """Examine raw scraped content from individual files."""
    
    raw_files = [
        "data/raw/api_reference_full.json",
        "data/raw/samples_full.json", 
        "data/raw/guides_full.json"
    ]
    
    for file_path in raw_files:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue
        
        print("="*80)
        print(f"INSPECTING: {file_path.name}")
        print("="*80)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Total documents: {len(data)}")
        
        # Take a few samples - first, middle, last
        indices = [0, len(data)//2, len(data)-1] if len(data) > 2 else [0]
        
        for i, idx in enumerate(indices):
            doc = data[idx]
            
            print(f"\n--- SAMPLE {i+1} (Index {idx}) ---")
            print(f"Title: {doc.get('title', 'No title')}")
            print(f"URL: {doc.get('url', 'No URL')}")
            print(f"Type: {doc.get('doc_type', 'No type')}")
            
            content = doc.get('content', '')
            print(f"Content length: {len(content)} characters")
            
            # Show first 1000 characters
            print(f"\nContent preview:")
            print("-" * 50)
            preview = content[:1000]
            print(preview)
            if len(content) > 1000:
                print("...[truncated]")
            print("-" * 50)
            
            # Check for code patterns in raw content
            code_patterns = [
                'import ', 'const ', 'let ', 'var ', 'function ', 'class ',
                'new ', '=>', 'require(', 'export ', '.js', '.html', '.css'
            ]
            
            found_patterns = []
            for pattern in code_patterns:
                if pattern in content:
                    count = content.count(pattern)
                    found_patterns.append(f"{pattern}({count})")
            
            if found_patterns:
                print(f"Code patterns found: {', '.join(found_patterns)}")
            else:
                print("No code patterns detected")
            
            # Check for HTML structure
            html_patterns = {
                'HTML tags': ['<h1', '<h2', '<h3', '<pre', '<code', '<div', '<p>'],
                'Code blocks': ['<pre>', '<code>', '```'],
                'Links': ['<a href', 'href='],
                'Lists': ['<ul>', '<ol>', '<li>'],
                'Tables': ['<table>', '<tr>', '<td>']
            }
            
            html_found = {}
            for category, patterns in html_patterns.items():
                found = [p for p in patterns if p in content]
                if found:
                    html_found[category] = found
            
            if html_found:
                print(f"HTML structure found:")
                for category, patterns in html_found.items():
                    print(f"  {category}: {', '.join(patterns)}")
            else:
                print("No HTML structure detected")
            
            # Check for code examples section
            code_sections = []
            if 'code_examples' in doc:
                code_sections = doc['code_examples']
                print(f"Separate code_examples field: {len(code_sections)} examples")
                if code_sections:
                    print(f"First code example preview:")
                    print(code_sections[0][:200] + "..." if len(code_sections[0]) > 200 else code_sections[0])
            
            print("\n" + "="*60)

if __name__ == "__main__":
    inspect_raw_files()