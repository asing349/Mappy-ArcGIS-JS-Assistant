"""
Gemini Client - LLM Interface for Mappy RAG System
Handles all interactions with Google's Gemini API
"""

import google.generativeai as genai
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import os
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Structured response from the LLM"""
    content: str
    tokens_used: int
    response_time: float
    model_used: str
    success: bool
    error_message: Optional[str] = None

class GeminiClient:
    """Client for interacting with Gemini API"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = "gemini-2.5-flash",
                 max_retries: int = 3):
        """
        Initialize Gemini client
        
        Args:
            api_key: Gemini API key (if None, reads from .env file)
            model_name: Gemini model to use
            max_retries: Maximum retry attempts for failed requests
        """
        self.model_name = model_name
        self.max_retries = max_retries
        
        # Load environment variables from project root .env file
        project_root = Path(__file__).parent.parent.parent  # Go up from src/rag/ to project root
        env_path = project_root / ".env"
        
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from: {env_path}")
        else:
            logger.warning(f"No .env file found at: {env_path}")
        
        # Configure API key
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                f"Gemini API key not provided. Please add GEMINI_API_KEY to {env_path} "
                "or set as environment variable."
            )
        
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(model_name)
        
        # Generation config for consistent responses
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,  # Low temperature for factual responses
            top_p=0.8,
            top_k=40,
            max_output_tokens=2048,
            candidate_count=1
        )
        
        # Safety settings - Allow most content for documentation
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        logger.info(f"Gemini client initialized with model: {model_name}")
    
    def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> LLMResponse:
        """
        Generate response from Gemini
        
        Args:
            prompt: User prompt
            system_instruction: System instruction for the model
            
        Returns:
            LLMResponse with generated content and metadata
        """
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                # Prepare full prompt
                full_prompt = prompt
                if system_instruction:
                    full_prompt = f"{system_instruction}\n\n{prompt}"
                
                # Generate response
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                
                # Check for blocked content
                if not response.text:
                    error_msg = "Response was blocked or empty"
                    if hasattr(response, 'prompt_feedback'):
                        error_msg += f" - {response.prompt_feedback}"
                    
                    logger.warning(f"Attempt {attempt + 1}: {error_msg}")
                    if attempt == self.max_retries - 1:
                        return LLMResponse(
                            content="",
                            tokens_used=0,
                            response_time=time.time() - start_time,
                            model_used=self.model_name,
                            success=False,
                            error_message=error_msg
                        )
                    continue
                
                # Calculate tokens (approximate)
                tokens_used = len(response.text.split()) + len(full_prompt.split())
                
                response_time = time.time() - start_time
                
                logger.info(f"Gemini response generated in {response_time:.2f}s (~{tokens_used} tokens)")
                
                return LLMResponse(
                    content=response.text,
                    tokens_used=tokens_used,
                    response_time=response_time,
                    model_used=self.model_name,
                    success=True
                )
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    return LLMResponse(
                        content="",
                        tokens_used=0,
                        response_time=time.time() - start_time,
                        model_used=self.model_name,
                        success=False,
                        error_message=str(e)
                    )
                
                # Wait before retry
                time.sleep(2 ** attempt)
        
        # Should never reach here
        return LLMResponse(
            content="",
            tokens_used=0,
            response_time=time.time() - start_time,
            model_used=self.model_name,
            success=False,
            error_message="Max retries exceeded"
        )
    
    def test_connection(self) -> bool:
        """Test if Gemini API is working"""
        try:
            test_response = self.generate_response("Say 'API connection successful'")
            return test_response.success and "successful" in test_response.content.lower()
        except Exception as e:
            logger.error(f"Gemini API test failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            # Get available models
            models = list(genai.list_models())
            current_model_info = None
            
            for model in models:
                if self.model_name in model.name:
                    current_model_info = {
                        "name": model.name,
                        "display_name": model.display_name,
                        "description": model.description,
                        "input_token_limit": getattr(model, 'input_token_limit', 'Unknown'),
                        "output_token_limit": getattr(model, 'output_token_limit', 'Unknown'),
                    }
                    break
            
            return {
                "current_model": self.model_name,
                "model_info": current_model_info,
                "available_models": [m.name for m in models]
            }
            
        except Exception as e:
            logger.error(f"Could not get model info: {e}")
            return {"error": str(e)}

def main():
    """Test the Gemini client"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Gemini Client...")
    
    try:
        # Initialize client
        client = GeminiClient()
        
        # Test connection
        print("\n1. Testing API connection...")
        if client.test_connection():
            print("   ✅ API connection successful")
        else:
            print("   ❌ API connection failed")
            return
        
        # Get model info
        print("\n2. Getting model information...")
        model_info = client.get_model_info()
        print(f"   Model: {model_info.get('current_model', 'Unknown')}")
        
        # Test basic response
        print("\n3. Testing basic response generation...")
        response = client.generate_response(
            "Explain what ArcGIS JavaScript SDK is in one sentence."
        )
        
        if response.success:
            print(f"   ✅ Response generated in {response.response_time:.2f}s")
            print(f"   📝 Content: {response.content}")
        else:
            print(f"   ❌ Response failed: {response.error_message}")
        
        # Test with system instruction
        print("\n4. Testing with system instruction...")
        system_instruction = "You are a helpful assistant for ArcGIS JavaScript SDK documentation. Provide concise, accurate answers."
        
        response = client.generate_response(
            "What is a PointBarrier in routing?",
            system_instruction=system_instruction
        )
        
        if response.success:
            print(f"   ✅ Response with system instruction generated")
            print(f"   📝 Content: {response.content[:200]}...")
        else:
            print(f"   ❌ Response failed: {response.error_message}")
        
        print("\n✅ Gemini client testing complete!")
        
    except Exception as e:
        print(f"❌ Gemini client test failed: {e}")

if __name__ == "__main__":
    main()