from rag.rag_engine import ArcGISRAGEngine
from rag.models import RAGRequest, ModelType

def test_rag_engine_basic():
    try:
        # Initialize RAG engine
        rag_engine = ArcGISRAGEngine()
        print("✅ RAG engine initialized")
        
        # Test that components are working
        if rag_engine.gemini_client.test_connection():
            print("✅ Gemini client connected")
        else:
            print("❌ Gemini client failed")
            return False
        
        # Test prompt building (without search)
        mock_context_data = type('MockContext', (), {
            'formatted_content': '=== API DOCUMENTATION ===\n[1] PointBarrier Class\nA PointBarrier represents a restriction...',
            'source_mapping': {1: {'title': 'PointBarrier', 'url': 'test.com'}},
            'total_tokens': 100,
            'chunk_count': 1
        })()
        
        prompt = rag_engine._build_prompt("What is a PointBarrier?", mock_context_data)
        print("✅ Prompt building working")
        print(f"   Prompt length: {len(prompt)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG engine test error: {e}")
        return False

if __name__ == "__main__":
    test_rag_engine_basic()