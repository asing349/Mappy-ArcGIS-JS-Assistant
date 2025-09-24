"""
Context Assembler - Enhanced Context Building for Mappy RAG System
Takes search results and builds intelligent context for LLM prompts
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

@dataclass
class ContextChunk:
    """Represents a chunk of context with metadata"""
    content: str
    doc_type: str
    chunk_type: str
    title: str
    url: str
    relevance_score: float
    rank: int

@dataclass
class AssembledContext:
    """Complete assembled context ready for LLM"""
    context_text: str
    total_chunks: int
    doc_types_used: List[str]
    sources: List[Dict[str, str]]
    context_stats: Dict[str, Any]
    truncated: bool = False

class ContextAssembler:
    """Assembles search results into optimized context for LLM consumption"""
    
    def __init__(self, 
                 max_context_length: int = 8000,
                 max_chunks: int = 10,
                 prefer_diversity: bool = True):
        """
        Initialize context assembler
        
        Args:
            max_context_length: Maximum characters in assembled context
            max_chunks: Maximum number of chunks to include
            prefer_diversity: Whether to prefer diverse document types
        """
        self.max_context_length = max_context_length
        self.max_chunks = max_chunks
        self.prefer_diversity = prefer_diversity
        
        # Document type priorities (higher = more important)
        self.doc_type_priority = {
            "api_reference": 3,
            "guide": 2,
            "sample": 1
        }
        
        # Chunk type priorities within document types
        self.chunk_type_priority = {
            "class_overview": 5,
            "method_detail": 4,
            "property_detail": 4,
            "code_example": 3,
            "tutorial_step": 4,
            "concept_explanation": 3,
            "complete_example": 2,
            "additional_example": 1
        }
    
    def assemble_context(self, 
                        search_results: Dict[str, Any], 
                        query: str,
                        context_focus: str = "balanced") -> AssembledContext:
        """
        Assemble search results into optimized context
        
        Args:
            search_results: Results from search engine
            query: Original user query
            context_focus: "api", "tutorial", "examples", or "balanced"
            
        Returns:
            AssembledContext ready for LLM consumption
        """
        if not search_results.get('results'):
            return AssembledContext(
                context_text="No relevant documentation found.",
                total_chunks=0,
                doc_types_used=[],
                sources=[],
                context_stats={"empty": True}
            )
        
        # Convert search results to ContextChunks
        chunks = self._convert_to_chunks(search_results['results'])
        
        # Apply context focus filtering and prioritization
        chunks = self._apply_context_focus(chunks, context_focus, query)
        
        # Select optimal chunks for context
        selected_chunks = self._select_optimal_chunks(chunks)
        
        # Assemble final context
        return self._build_final_context(selected_chunks, query)
    
    def _convert_to_chunks(self, results: List[Dict[str, Any]]) -> List[ContextChunk]:
        """Convert search results to ContextChunk objects"""
        chunks = []
        
        for result in results:
            chunks.append(ContextChunk(
                content=result['content'],
                doc_type=result.get('doc_type', 'unknown'),
                chunk_type=result.get('chunk_type', 'unknown'),
                title=result.get('title', 'No title'),
                url=result.get('url', ''),
                relevance_score=result.get('similarity_score', 0.0),
                rank=result.get('rank', 999)
            ))
        
        return chunks
    
    def _apply_context_focus(self, 
                           chunks: List[ContextChunk], 
                           focus: str, 
                           query: str) -> List[ContextChunk]:
        """Apply context focus to prioritize certain types of content"""
        
        # Adjust priorities based on focus
        if focus == "api":
            # Prioritize API reference content
            for chunk in chunks:
                if chunk.doc_type == "api_reference":
                    chunk.relevance_score *= 1.5
                elif chunk.chunk_type == "code_example":
                    chunk.relevance_score *= 1.2
        
        elif focus == "tutorial":
            # Prioritize guide content and tutorial steps
            for chunk in chunks:
                if chunk.doc_type == "guide":
                    chunk.relevance_score *= 1.5
                elif chunk.chunk_type in ["tutorial_step", "concept_explanation"]:
                    chunk.relevance_score *= 1.3
        
        elif focus == "examples":
            # Prioritize code examples and samples
            for chunk in chunks:
                if chunk.doc_type == "sample":
                    chunk.relevance_score *= 1.5
                elif chunk.chunk_type in ["code_example", "complete_example"]:
                    chunk.relevance_score *= 1.4
        
        # Query-specific boosts
        query_lower = query.lower()
        for chunk in chunks:
            # Boost chunks that match query terms in title
            if any(term in chunk.title.lower() for term in query_lower.split()):
                chunk.relevance_score *= 1.2
            
            # Boost chunks with code if query suggests technical implementation
            if any(term in query_lower for term in ["how to", "implement", "code", "example"]):
                if chunk.chunk_type in ["code_example", "complete_example"]:
                    chunk.relevance_score *= 1.3
        
        return chunks
    
    def _select_optimal_chunks(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """Select optimal chunks balancing relevance, diversity, and length"""
        
        if not chunks:
            return []
        
        # Sort by relevance score
        chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        
        selected = []
        current_length = 0
        doc_type_counts = defaultdict(int)
        
        for chunk in chunks:
            # Check if adding this chunk would exceed limits
            chunk_length = len(chunk.content)
            if (current_length + chunk_length > self.max_context_length or 
                len(selected) >= self.max_chunks):
                break
            
            # If preferring diversity, limit chunks per document type
            if self.prefer_diversity:
                if doc_type_counts[chunk.doc_type] >= 4:  # Max 4 chunks per doc type
                    continue
            
            selected.append(chunk)
            current_length += chunk_length
            doc_type_counts[chunk.doc_type] += 1
        
        # Re-sort selected chunks for optimal presentation
        return self._optimize_chunk_order(selected)
    
    def _optimize_chunk_order(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """Optimize the order of selected chunks for LLM consumption"""
        
        # Group by document type
        api_chunks = [c for c in chunks if c.doc_type == "api_reference"]
        guide_chunks = [c for c in chunks if c.doc_type == "guide"]
        sample_chunks = [c for c in chunks if c.doc_type == "sample"]
        
        # Order: API overview first, then guides, then examples
        ordered = []
        
        # Add API overview/class definitions first
        for chunk in api_chunks:
            if chunk.chunk_type in ["class_overview", "method_detail", "property_detail"]:
                ordered.append(chunk)
        
        # Add guide content
        ordered.extend(guide_chunks)
        
        # Add remaining API chunks (mainly code examples)
        for chunk in api_chunks:
            if chunk not in ordered:
                ordered.append(chunk)
        
        # Add sample code last
        ordered.extend(sample_chunks)
        
        return ordered
    
    def _build_final_context(self, chunks: List[ContextChunk], query: str) -> AssembledContext:
        """Build the final context text from selected chunks"""
        
        if not chunks:
            return AssembledContext(
                context_text="No relevant content found.",
                total_chunks=0,
                doc_types_used=[],
                sources=[],
                context_stats={"empty": True}
            )
        
        context_parts = []
        sources = []
        doc_types_used = list(set(chunk.doc_type for chunk in chunks))
        
        # Add context header
        context_parts.append("=== ARCGIS JAVASCRIPT SDK DOCUMENTATION ===\n")
        
        # Group chunks by document type for cleaner presentation
        for doc_type in ["api_reference", "guide", "sample"]:
            type_chunks = [c for c in chunks if c.doc_type == doc_type]
            if not type_chunks:
                continue
            
            # Add section header
            section_name = {
                "api_reference": "API REFERENCE",
                "guide": "GUIDES & TUTORIALS", 
                "sample": "CODE EXAMPLES"
            }[doc_type]
            
            context_parts.append(f"\n--- {section_name} ---\n")
            
            # Add chunks
            for i, chunk in enumerate(type_chunks, 1):
                # Format chunk with clear boundaries
                chunk_text = f"[{section_name} {i}] {chunk.title}\n"
                chunk_text += f"Source: {chunk.url}\n"
                chunk_text += f"{chunk.content}\n"
                
                context_parts.append(chunk_text)
                
                # Add to sources
                sources.append({
                    "title": chunk.title,
                    "url": chunk.url,
                    "doc_type": chunk.doc_type,
                    "relevance_score": chunk.relevance_score
                })
        
        context_text = "\n".join(context_parts)
        
        # Check if context was truncated
        truncated = len(chunks) < len(chunks) or len(context_text) >= self.max_context_length
        
        # Calculate stats
        context_stats = {
            "total_characters": len(context_text),
            "chunks_by_type": {doc_type: len([c for c in chunks if c.doc_type == doc_type]) 
                             for doc_type in doc_types_used},
            "average_relevance": sum(c.relevance_score for c in chunks) / len(chunks),
            "query_terms_found": self._count_query_terms_in_context(query, context_text)
        }
        
        return AssembledContext(
            context_text=context_text,
            total_chunks=len(chunks),
            doc_types_used=doc_types_used,
            sources=sources,
            context_stats=context_stats,
            truncated=truncated
        )
    
    def _count_query_terms_in_context(self, query: str, context: str) -> int:
        """Count how many query terms appear in the context"""
        query_terms = set(query.lower().split())
        context_lower = context.lower()
        
        return sum(1 for term in query_terms if term in context_lower)

def main():
    """Test the context assembler"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Context Assembler...")
    
    # Mock search results for testing
    mock_results = {
        "search_time": 0.1,
        "total_results": 3,
        "results": [
            {
                "content": "PointBarrier represents a point barrier used in routing analysis. It prevents travel through specific point locations.",
                "doc_type": "api_reference",
                "chunk_type": "class_overview",
                "title": "PointBarrier Class",
                "url": "https://developers.arcgis.com/javascript/latest/api-reference/esri-rest-support-PointBarrier.html",
                "similarity_score": 0.95,
                "rank": 1
            },
            {
                "content": "// Create a point barrier\nconst pointBarrier = new PointBarrier({\n  geometry: new Point({x: -117.195, y: 34.057})\n});",
                "doc_type": "api_reference", 
                "chunk_type": "code_example",
                "title": "PointBarrier Code Example",
                "url": "https://developers.arcgis.com/javascript/latest/api-reference/esri-rest-support-PointBarrier.html",
                "similarity_score": 0.87,
                "rank": 2
            },
            {
                "content": "This tutorial shows how to add routing barriers to prevent travel through certain areas.",
                "doc_type": "guide",
                "chunk_type": "tutorial_step", 
                "title": "Adding Routing Barriers",
                "url": "https://developers.arcgis.com/javascript/latest/tutorials/routing-barriers/",
                "similarity_score": 0.82,
                "rank": 3
            }
        ]
    }
    
    # Test context assembly
    assembler = ContextAssembler()
    
    print("\n1. Testing balanced context assembly...")
    context = assembler.assemble_context(mock_results, "PointBarrier routing", "balanced")
    
    print(f"   Total chunks: {context.total_chunks}")
    print(f"   Doc types: {context.doc_types_used}")
    print(f"   Context length: {len(context.context_text)} chars")
    print(f"   Truncated: {context.truncated}")
    
    print("\n2. Testing API-focused context...")
    api_context = assembler.assemble_context(mock_results, "PointBarrier API", "api")
    print(f"   API context length: {len(api_context.context_text)} chars")
    
    print("\n3. Sample context output:")
    print("=" * 60)
    print(context.context_text[:500] + "...")
    print("=" * 60)
    
    print("\n4. Context statistics:")
    for key, value in context.context_stats.items():
        print(f"   {key}: {value}")
    
    print("\nContext Assembler testing complete!")

if __name__ == "__main__":
    main()