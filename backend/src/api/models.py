"""
Pydantic models for FastAPI request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum

class ContextFocus(str, Enum):
    """Available context focus options"""
    BALANCED = "balanced"
    API = "api"
    TUTORIAL = "tutorial"
    EXAMPLES = "examples"

class QueryType(str, Enum):
    """Query types detected by the system"""
    API_REFERENCE = "api_reference"
    HOW_TO = "how_to"
    CONCEPTUAL = "conceptual"
    TROUBLESHOOTING = "troubleshooting"
    CODE_EXAMPLE = "code_example"
    COMPARISON = "comparison"
    GENERAL = "general"

class SourceInfo(BaseModel):
    """Information about a documentation source"""
    title: str = Field(..., description="Title of the documentation page")
    url: str = Field(..., description="URL to the original documentation")
    doc_type: str = Field(..., description="Type of document (api_reference, guide, sample)")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")

class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=1000,
        description="The user's question about ArcGIS JavaScript SDK",
        example="What is PointBarrier used for in routing?"
    )
    context_focus: ContextFocus = Field(
        default=ContextFocus.BALANCED,
        description="Focus for context selection"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier for rate limiting and analytics"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate and clean the query"""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str = Field(..., description="AI-generated answer with markdown formatting")
    sources: List[SourceInfo] = Field(..., description="List of documentation sources used")
    query_type: str = Field(..., description="Detected type of the query")
    context_focus: ContextFocus = Field(..., description="Context focus used")
    performance_metrics: Dict[str, float] = Field(..., description="Performance timing information")
    session_id: Optional[str] = Field(default=None, description="Session identifier if provided")
    success: bool = Field(..., description="Whether the query was processed successfully")

class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Overall system status (healthy/degraded/unhealthy)")
    components: Dict[str, Any] = Field(..., description="Status of individual components")
    timestamp: float = Field(..., description="Unix timestamp of the health check")

class ErrorResponse(BaseModel):
    """Response model for error cases"""
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: float = Field(..., description="Unix timestamp of the error")

class StatsResponse(BaseModel):
    """Response model for statistics endpoint"""
    rate_limiter_stats: Dict[str, Any] = Field(..., description="Rate limiting statistics")
    uptime: float = Field(..., description="API uptime in seconds")

# Example responses for documentation
class QueryExamples:
    """Example requests and responses for API documentation"""
    
    EXAMPLE_REQUEST = {
        "query": "How do I create a PointBarrier for routing analysis?",
        "context_focus": "tutorial",
        "session_id": "user-123"
    }
    
    EXAMPLE_RESPONSE = {
        "answer": "## How to Create A PointBarrier For Routing Analysis?\n\n**Overview:** PointBarrier objects are used in routing to specify locations that routes should avoid...",
        "sources": [
            {
                "title": "PointBarrier Class",
                "url": "https://developers.arcgis.com/javascript/latest/api-reference/esri-rest-support-PointBarrier.html",
                "doc_type": "api_reference",
                "relevance_score": 0.95
            }
        ],
        "query_type": "how_to",
        "context_focus": "tutorial",
        "performance_metrics": {
            "search_time": 0.005,
            "context_assembly_time": 0.002,
            "prompt_building_time": 0.001,
            "llm_response_time": 3.245,
            "total_time": 3.253,
            "api_processing_time": 3.255
        },
        "session_id": "user-123",
        "success": True
    }
    
    HEALTH_RESPONSE = {
        "status": "healthy",
        "components": {
            "search_engine": "working",
            "gemini_client": "working",
            "context_assembler": "initialized",
            "prompt_builder": "initialized"
        },
        "timestamp": 1695456789.123
    }
    
    ERROR_RESPONSE = {
        "error": "Query must be at least 3 characters long",
        "status_code": 400,
        "timestamp": 1695456789.123
    }