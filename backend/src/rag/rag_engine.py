"""
RAG Engine - Simplified RAG Orchestration for Mappy ArcGIS Assistant
Fixed import for SimpleMappySearch
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys

logger = logging.getLogger(__name__)

# Add src directory to path and import SimpleMappySearch
try:
    # Add src to path from any location
    src_path = Path(__file__).parent.parent  # Go up from rag/ to src/
    sys.path.insert(0, str(src_path))
    
    from simple_search import SimpleMappySearch
    logger.info("Imported SimpleMappySearch successfully")
except ImportError as e:
    logger.error(f"Could not import SimpleMappySearch: {e}")
    SimpleMappySearch = None

# Import RAG components from current directory (src/rag/)
from .gemini_client import GeminiClient, LLMResponse
from .context_assembler import ContextAssembler, AssembledContext
from .prompt_builder import PromptBuilder, QueryType

@dataclass
class RAGResponse:
    """Complete response from the RAG system"""
    answer: str
    sources: List[Dict[str, str]]
    query_type: str
    context_stats: Dict[str, Any]
    performance_metrics: Dict[str, float]
    success: bool
    error_message: Optional[str] = None

class MappyRAGEngine:
    """Simplified RAG engine using your working ChromaDB search"""
    
    def __init__(self, 
                 gemini_api_key: Optional[str] = None,
                 gemini_model: str = "gemini-1.5-flash",
                 max_context_length: int = 8000,
                 max_search_results: int = 10):
        """
        Initialize the RAG engine
        
        Args:
            gemini_api_key: Gemini API key
            gemini_model: Gemini model to use
            max_context_length: Maximum context length for LLM
            max_search_results: Maximum search results to retrieve
        """
        self.max_search_results = max_search_results
        
        # Initialize your working search engine
        if SimpleMappySearch is None:
            raise ValueError("SimpleMappySearch not available. Check simple_search.py in src/")
        
        self.search_engine = SimpleMappySearch()
        logger.info("Initialized SimpleMappySearch for ChromaDB vector search")
        
        # Initialize RAG components
        self.context_assembler = ContextAssembler(max_context_length=max_context_length)
        self.prompt_builder = PromptBuilder()
        self.gemini_client = GeminiClient(api_key=gemini_api_key, model_name=gemini_model)
        
        logger.info(f"RAG Engine initialized with Gemini model: {gemini_model}")
    
    def query(self, 
             user_query: str,
             context_focus: str = "balanced") -> RAGResponse:
        """
        Process a complete RAG query using your ChromaDB embeddings
        
        Args:
            user_query: The user's question
            context_focus: "balanced", "api", "tutorial", or "examples"
            
        Returns:
            RAGResponse with answer and metadata
        """
        start_time = time.time()
        performance_metrics = {}
        
        try:
            logger.info(f"Processing query: '{user_query}'")
            
            # Step 1: Vector search using your ChromaDB with real embeddings
            search_start = time.time()
            search_results = self.search_engine.search(user_query, n_results=self.max_search_results)
            performance_metrics["search_time"] = time.time() - search_start
            
            logger.info(f"Search found {search_results.get('total_results', 0)} results in {search_results.get('search_time', 0):.3f}s")
            
            if not search_results.get("results"):
                return RAGResponse(
                    answer="I couldn't find any relevant ArcGIS JavaScript SDK documentation for your query. Please try rephrasing your question or using different keywords.",
                    sources=[],
                    query_type="no_results",
                    context_stats={"no_results": True},
                    performance_metrics=performance_metrics,
                    success=False,
                    error_message="No search results found"
                )
            
            # Step 2: Assemble context from search results
            context_start = time.time()
            assembled_context = self.context_assembler.assemble_context(
                search_results, user_query, context_focus
            )
            performance_metrics["context_assembly_time"] = time.time() - context_start
            
            # Step 3: Build optimized prompt
            prompt_start = time.time()
            detected_query_type = self.prompt_builder.classify_query(user_query)
            complete_prompt = self.prompt_builder.build_complete_prompt(
                user_query, assembled_context.context_text, detected_query_type
            )
            performance_metrics["prompt_building_time"] = time.time() - prompt_start
            
            logger.info(f"Query classified as: {detected_query_type.value}")
            
            # Step 4: Generate response with Gemini
            llm_start = time.time()
            llm_response = self.gemini_client.generate_response(complete_prompt)
            performance_metrics["llm_response_time"] = time.time() - llm_start
            
            if not llm_response.success:
                return RAGResponse(
                    answer="I apologize, but I encountered an error while generating a response. Please try again.",
                    sources=assembled_context.sources,
                    query_type=detected_query_type.value,
                    context_stats=assembled_context.context_stats,
                    performance_metrics=performance_metrics,
                    success=False,
                    error_message=llm_response.error_message
                )
            
            # Step 5: Format final response
            final_answer = self._format_response(llm_response.content, assembled_context.sources)
            
            performance_metrics["total_time"] = time.time() - start_time
            
            logger.info(f"RAG query completed in {performance_metrics['total_time']:.2f}s")
            
            return RAGResponse(
                answer=final_answer,
                sources=assembled_context.sources,
                query_type=detected_query_type.value,
                context_stats=assembled_context.context_stats,
                performance_metrics=performance_metrics,
                success=True
            )
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            performance_metrics["total_time"] = time.time() - start_time
            
            return RAGResponse(
                answer="I apologize, but I encountered an unexpected error. Please try again or rephrase your question.",
                sources=[],
                query_type="error",
                context_stats={"error": True},
                performance_metrics=performance_metrics,
                success=False,
                error_message=str(e))
    
    def _format_response(self, response: str, sources: List[Dict[str, str]]) -> str:
        """Format the final response with proper citations"""
        
        formatted = response.strip()
        
        # Add sources section if sources exist and not already present
        if sources and "References:" not in formatted and "Sources:" not in formatted:
            formatted += "\n\n## References\n\n"
            for i, source in enumerate(sources[:5], 1):  # Top 5 sources
                formatted += f"{i}. [{source['title']}]({source['url']})\n"
        
        return formatted
    
    def test_rag_pipeline(self):
        """Test the complete RAG pipeline with sample queries"""
        
        test_queries = [
            "What is PointBarrier in ArcGIS?",
            "How to create a 3D scene view?", 
            "Show me an example of adding a feature layer",
            "FeatureLayer vs GraphicsLayer comparison"
        ]
        
        logger.info("\n" + "="*60)
        logger.info("Testing Complete RAG Pipeline")
        logger.info("="*60)
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\nTest {i}: '{query}'")
            
            try:
                response = self.query(query)
                
                if response.success:
                    logger.info(f"   ✅ Success!")
                    logger.info(f"   📊 Query type: {response.query_type}")
                    logger.info(f"   📋 Sources: {len(response.sources)}")
                    logger.info(f"   ⏱️  Total time: {response.performance_metrics.get('total_time', 0):.2f}s")
                    logger.info(f"   🔍 Answer preview: {response.answer[:150]}...")
                else:
                    logger.error(f"   ❌ Failed: {response.error_message}")
                    
            except Exception as e:
                logger.error(f"   ❌ Test failed: {e}")
        
        logger.info("\n✅ RAG pipeline testing complete!")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Check status of all system components"""
        
        status = {}
        
        # Test search engine (ChromaDB + Vertex AI)
        try:
            test_search = self.search_engine.search("test query", n_results=1)
            status["search_engine"] = "working" if test_search.get("results") else "no_results"
        except Exception as e:
            status["search_engine"] = f"failed: {e}"
        
        # Test Gemini client
        try:
            status["gemini_client"] = "working" if self.gemini_client.test_connection() else "failed"
        except Exception as e:
            status["gemini_client"] = f"failed: {e}"
        
        # Other components
        status["context_assembler"] = "initialized"
        status["prompt_builder"] = "initialized"
        
        return status