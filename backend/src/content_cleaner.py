"""
Module 2: Structure-Preserving Content Enhancement
Enhances content quality while preserving semantic structure and cross-references.
"""

import re
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import json
import html
from datetime import datetime
from urllib.parse import urlparse

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContentQuality:
    """Content quality metrics for documentation."""
    structural_completeness: float  # 0-100 (has headings, code, examples)
    technical_depth: float         # 0-100 (parameters, methods, detailed explanations)
    cross_reference_richness: float # 0-100 (links to related content)
    code_example_quality: float    # 0-100 (working code examples)
    estimated_usefulness: str      # 'high', 'medium', 'low'
    missing_elements: List[str]    # What's missing for completeness


@dataclass
class EnhancedDocument:
    """Enhanced document with preserved structure."""
    id: str
    url: str
    title: str
    doc_type: str
    content: str
    semantic_structure: Dict[str, Any]  # Preserved HTML structure info
    cross_references: List[str]         # Internal and external links
    code_examples: List[Dict[str, str]] # Code with language and context
    metadata: Dict[str, Any]
    quality: ContentQuality
    content_signature: str             # For smart duplicate detection
    enhanced_at: str


class DocumentationEnhancer:
    """Documentation-aware content enhancement."""
    
    def __init__(self):
        self.stats = {
            'documents_processed': 0,
            'structure_preserved': 0,
            'cross_references_extracted': 0,
            'code_examples_extracted': 0,
            'noise_removed': 0,
            'duplicates_merged': 0,
            'quality_enhanced': 0,
            'errors': []
        }
        self.seen_signatures: Dict[str, int] = {}
        self.url_map: Dict[str, str] = {}  # Map URLs to document IDs
        
    def extract_semantic_structure(self, content: str) -> Dict[str, Any]:
        """Extract and preserve semantic HTML structure."""
        structure = {
            'headings': [],
            'code_blocks': [],
            'parameter_tables': [],
            'lists': [],
            'emphasis': []
        }
        
        # Extract headings with hierarchy
        heading_pattern = r'<(h[1-6])[^>]*>(.*?)</\1>'
        for match in re.finditer(heading_pattern, content, re.IGNORECASE | re.DOTALL):
            level = int(match.group(1)[1])
            text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            structure['headings'].append({
                'level': level,
                'text': text,
                'position': match.start()
            })
        
        # Extract code blocks with language hints
        code_patterns = [
            (r'<pre[^>]*><code[^>]*class="[^"]*javascript[^"]*"[^>]*>(.*?)</code></pre>', 'javascript'),
            (r'<pre[^>]*><code[^>]*class="[^"]*html[^"]*"[^>]*>(.*?)</code></pre>', 'html'),
            (r'<pre[^>]*><code[^>]*class="[^"]*css[^"]*"[^>]*>(.*?)</code></pre>', 'css'),
            (r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', 'code'),
            (r'<code[^>]*>(.*?)</code>', 'inline')
        ]
        
        for pattern, lang in code_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                code_text = html.unescape(match.group(1))
                structure['code_blocks'].append({
                    'language': lang,
                    'content': code_text.strip(),
                    'position': match.start(),
                    'type': 'block' if lang != 'inline' else 'inline'
                })
        
        # Extract parameter tables
        table_pattern = r'<table[^>]*>(.*?)</table>'
        for match in re.finditer(table_pattern, content, re.IGNORECASE | re.DOTALL):
            table_content = match.group(1)
            if any(keyword in table_content.lower() for keyword in ['parameter', 'property', 'method', 'return']):
                structure['parameter_tables'].append({
                    'content': table_content,
                    'position': match.start()
                })
        
        # Extract lists (often contain API methods or features)
        list_pattern = r'<(ul|ol)[^>]*>(.*?)</\1>'
        for match in re.finditer(list_pattern, content, re.IGNORECASE | re.DOTALL):
            list_content = match.group(2)
            items = re.findall(r'<li[^>]*>(.*?)</li>', list_content, re.IGNORECASE | re.DOTALL)
            if items:
                structure['lists'].append({
                    'type': match.group(1).lower(),
                    'items': [re.sub(r'<[^>]+>', '', item).strip() for item in items],
                    'position': match.start()
                })
        
        return structure
    
    def extract_cross_references(self, content: str, base_url: str) -> List[str]:
        """Extract and categorize cross-references."""
        references = []
        
        # Extract all links
        link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        for match in re.finditer(link_pattern, content, re.IGNORECASE | re.DOTALL):
            url = match.group(1)
            link_text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            
            # Categorize the link
            parsed_url = urlparse(url)
            if parsed_url.netloc == '':
                # Relative URL - internal documentation
                full_url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
                references.append(full_url)
            elif 'developers.arcgis.com' in parsed_url.netloc:
                # Internal ArcGIS documentation
                references.append(url)
            elif parsed_url.scheme in ['http', 'https']:
                # External reference
                references.append(url)
        
        return list(set(references))  # Remove duplicates
    
    def extract_enhanced_code_examples(self, structure: Dict[str, Any], content: str) -> List[Dict[str, str]]:
        """Extract code examples with enhanced context."""
        enhanced_examples = []
        
        for code_block in structure['code_blocks']:
            if code_block['type'] == 'block' and len(code_block['content']) > 50:
                # Find surrounding context
                position = code_block['position']
                
                # Look for preceding heading or paragraph for context
                preceding_text = content[:position]
                context_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>[^<]*$', preceding_text, re.IGNORECASE | re.DOTALL)
                context = ""
                if context_match:
                    context = re.sub(r'<[^>]+>', '', context_match.group(1)).strip()
                
                # Determine if this is a complete example
                code_content = code_block['content']
                is_complete = any(keyword in code_content for keyword in [
                    'import', 'const', 'let', 'var', 'function', 'class', 'new ', '= '
                ])
                
                enhanced_examples.append({
                    'language': code_block['language'],
                    'content': code_content,
                    'context': context,
                    'is_complete': is_complete,
                    'length': len(code_content)
                })
        
        return enhanced_examples
    
    def remove_navigation_noise(self, content: str) -> str:
        """Remove navigation and non-content elements while preserving documentation structure."""
        
        # Remove navigation menus (but keep breadcrumbs for context)
        nav_patterns = [
            r'<nav[^>]*>.*?</nav>',
            r'<header[^>]*>.*?</header>',
            r'<footer[^>]*>.*?</footer>',
            r'<aside[^>]*>.*?</aside>',
        ]
        
        for pattern in nav_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove common non-content divs
        noise_patterns = [
            r'<div[^>]*class="[^"]*(?:nav|menu|sidebar|footer|header|advertisement)[^"]*"[^>]*>.*?</div>',
            r'<div[^>]*id="[^"]*(?:nav|menu|sidebar|footer|header|ad)[^"]*"[^>]*>.*?</div>',
        ]
        
        for pattern in noise_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove script and style tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        return content
    
    def assess_documentation_quality(self, doc: Dict[str, Any], structure: Dict[str, Any], 
                                   cross_refs: List[str], code_examples: List[Dict]) -> ContentQuality:
        """Assess quality specific to technical documentation."""
        
        doc_type = doc.get('type', '')
        content = doc.get('content', '')
        missing_elements = []
        
        # Structural completeness assessment
        structure_score = 0
        structure_factors = 0
        
        # Check for headings (organization)
        if structure['headings']:
            structure_score += 25
            if len(structure['headings']) >= 3:  # Well-organized
                structure_score += 10
        else:
            missing_elements.append("No clear section headings")
        structure_factors += 35
        
        # Check for code examples
        if code_examples:
            structure_score += 25
            complete_examples = [ex for ex in code_examples if ex['is_complete']]
            if complete_examples:
                structure_score += 15  # Bonus for complete examples
        else:
            if doc_type in ['api_reference', 'sample']:
                missing_elements.append("No code examples")
        structure_factors += 40
        
        # Check for parameter/method documentation
        if structure['parameter_tables'] or 'parameter' in content.lower():
            structure_score += 15
        elif doc_type == 'api_reference':
            missing_elements.append("No parameter documentation")
        structure_factors += 15
        
        # Check for lists (features, methods, etc.)
        if structure['lists']:
            structure_score += 10
        structure_factors += 10
        
        structural_completeness = (structure_score / structure_factors) * 100
        
        # Technical depth assessment
        depth_indicators = [
            ('parameter', 15), ('return', 10), ('example', 15), ('method', 10),
            ('property', 10), ('class', 10), ('function', 10), ('object', 5),
            ('import', 10), ('const', 5), ('let', 5), ('var', 5)
        ]
        
        depth_score = 0
        for indicator, points in depth_indicators:
            if indicator in content.lower():
                depth_score += points
        
        technical_depth = min(100, depth_score)
        
        # Cross-reference richness
        ref_score = 0
        if cross_refs:
            ref_score = min(100, len(cross_refs) * 10)  # Up to 10 refs = 100%
            if len(cross_refs) >= 5:
                ref_score += 20  # Bonus for rich linking
        
        cross_reference_richness = min(100, ref_score)
        
        # Code example quality
        code_quality = 0
        if code_examples:
            total_code_length = sum(ex['length'] for ex in code_examples)
            complete_examples = [ex for ex in code_examples if ex['is_complete']]
            
            code_quality += min(50, len(code_examples) * 10)  # Quantity
            code_quality += min(30, total_code_length / 100)   # Substantiality
            code_quality += len(complete_examples) * 10        # Completeness
        
        code_example_quality = min(100, code_quality)
        
        # Overall usefulness determination
        avg_score = (structural_completeness + technical_depth + cross_reference_richness + code_example_quality) / 4
        
        if avg_score >= 75:
            usefulness = 'high'
        elif avg_score >= 50:
            usefulness = 'medium'
        else:
            usefulness = 'low'
        
        return ContentQuality(
            structural_completeness=structural_completeness,
            technical_depth=technical_depth,
            cross_reference_richness=cross_reference_richness,
            code_example_quality=code_example_quality,
            estimated_usefulness=usefulness,
            missing_elements=missing_elements
        )
    
    def create_content_signature(self, content: str, title: str) -> str:
        """Create signature for smart duplicate detection."""
        # Use key phrases and structure for signature, not just content hash
        
        # Extract key technical terms
        technical_terms = re.findall(r'\b(?:class|method|property|function|parameter|return|import|const|let|var)\s+\w+', content.lower())
        
        # Extract heading text
        headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', content, re.IGNORECASE)
        heading_text = ' '.join(re.sub(r'<[^>]+>', '', h) for h in headings)
        
        # Create signature from title + key terms + structure
        signature_parts = [
            title.lower().strip(),
            ' '.join(sorted(set(technical_terms)))[:200],
            heading_text.lower()[:200]
        ]
        
        signature = ' | '.join(signature_parts)
        return hashlib.md5(signature.encode()).hexdigest()
    
    def detect_smart_duplicates(self, documents: List[Dict[str, Any]]) -> List[List[int]]:
        """Detect duplicates while preserving inheritance relationships."""
        signature_groups = defaultdict(list)
        inheritance_patterns = {}
        
        for i, doc in enumerate(documents):
            title = doc.get('title', '')
            content = doc.get('content', '')
            doc_type = doc.get('type', '')
            
            # Check for inheritance relationships (child classes referencing parent methods)
            if doc_type == 'api_reference' and ('extends' in content.lower() or 'inherits' in content.lower()):
                inheritance_patterns[i] = True
            
            signature = self.create_content_signature(content, title)
            signature_groups[signature].append(i)
        
        # Only group true duplicates, not inheritance relationships
        duplicate_groups = []
        for signature, indices in signature_groups.items():
            if len(indices) > 1:
                # Check if these are inheritance relationships
                inheritance_group = any(i in inheritance_patterns for i in indices)
                if not inheritance_group:
                    duplicate_groups.append(indices)
        
        return duplicate_groups
    
    def enhance_document(self, doc: Dict[str, Any]) -> Optional[EnhancedDocument]:
        """Enhance a single document while preserving structure."""
        try:
            original_content = doc.get('content', '')
            
            # Step 1: Remove navigation noise (preserve documentation structure)
            cleaned_content = self.remove_navigation_noise(original_content)
            if len(cleaned_content) < len(original_content) * 0.8:
                self.stats['noise_removed'] += 1
            
            # Step 2: Extract semantic structure
            structure = self.extract_semantic_structure(cleaned_content)
            if structure['headings'] or structure['code_blocks']:
                self.stats['structure_preserved'] += 1
            
            # Step 3: Extract cross-references
            base_url = doc.get('url', '')
            cross_refs = self.extract_cross_references(cleaned_content, base_url)
            if cross_refs:
                self.stats['cross_references_extracted'] += len(cross_refs)
            
            # Step 4: Extract enhanced code examples
            code_examples = self.extract_enhanced_code_examples(structure, cleaned_content)
            if code_examples:
                self.stats['code_examples_extracted'] += len(code_examples)
            
            # Step 5: Assess documentation quality
            quality = self.assess_documentation_quality(doc, structure, cross_refs, code_examples)
            
            # Step 6: Create content signature
            signature = self.create_content_signature(cleaned_content, doc.get('title', ''))
            
            self.stats['documents_processed'] += 1
            
            # Quality improvement check
            if (quality.structural_completeness > 70 and 
                quality.technical_depth > 60 and 
                code_examples):
                self.stats['quality_enhanced'] += 1
            
            return EnhancedDocument(
                id=doc.get('id', ''),
                url=doc.get('url', ''),
                title=doc.get('title', 'Untitled'),
                doc_type=doc.get('type', 'unknown'),
                content=cleaned_content,  # Preserves semantic HTML
                semantic_structure=structure,
                cross_references=cross_refs,
                code_examples=code_examples,
                metadata=doc.get('metadata', {}),
                quality=quality,
                content_signature=signature,
                enhanced_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            error_msg = f"Error enhancing document {doc.get('id', 'unknown')}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return None
    
    def process_corpus(self, documents: List[Dict[str, Any]]) -> List[EnhancedDocument]:
        """Process entire corpus with structure-preserving enhancement."""
        logger.info(f"Starting structure-preserving enhancement for {len(documents)} documents")
        
        # Step 1: Enhance all documents
        enhanced_docs = []
        for doc in documents:
            enhanced_doc = self.enhance_document(doc)
            if enhanced_doc:
                enhanced_docs.append(enhanced_doc)
                # Build URL mapping for cross-reference resolution
                self.url_map[enhanced_doc.url] = enhanced_doc.id
        
        logger.info(f"Enhanced {len(enhanced_docs)} documents")
        
        # Step 2: Detect smart duplicates (avoiding inheritance relationships)
        original_dict_docs = [
            {
                'content': doc.content,
                'type': doc.doc_type,
                'title': doc.title,
                'id': doc.id
            } for doc in enhanced_docs
        ]
        
        duplicate_groups = self.detect_smart_duplicates(original_dict_docs)
        logger.info(f"Found {len(duplicate_groups)} duplicate groups (preserving inheritance)")
        
        # Step 3: Handle duplicates intelligently
        docs_to_remove = set()
        for group in duplicate_groups:
            # For documentation, prefer the most complete version
            best_idx = max(group, key=lambda i: (
                enhanced_docs[i].quality.structural_completeness +
                enhanced_docs[i].quality.technical_depth +
                len(enhanced_docs[i].code_examples) * 10
            ))
            
            for idx in group:
                if idx != best_idx:
                    docs_to_remove.add(idx)
        
        # Filter out true duplicates
        final_docs = [doc for i, doc in enumerate(enhanced_docs) if i not in docs_to_remove]
        self.stats['duplicates_merged'] = len(docs_to_remove)
        
        logger.info(f"Merged {self.stats['duplicates_merged']} duplicates")
        logger.info(f"Final enhanced corpus: {len(final_docs)} documents")
        
        return final_docs
    
    def save_enhanced_corpus(self, enhanced_docs: List[EnhancedDocument], output_dir: str = None):
        """Save enhanced corpus preserving all structural information."""
        if output_dir is None:
            output_dir = config.PROCESSED_DATA_DIR
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        def doc_to_dict(doc):
            return {
                'id': doc.id,
                'url': doc.url,
                'title': doc.title,
                'type': doc.doc_type,
                'content': doc.content,  # Preserves semantic HTML
                'semantic_structure': doc.semantic_structure,
                'cross_references': doc.cross_references,
                'code_examples': doc.code_examples,
                'metadata': doc.metadata,
                'quality': {
                    'structural_completeness': doc.quality.structural_completeness,
                    'technical_depth': doc.quality.technical_depth,
                    'cross_reference_richness': doc.quality.cross_reference_richness,
                    'code_example_quality': doc.quality.code_example_quality,
                    'estimated_usefulness': doc.quality.estimated_usefulness,
                    'missing_elements': doc.quality.missing_elements
                },
                'content_signature': doc.content_signature,
                'enhanced_at': doc.enhanced_at
            }
        
        # Save enhanced documents
        enhanced_file = output_path / "enhanced_documents.json"
        with open(enhanced_file, 'w', encoding='utf-8') as f:
            json.dump([doc_to_dict(doc) for doc in enhanced_docs], f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(enhanced_docs)} enhanced documents to {enhanced_file}")
        
        # Save cross-reference map
        ref_map = {}
        for doc in enhanced_docs:
            if doc.cross_references:
                ref_map[doc.id] = doc.cross_references
        
        ref_file = output_path / "cross_reference_map.json"
        with open(ref_file, 'w', encoding='utf-8') as f:
            json.dump(ref_map, f, indent=2)
        
        # Save enhancement statistics
        stats_file = output_path / "enhancement_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                **self.stats,
                'processing_date': datetime.now().isoformat(),
                'documents_final': len(enhanced_docs),
                'high_quality_docs': len([d for d in enhanced_docs if d.quality.estimated_usefulness == 'high']),
                'docs_with_complete_examples': len([d for d in enhanced_docs if any(ex['is_complete'] for ex in d.code_examples)]),
                'avg_cross_references': sum(len(d.cross_references) for d in enhanced_docs) / len(enhanced_docs)
            }, f, indent=2)
        
        logger.info(f"Saved enhancement statistics to {stats_file}")
        return output_path
    
    def print_summary(self):
        """Print enhancement summary."""
        logger.info("\n" + "="*70)
        logger.info("📊 MODULE 2: STRUCTURE-PRESERVING ENHANCEMENT SUMMARY")
        logger.info("="*70)
        logger.info(f"Documents processed: {self.stats['documents_processed']}")
        logger.info(f"Structure preserved: {self.stats['structure_preserved']}")
        logger.info(f"Cross-references extracted: {self.stats['cross_references_extracted']}")
        logger.info(f"Code examples extracted: {self.stats['code_examples_extracted']}")
        logger.info(f"Noise removed: {self.stats['noise_removed']}")
        logger.info(f"Duplicates merged: {self.stats['duplicates_merged']}")
        logger.info(f"Quality enhanced: {self.stats['quality_enhanced']}")
        
        if self.stats['errors']:
            logger.warning(f"Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:3]:
                logger.warning(f"  - {error}")
        else:
            logger.info("✅ No errors!")
        
        logger.info("="*70)


def main():
    """Main function to test structure-preserving enhancement."""
    from simple_corpus_loader import SimpleCorpusLoader
    
    # Load corpus from Module 1
    loader = SimpleCorpusLoader()
    documents = loader.load_corpus()
    
    if not documents:
        logger.error("No documents loaded from Module 1")
        return
    
    # Enhance corpus while preserving structure
    enhancer = DocumentationEnhancer()
    enhanced_docs = enhancer.process_corpus(documents)
    
    # Save results
    output_path = enhancer.save_enhanced_corpus(enhanced_docs)
    
    # Print summary
    enhancer.print_summary()
    
    logger.info(f"\nModule 2 complete! Enhanced corpus saved to {output_path}")
    logger.info(f"Processed {len(enhanced_docs)} documents with preserved structure ready for Module 3")


if __name__ == "__main__":
    main()