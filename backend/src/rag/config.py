import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class GeminiRAGConfig:
    """Configuration for Gemini RAG system"""
    
    # API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Model Configuration
    MODELS = {
        "fast": "gemini-1.5-flash",
        "quality": "gemini-1.5-flash", 
        "budget": "gemini-1.0-pro"
    }
    
    DEFAULT_MODEL = "fast"
    
    # Generation Parameters
    GENERATION_CONFIG = {
        "temperature": 0.1,      # Factual responses
        "max_output_tokens": 1500,
        "top_p": 0.9,
        "top_k": 40
    }
    
    # Safety Settings (moderate for technical docs)
    SAFETY_SETTINGS = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH", 
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
    
    # RAG Configuration
    MAX_SOURCE_CHUNKS = 10     # Leverage Gemini's large context
    SEARCH_RESULTS = 12        # Get more, then filter to best
    
    # Performance Configuration
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        return True