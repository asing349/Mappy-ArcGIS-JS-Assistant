# Test RAG with artificial content to prove the system works
class MockSearchEngine:
    def search(self, query, n_results=5):
        # Mock search results with actual content
        mock_results = [
            {
                'title': 'PointBarrier Class',
                'content': '''The PointBarrier class represents a point location that restricts travel. 
                
Constructor:
new PointBarrier({
  geometry: Point,
  barrierType: "restriction" | "scaled-cost"
})

Example:
const barrier = new PointBarrier({
  geometry: new Point({longitude: -118, latitude: 34}),
  barrierType: "restriction"
});''',
                'doc_type': 'api_reference',
                'url': 'https://developers.arcgis.com/javascript/latest/api-reference/esri-rest-support-PointBarrier.html',
                'similarity_score': 0.9
            }
        ]
        
        return {
            'results': mock_results,
            'total_results': len(mock_results)
        }

# Test RAG with mock content
from rag.rag_engine import ArcGISRAGEngine
from rag.models import RAGRequest, ModelType

def test_rag_with_content():
    rag_engine = ArcGISRAGEngine()
    mock_search = MockSearchEngine()
    rag_engine.connect_search_engine(mock_search)
    
    request = RAGRequest(
        question="How do I create a PointBarrier?",
        model_type=ModelType.FAST
    )
    
    response = rag_engine.answer_question(request)
    
    print("RAG Response with Real Content:")
    print(f"Answer: {response.answer}")
    print(f"Sources: {len(response.sources)}")
    print(f"Error: {response.error}")

if __name__ == "__main__":
    test_rag_with_content()