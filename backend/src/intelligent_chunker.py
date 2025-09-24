import json
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Chunk:
    """Represents a single chunk of content"""
    id: str
    content: str
    doc_type: str  # api_reference, sample, guide
    chunk_type: str  # class_overview, method, property, example, tutorial_step
    metadata: Dict[str, Any]
    parent_doc_id: str
    token_count: int

class DocumentChunker:
    """Main chunker that routes to document-type specific strategies"""
    
    def __init__(self, target_chunk_size: int = 600, overlap_ratio: float = 0.15):
        self.target_chunk_size = target_chunk_size
        self.overlap_ratio = overlap_ratio
        self.chunk_counter = 0
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def generate_chunk_id(self) -> str:
        """Generate unique chunk ID"""
        self.chunk_counter += 1
        return f"chunk_{self.chunk_counter:06d}"
    
    def chunk_document(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Route document to appropriate chunking strategy"""
        # Handle invalid document formats
        if not isinstance(doc, dict):
            print(f"⚠️  Skipping invalid document (not a dict): {type(doc)}")
            return []
        
        # Ensure required fields exist
        if not doc.get('title') and not doc.get('content'):
            print(f"⚠️  Skipping document missing title/content: {doc}")
            return []
        
        # Use 'doc_type' field instead of 'type' to match your data structure
        doc_type = doc.get('doc_type', 'unknown')
        
        # Map your actual doc_type values to chunking strategies
        if doc_type == 'api_reference':
            return self.chunk_api_reference(doc)
        elif doc_type == 'sample':
            return self.chunk_sample(doc)
        elif doc_type == 'guide':
            return self.chunk_guide(doc)
        else:
            # For unknown types, infer from filename or URL
            return self.chunk_by_inference(doc)
    
    def chunk_api_reference(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Chunk API reference documents by structural elements"""
        chunks = []
        content = doc.get('content', '')
        title = doc.get('title', '')
        url = doc.get('url', '')
        code_examples = doc.get('code_examples', [])
        
        # 1. Create main API reference chunk with description
        # For API docs, keep the main content as one chunk since it's usually well-structured
        main_content = f"{title}\n\n{content}"
        
        # Add first few code examples to main content if they exist
        if code_examples:
            main_content += "\n\nCode Examples:\n"
            for i, example in enumerate(code_examples[:2]):  # Limit to first 2 examples
                main_content += f"\nExample {i+1}:\n{example}\n"
        
        # Add source URL
        main_content += f"\n\nSource: {url}"
        
        chunks.append(Chunk(
            id=self.generate_chunk_id(),
            content=main_content,
            doc_type='api_reference',
            chunk_type='class_overview',
            metadata={
                'title': title,
                'url': url,
                'class_name': title,
                'example_count': len(code_examples)
            },
            parent_doc_id=url,
            token_count=self.estimate_tokens(main_content)
        ))
        
        # 2. Create separate chunks for additional code examples if content is large
        if len(code_examples) > 2:
            for i, example in enumerate(code_examples[2:], start=3):
                example_content = f"{title} - Code Example {i}\n\n{example}\n\nSource: {url}"
                chunks.append(Chunk(
                    id=self.generate_chunk_id(),
                    content=example_content,
                    doc_type='api_reference',
                    chunk_type='code_example',
                    metadata={
                        'title': title,
                        'url': url,
                        'class_name': title,
                        'example_index': i
                    },
                    parent_doc_id=url,
                    token_count=self.estimate_tokens(example_content)
                ))
        
        return chunks
    
    def chunk_sample(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Chunk sample documents - keep description with code together"""
        chunks = []
        content = doc.get('content', '')
        title = doc.get('title', '')
        url = doc.get('url', '')
        code_examples = doc.get('code_examples', [])
        
        # For samples, create one main chunk with description
        main_content = f"{title}\n\n{content}"
        
        # Add code examples to the main content if they exist
        if code_examples:
            main_content += "\n\nCode Examples:\n"
            for i, example in enumerate(code_examples[:3]):  # Limit to first 3 examples
                main_content += f"\nExample {i+1}:\n{example}\n"
        
        # Add source URL
        main_content += f"\n\nSource: {url}"
        
        chunks.append(Chunk(
            id=self.generate_chunk_id(),
            content=main_content,
            doc_type='sample',
            chunk_type='complete_example',
            metadata={
                'title': title,
                'url': url,
                'example_count': len(code_examples)
            },
            parent_doc_id=url,
            token_count=self.estimate_tokens(main_content)
        ))
        
        # If content is too large, split code examples into separate chunks
        if self.estimate_tokens(main_content) > self.target_chunk_size * 1.5:
            # Create separate chunks for additional code examples
            for i, example in enumerate(code_examples[3:], start=4):
                example_content = f"{title} - Additional Example {i}\n\n{example}\n\nSource: {url}"
                chunks.append(Chunk(
                    id=self.generate_chunk_id(),
                    content=example_content,
                    doc_type='sample',
                    chunk_type='additional_example',
                    metadata={
                        'title': title,
                        'url': url,
                        'example_index': i
                    },
                    parent_doc_id=url,
                    token_count=self.estimate_tokens(example_content)
                ))
        
        return chunks
    
    def chunk_guide(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Chunk guide documents by sections/steps"""
        chunks = []
        content = doc.get('content', '')
        title = doc.get('title', '')
        url = doc.get('url', '')
        
        # Split by common guide patterns
        sections = self.split_guide_sections(content)
        
        for i, section in enumerate(sections):
            if section.strip():
                section_content = f"{title} - Section {i+1}\n\n{section}\n\nSource: {url}"
                chunks.append(Chunk(
                    id=self.generate_chunk_id(),
                    content=section_content,
                    doc_type='guide',
                    chunk_type='tutorial_step',
                    metadata={
                        'title': title,
                        'url': url,
                        'section_index': i,
                        'total_sections': len(sections)
                    },
                    parent_doc_id=url,
                    token_count=self.estimate_tokens(section_content)
                ))
        
        return chunks
    
    def chunk_by_inference(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Infer document type from URL and content when doc_type is missing"""
        url = doc.get('url', '')
        title = doc.get('title', '')
        
        # Infer type from URL patterns
        if '/api-reference/' in url:
            return self.chunk_api_reference(doc)
        elif '/sample-code/' in url:
            return self.chunk_sample(doc)
        elif '/tutorials/' in url or '/get-started/' in url:
            return self.chunk_guide(doc)
        else:
            # Fallback to generic chunking
            return self.chunk_generic(doc)
    
    def extract_class_overview(self, content: str, title: str) -> str:
        """Extract class/object description from API reference"""
        lines = content.split('\n')
        overview_lines = []
        
        # Take title and first few meaningful lines
        overview_lines.append(title)
        
        collecting = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Start collecting after import statements
            if 'import' in line or 'CDN:' in line:
                collecting = True
                continue
            
            if collecting:
                # Stop at first major section
                if line.startswith('Constructor') or line.startswith('Property Overview'):
                    break
                overview_lines.append(line)
                
                # Limit overview size
                if len(overview_lines) > 10:
                    break
        
        return '\n'.join(overview_lines)
    
    def extract_api_sections(self, content: str) -> List[Dict[str, str]]:
        """Extract properties and methods from API reference"""
        sections = []
        
        # Simple pattern matching for now
        # This can be enhanced with more sophisticated parsing
        property_pattern = r'Property\s+([A-Za-z]+)\s*\n(.*?)(?=Property|Method|$)'
        method_pattern = r'Method\s+([A-Za-z]+)\s*\n(.*?)(?=Property|Method|$)'
        
        # Find properties
        for match in re.finditer(property_pattern, content, re.DOTALL):
            sections.append({
                'name': match.group(1),
                'type': 'property',
                'content': match.group(2).strip()
            })
        
        # Find methods
        for match in re.finditer(method_pattern, content, re.DOTALL):
            sections.append({
                'name': match.group(1),
                'type': 'method',
                'content': match.group(2).strip()
            })
        
    def chunk_generic(self, doc: Dict[str, Any]) -> List[Chunk]:
        """Fallback chunking for unknown document types"""
        content = doc.get('content', '')
        title = doc.get('title', '')
        url = doc.get('url', '')
        
        # Simple paragraph-based splitting
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            test_chunk = current_chunk + "\n\n" + para if current_chunk else para
            if self.estimate_tokens(test_chunk) <= self.target_chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return [Chunk(
            id=self.generate_chunk_id(),
            content=f"{title}\n\n{chunk}\n\nSource: {url}",
            doc_type='generic',
            chunk_type='text_section',
            metadata={'title': title, 'url': url},
            parent_doc_id=url,
            token_count=self.estimate_tokens(f"{title}\n\n{chunk}\n\nSource: {url}")
        ) for chunk in chunks]
    
    def split_guide_sections(self, content: str) -> List[str]:
        """Split guide content by sections"""
        # Split by common patterns in tutorials
        patterns = [
            r'\n(?=##\s)',  # H2 headers
            r'\n(?=###\s)', # H3 headers
            r'\n(?=Step\s\d+)', # Step numbers
            r'\n(?=Prerequisites)', # Prerequisites
            r'\n(?=What\'s Next)', # Next steps
        ]
        
        sections = [content]
        for pattern in patterns:
            new_sections = []
            for section in sections:
                new_sections.extend(re.split(pattern, section))
            sections = new_sections
        
        return [s.strip() for s in sections if s.strip()]

def process_corpus(input_dir: str = "data/raw", output_dir: str = "data/processed"):
    """Process entire corpus and save chunked results"""
    chunker = DocumentChunker()
    all_chunks = []
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files in input directory
    input_path = Path(input_dir)
    json_files = list(input_path.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return
    
    # Filter out the problematic scrape_summary file and any other non-document files
    valid_files = []
    for file_path in json_files:
        # Skip files that are likely summaries or metadata
        if 'summary' in file_path.name.lower() or file_path.stat().st_size < 1024:  # Less than 1KB
            print(f"  ⚠️  Skipping {file_path.name} (appears to be summary/metadata)")
            continue
        valid_files.append(file_path)
    
    if not valid_files:
        print(f"No valid document files found in {input_dir}")
        return
    
    print(f"\nProcessing {len(valid_files)} valid document files:")
    for file_path in valid_files:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"  📁 {file_path.name}: {size_mb:.1f} MB")
    
    for file_path in valid_files:
        print(f"\nProcessing {file_path.name}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        file_chunks = []
        for doc in documents:
            chunks = chunker.chunk_document(doc)
            file_chunks.extend(chunks)
            all_chunks.extend(chunks)
            
        print(f"  ✅ Generated {len(file_chunks)} chunks")
        
        # Save individual file chunks
        file_name = file_path.stem
        individual_output = Path(output_dir) / f"{file_name}_chunks.json"
        
        chunks_dict = [
            {
                'id': chunk.id,
                'content': chunk.content,
                'doc_type': chunk.doc_type,
                'chunk_type': chunk.chunk_type,
                'metadata': chunk.metadata,
                'parent_doc_id': chunk.parent_doc_id,
                'token_count': chunk.token_count
            }
            for chunk in file_chunks
        ]
        
        with open(individual_output, 'w', encoding='utf-8') as f:
            json.dump(chunks_dict, f, indent=2, ensure_ascii=False)
        print(f"  📄 Saved to: {individual_output}")
    
    # Convert all chunks to dictionaries for JSON serialization
    all_chunks_dict = [
        {
            'id': chunk.id,
            'content': chunk.content,
            'doc_type': chunk.doc_type,
            'chunk_type': chunk.chunk_type,
            'metadata': chunk.metadata,
            'parent_doc_id': chunk.parent_doc_id,
            'token_count': chunk.token_count
        }
        for chunk in all_chunks
    ]
    
    # Save combined results
    combined_output = Path(output_dir) / "all_chunks.json"
    with open(combined_output, 'w', encoding='utf-8') as f:
        json.dump(all_chunks_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 CHUNKING COMPLETE!")
    print(f"Total chunks generated: {len(all_chunks)}")
    print(f"Individual files saved to: {output_dir}/")
    print(f"Combined chunks: {combined_output}")
    
    # Print statistics
    print_chunk_statistics(all_chunks)
    
    return str(combined_output)

def print_chunk_statistics(chunks: List[Chunk]):
    """Print statistics about generated chunks"""
    from collections import Counter
    
    print("\n=== CHUNK STATISTICS ===")
    
    # By document type
    doc_types = Counter(chunk.doc_type for chunk in chunks)
    print(f"Chunks by document type: {dict(doc_types)}")
    
    # By chunk type
    chunk_types = Counter(chunk.chunk_type for chunk in chunks)
    print(f"Chunks by chunk type: {dict(chunk_types)}")
    
    # Token distribution
    token_counts = [chunk.token_count for chunk in chunks]
    print(f"Token count - Min: {min(token_counts)}, Max: {max(token_counts)}, Avg: {sum(token_counts)/len(token_counts):.1f}")

if __name__ == "__main__":
    # Process files from your existing Mappy project structure
    input_directory = "data/raw"      # Where your JSON files are
    output_directory = "data/processed"  # Where chunks will be saved
    
    process_corpus(input_directory, output_directory)