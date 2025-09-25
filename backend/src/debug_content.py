#!/usr/bin/env python3
"""
Test script for Mappy search functionality
Run from backend/src/ directory
"""

from simple_search import SimpleMappySearch

def test_search():
    # Initialize search service
    search = SimpleMappySearch()
    
    # Test queries
    test_queries = [
        "how to create a map with ArcGIS",
        "elevation layer 3D",
        "JavaScript SDK sample code",
        "add markers to map",
        "popup configuration"
    ]
    
    print("Testing search with new contextual embeddings...")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        results = search.search(query, n_results=3)
        
        if results['total_results'] > 0:
            for result in results['results']:
                print(f"Rank {result['rank']}: {result['title']}")
                print(f"Score: {result['similarity_score']:.3f}")
                print(f"Type: {result['doc_type']}")
                print(f"Content: {result['content'][:100]}...")
                print()
        else:
            print("No results found")
            
        print(f"Search time: {results['search_time']:.3f}s")
        print("=" * 40)

if __name__ == "__main__":
    test_search()