from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class ModelType(Enum):
    FAST = "fast"
    QUALITY = "quality" 
    BUDGET = "budget"

@dataclass
class Source:
    """Represents a source document/chunk used in RAG"""
    title: str
    url: str
    content: str
    doc_type: str  # api_reference, guide, sample
    chunk_type: str
    similarity_score: float
    preview: str

@dataclass
class RAGRequest:
    """Request for RAG system"""
    question: str
    model_type: ModelType = ModelType.FAST
    max_sources: int = 10
    include_citations: bool = True
    temperature: float = 0.1

@dataclass
class RAGResponse:
    """Response from RAG system"""
    answer: str
    sources: List[Source]
    model_used: str
    processing_time: float
    token_usage: Optional[Dict[str, int]]
    confidence_score: Optional[float]
    error: Optional[str] = None

@dataclass
class ContextData:
    """Processed context for RAG"""
    formatted_content: str
    source_mapping: Dict[int, Source]
    total_tokens: int
    chunk_count: int