import sys
from pathlib import Path

# Import your existing search engine
from simple_search import SimpleMappySearch

# Import RAG components
from rag.rag_engine import ArcGISRAGEngine
from rag.models import RAGRequest, ModelType

def test_full_rag_pipeline():
    try:
        print("Starting full RAG pipeline test...")
        
        # Step 1: Initialize search engine
        search_engine = SimpleMappySearch()
        print("✅ Search engine initialized")
        
        # Step 2: Initialize RAG engine
        rag_engine = ArcGISRAGEngine()
        print("✅ RAG engine initialized")
        
        # Step 3: Connect search to RAG
        rag_engine.connect_search_engine(search_engine)
        print("✅ Search engine connected to RAG")
        
        # Step 4: Test the complete pipeline
        test_questions = [
            "How do I create a PointBarrier?",
            "What is the Widget class?",
            "Show me 3D visualization examples"
        ]
        
        for question in test_questions:
            print(f"\n🧪 Testing: '{question}'")
            
            # Create request
            request = RAGRequest(
                question=question,
                model_type=ModelType.FAST,
                max_sources=8
            )
            
            # Get RAG response
            response = rag_engine.answer_question(request)
            
            if response.error:
                print(f"❌ Error: {response.error}")
            else:
                print(f"✅ Answer generated")
                print(f"   Model: {response.model_used}")
                print(f"   Time: {response.processing_time:.2f}s")
                print(f"   Sources: {len(response.sources)}")
                print(f"   Answer preview: {response.answer[:150]}...")
                
                # Show sources
                if response.sources:
                    print(f"   Top source: {response.sources[0].title}")
        
        print("\n✅ Full RAG pipeline test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Full RAG test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_full_rag_pipeline()