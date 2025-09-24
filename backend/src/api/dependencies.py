"""
FastAPI dependencies for RAG engine management and rate limiting
"""

import time
import logging
import sys
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict, deque
from threading import Lock

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

# Global RAG engine instance
_rag_engine_instance = None
_rag_engine_lock = Lock()

def get_rag_engine():
    """
    Dependency to get or create RAG engine instance
    Implements singleton pattern for efficient resource usage
    """
    global _rag_engine_instance
    
    if _rag_engine_instance is None:
        with _rag_engine_lock:
            # Double-check locking pattern
            if _rag_engine_instance is None:
                try:
                    from rag.rag_engine import MappyRAGEngine
                    logger.info("Initializing RAG engine...")
                    _rag_engine_instance = MappyRAGEngine()
                    logger.info("RAG engine initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize RAG engine: {e}")
                    raise
    
    return _rag_engine_instance

class RateLimiter:
    """
    Simple in-memory rate limiter for API endpoints
    Tracks requests per client and enforces limits
    """
    
    def __init__(self, requests_per_minute: int = 30):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests allowed per minute per client
        """
        self.requests_per_minute = requests_per_minute
        self.request_times: Dict[str, deque] = defaultdict(lambda: deque())
        self.lock = Lock()
        
    def allow_request(self, client_id: str) -> bool:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()
        
        with self.lock:
            # Get client's request history
            client_requests = self.request_times[client_id]
            
            # Remove requests older than 1 minute
            while client_requests and current_time - client_requests[0] > 60:
                client_requests.popleft()
            
            # Check if client has exceeded rate limit
            if len(client_requests) >= self.requests_per_minute:
                return False
            
            # Record this request
            client_requests.append(current_time)
            return True
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        with self.lock:
            return {
                "total_clients": len(self.request_times),
                "requests_per_minute_limit": self.requests_per_minute,
                "active_clients": len([
                    client_id for client_id, requests in self.request_times.items()
                    if requests and time.time() - requests[-1] < 300  # Active in last 5 minutes
                ])
            }
    
    def reset_client(self, client_id: str):
        """Reset rate limit for a specific client"""
        with self.lock:
            if client_id in self.request_times:
                del self.request_times[client_id]

class RequestLogger:
    """
    Simple request logging for analytics
    Tracks query patterns and performance
    """
    
    def __init__(self):
        self.requests: deque = deque(maxlen=1000)  # Keep last 1000 requests
        self.lock = Lock()
    
    def log_request(self, 
                   query: str, 
                   query_type: str, 
                   response_time: float,
                   success: bool,
                   session_id: Optional[str] = None):
        """Log a request for analytics"""
        
        request_data = {
            "timestamp": time.time(),
            "query_length": len(query),
            "query_type": query_type,
            "response_time": response_time,
            "success": success,
            "session_id": session_id
        }
        
        with self.lock:
            self.requests.append(request_data)
    
    def get_analytics(self) -> Dict[str, any]:
        """Get request analytics"""
        with self.lock:
            if not self.requests:
                return {"total_requests": 0}
            
            requests = list(self.requests)
            
            # Calculate statistics
            total_requests = len(requests)
            successful_requests = sum(1 for r in requests if r["success"])
            average_response_time = sum(r["response_time"] for r in requests) / total_requests
            
            # Query type distribution
            query_types = defaultdict(int)
            for request in requests:
                query_types[request["query_type"]] += 1
            
            # Recent activity (last hour)
            hour_ago = time.time() - 3600
            recent_requests = [r for r in requests if r["timestamp"] > hour_ago]
            
            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
                "average_response_time": average_response_time,
                "query_type_distribution": dict(query_types),
                "requests_last_hour": len(recent_requests),
                "unique_sessions": len(set(r["session_id"] for r in requests if r["session_id"]))
            }

# Global instances
request_logger = RequestLogger()

def get_request_logger() -> RequestLogger:
    """Dependency to get request logger"""
    return request_logger

def log_query_request(query: str, 
                     query_type: str, 
                     response_time: float,
                     success: bool,
                     session_id: Optional[str] = None):
    """Helper function to log requests"""
    request_logger.log_request(query, query_type, response_time, success, session_id)

# Health check utilities
def check_system_health() -> Dict[str, str]:
    """
    Comprehensive system health check
    Returns status of all critical components
    """
    health_status = {}
    
    try:
        # Check RAG engine
        rag_engine = get_rag_engine()
        rag_status = rag_engine.get_system_status()
        health_status.update(rag_status)
        
        # Check API health
        health_status["api_status"] = "healthy"
        
    except Exception as e:
        health_status["api_status"] = f"error: {str(e)}"
    
    return health_status

class ConfigManager:
    """
    Configuration management for the API
    Handles environment-based configuration
    """
    
    def __init__(self):
        import os
        
        self.config = {
            "rate_limit_requests_per_minute": int(os.getenv("RATE_LIMIT_RPM", "30")),
            "max_query_length": int(os.getenv("MAX_QUERY_LENGTH", "1000")),
            "enable_analytics": os.getenv("ENABLE_ANALYTICS", "true").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
            "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
            "api_title": os.getenv("API_TITLE", "Mappy ArcGIS Assistant API"),
            "api_description": os.getenv("API_DESCRIPTION", "AI-powered documentation assistant for ArcGIS JavaScript SDK")
        }
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def update(self, key: str, value):
        """Update configuration value"""
        self.config[key] = value

# Global config instance
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """Dependency to get configuration manager"""
    return config_manager