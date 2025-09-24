from rag.config import GeminiRAGConfig
from rag.models import RAGRequest, ModelType

def test_config():
    try:
        # Test config validation
        GeminiRAGConfig.validate_config()
        print("✅ Configuration valid")
        
        # Test models dictionary
        print(f"Available models: {GeminiRAGConfig.MODELS}")
        print(f"Default model: {GeminiRAGConfig.DEFAULT_MODEL}")
        
        # Test data models
        request = RAGRequest(
            question="How do I create a PointBarrier?",
            model_type=ModelType.FAST
        )
        print(f"✅ Request model working: {request.question}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

if __name__ == "__main__":
    test_config()