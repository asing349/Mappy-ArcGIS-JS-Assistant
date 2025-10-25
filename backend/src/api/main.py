"""
Module 14: FastAPI Web Gateway for Mappy RAG System
Main application file that exposes the RAG system as a REST API
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import sys
import os
from pathlib import Path
from typing import Optional
import uvicorn

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))  # Add src/ to path

from api.models import QueryRequest, QueryResponse, HealthResponse, ErrorResponse
from api.dependencies import get_rag_engine, RateLimiter
from rag.rag_engine import MappyRAGEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mappy ArcGIS Assistant API",
    description="AI-powered documentation assistant for ArcGIS JavaScript SDK",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend integration
allowed_origins = [
    "https://mappy-js-sdk.vercel.app",
    "http://localhost:3000",
    "vscode-webview://*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter
rate_limiter = RateLimiter(requests_per_minute=30)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Mappy ArcGIS Assistant API...")
    
    # Test RAG engine initialization
    try:
        rag_engine = get_rag_engine()
        status = rag_engine.get_system_status()
        logger.info(f"RAG system status: {status}")
        
        if status.get("search_engine") != "working":
            logger.warning("Search engine not working properly")
        if status.get("gemini_client") != "working":
            logger.warning("Gemini client not working properly")
            
    except Exception as e:
        logger.error(f"Failed to initialize RAG engine: {e}")

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Mappy ArcGIS Assistant API",
        "version": "1.0.0",
        "description": "AI-powered documentation assistant for ArcGIS JavaScript SDK",
        "endpoints": {
            "query": "/query - Main chat endpoint",
            "health": "/health - System health check",
            "docs": "/docs - API documentation"
        }
    }

@app.post("/query", response_model=QueryResponse)
async def query_arcgis_docs(
    request: QueryRequest,
    rag_engine: MappyRAGEngine = Depends(get_rag_engine)
):
    """
    Main query endpoint for ArcGIS documentation questions
    
    Processes natural language questions about ArcGIS JavaScript SDK
    and returns AI-generated answers with source citations.
    """
    
    # Apply rate limiting
    client_id = request.session_id or "anonymous"
    if not rate_limiter.allow_request(client_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before making another request."
        )
    
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: '{request.query}' (session: {request.session_id})")
        
        # Validate query length
        if len(request.query.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 3 characters long"
            )
        
        if len(request.query) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Query too long. Maximum 1000 characters allowed."
            )
        
        # Process query through RAG system
        rag_response = rag_engine.query(
            user_query=request.query,
            context_focus=request.context_focus
        )
        
        if not rag_response.success:
            logger.error(f"RAG query failed: {rag_response.error_message}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process query: {rag_response.error_message}"
            )
        
        # Build API response
        api_response = QueryResponse(
            answer=rag_response.answer,
            sources=rag_response.sources,
            query_type=rag_response.query_type,
            context_focus=request.context_focus,
            performance_metrics={
                **rag_response.performance_metrics,
                "api_processing_time": time.time() - start_time
            },
            session_id=request.session_id,
            success=True
        )
        
        logger.info(f"Query completed successfully in {time.time() - start_time:.2f}s")
        return api_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again."
        )

@app.get("/health", response_model=HealthResponse)
async def health_check(rag_engine: MappyRAGEngine = Depends(get_rag_engine)):
    """
    System health check endpoint
    
    Returns the status of all system components including
    search engine, LLM client, and database connections.
    """
    
    try:
        # Get system status from RAG engine
        system_status = rag_engine.get_system_status()
        
        # Determine overall health
        all_working = all(
            status in ["working", "initialized"]
            for status in system_status.values() 
            if isinstance(status, str) and not status.startswith("failed")
        )
        
        health_response = HealthResponse(
            status="healthy" if all_working else "degraded",
            components=system_status,
            timestamp=time.time()
        )
        
        # Return appropriate HTTP status
        if all_working:
            return health_response
        else:
            return JSONResponse(
                status_code=503,
                content=health_response.dict()
            )
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content=HealthResponse(
                status="unhealthy",
                components={"error": str(e)},
                timestamp=time.time()
            ).dict()
        )

@app.get("/stats", response_model=dict)
async def get_stats():
    """Get API usage statistics"""
    return {
        "rate_limiter_stats": rate_limiter.get_stats(),
        "uptime": time.time() - startup_time if 'startup_time' in globals() else 0
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            status_code=exc.status_code,
            timestamp=time.time()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            status_code=500,
            timestamp=time.time()
        ).dict()
    )

# Store startup time for stats
startup_time = time.time()

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )