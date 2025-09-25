"""
Prompt Builder - Intelligent Synthesis for Mappy RAG System
Clean, focused implementation that encourages synthesis over regurgitation
"""

import logging
from typing import Optional
import re
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries the system can handle"""
    API_REFERENCE = "api_reference"
    HOW_TO = "how_to" 
    CONCEPTUAL = "conceptual"
    TROUBLESHOOTING = "troubleshooting"
    CODE_EXAMPLE = "code_example"
    COMPARISON = "comparison"
    GENERAL = "general"

class PromptBuilder:
    """Builds prompts that encourage intelligent synthesis"""
    
    def __init__(self):
        """Initialize with query classification patterns"""
        
        self.query_patterns = {
            QueryType.API_REFERENCE: [
                r'\b(api|class|method|property|parameter|return)\b',
                r'\b(documentation|reference|spec)\b',
                r'\b(what is|define)\b.*\b(class|method|property)\b'
            ],
            QueryType.HOW_TO: [
                r'\bhow\s+(to|do|can)\b',
                r'\b(implement|create|build|setup|configure)\b',
                r'\b(step|tutorial|guide)\b'
            ],
            QueryType.CODE_EXAMPLE: [
                r'\b(example|sample|code|snippet)\b',
                r'\bshow\s+me\b',
                r'\b(demonstrate|illustrate)\b'
            ],
            QueryType.TROUBLESHOOTING: [
                r'\b(error|problem|issue|bug|fix|debug)\b',
                r'\b(not working|failed|broken)\b',
                r'\b(why|what\'s wrong)\b'
            ],
            QueryType.COMPARISON: [
                r'\b(vs|versus|compare|difference|better)\b',
                r'\b(which|what\'s the)\b.*\b(best|better)\b'
            ],
            QueryType.CONCEPTUAL: [
                r'\b(concept|theory|principle|architecture)\b',
                r'\b(explain|understand|learn)\b',
                r'\b(what are|what is)\b'
            ]
        }

    def classify_query(self, query: str) -> QueryType:
        """Classify the query type based on patterns"""
        query_lower = query.lower()
        
        scores = {}
        for query_type, patterns in self.query_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            scores[query_type] = score
        
        if max(scores.values()) == 0:
            return QueryType.GENERAL
        
        return max(scores, key=scores.get)

    def build_complete_prompt(self, 
                            query: str, 
                            context: str,
                            query_type: Optional[QueryType] = None) -> str:
        """Build a complete prompt that encourages synthesis"""
        
        if query_type is None:
            query_type = self.classify_query(query)
        
        # Get query-specific guidance
        query_guidance = self._get_query_guidance(query_type)
        
        prompt = f"""You are an expert ArcGIS JavaScript SDK assistant with deep technical knowledge. Your role is to provide helpful, accurate guidance by synthesizing information from the ArcGIS documentation.

SYNTHESIS APPROACH:
- Analyze the provided documentation to understand the topic
- Combine information from multiple sources when relevant
- Fill in logical gaps using your ArcGIS expertise
- Create coherent, practical guidance that goes beyond just repeating documentation
- Focus on what developers actually need to know to succeed

FORMATTING REQUIREMENTS - FOLLOW EXACTLY:
- Use ## for main sections only
- Use ### for subsections only  
- NEVER use #### (4 hashes) - use ### instead
- Use --- for section dividers
- Use ```javascript, ```html, ```css for code blocks
- Keep response under 3200 tokens while being comprehensive

Based on these ArcGIS JavaScript SDK documentation excerpts:

{context}

---

USER QUESTION: {query}

{query_guidance}

Provide a comprehensive response that synthesizes the documentation into practical guidance. Structure your response naturally and focus on being genuinely helpful to an ArcGIS developer. If the documentation doesn't fully cover the question, use your ArcGIS knowledge to provide additional helpful context while being clear about what comes from the docs vs. your expertise."""

        return prompt

    def _get_query_guidance(self, query_type: QueryType) -> str:
        """Get specific guidance based on query type"""
        
        guidance_map = {
            QueryType.HOW_TO: "IMPLEMENTATION FOCUS: Provide step-by-step guidance with working code. Include necessary imports, initialization, and error handling. Explain each step clearly and mention common pitfalls.",
            
            QueryType.API_REFERENCE: "API FOCUS: Explain the API clearly with proper syntax, parameters, and return values. Include practical usage examples and mention related APIs that developers often use together.",
            
            QueryType.CODE_EXAMPLE: "EXAMPLE FOCUS: Provide complete, working code examples with clear explanations. Include necessary setup code and explain key concepts demonstrated in the example.",
            
            QueryType.TROUBLESHOOTING: "PROBLEM-SOLVING FOCUS: Identify likely causes and provide practical solutions. Include diagnostic steps and prevention strategies. Be specific about error conditions.",
            
            QueryType.COMPARISON: "COMPARISON FOCUS: Provide objective analysis of different approaches. Explain when to use each option, with pros/cons and practical considerations.",
            
            QueryType.CONCEPTUAL: "UNDERSTANDING FOCUS: Explain concepts clearly with practical context. Help the developer understand not just how something works, but why it's designed that way.",
            
            QueryType.GENERAL: "COMPREHENSIVE FOCUS: Address all aspects of the question thoroughly. Provide practical guidance that helps the developer succeed with their implementation."
        }
        
        return guidance_map.get(query_type, guidance_map[QueryType.GENERAL])