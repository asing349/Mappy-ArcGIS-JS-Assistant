import os
from dotenv import load_dotenv
import google.generativeai as genai

def test_gemini_api():
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            print("Make sure you have GEMINI_API_KEY in your .env file")
            return False
        
        print(f"✅ API key loaded (first 10 chars): {api_key[:10]}...")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Test with simple model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content("Hello, are you working?")
        
        print("✅ Gemini API working!")
        print(f"Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

if __name__ == "__main__":
    test_gemini_api()