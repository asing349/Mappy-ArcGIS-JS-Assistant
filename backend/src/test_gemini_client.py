from rag.gemini_client import GeminiClient

def test_gemini_client():
    try:
        # Initialize client
        client = GeminiClient()
        print("✅ Gemini client initialized")
        
        # Test connection
        if client.test_connection():
            print("✅ Connection test passed")
        else:
            print("❌ Connection test failed")
            return False
        
        # Test different models
        models_to_test = ["fast", "quality"]
        
        for model_type in models_to_test:
            print(f"\n🧪 Testing {model_type} model...")
            
            result = client.generate_response(
                "Explain what ArcGIS is in one sentence.", 
                model_type
            )
            
            if result.get("error"):
                print(f"❌ {model_type} model error: {result['error']}")
            else:
                print(f"✅ {model_type} model working")
                print(f"   Response: {result['content'][:100]}...")
                print(f"   Time: {result['processing_time']:.2f}s")
                print(f"   Model: {result['model_used']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Client test error: {e}")
        return False

if __name__ == "__main__":
    test_gemini_client()