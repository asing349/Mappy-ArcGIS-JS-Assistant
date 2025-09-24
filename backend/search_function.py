
def search_arcgis_docs(query: str, n_results: int = 5):
    """
    Working search function for ArcGIS documentation.
    
    Args:
        query: Search query string
        n_results: Number of results to return
        
    Returns:
        List of search results with content and metadata
    """
    import chromadb
    from chromadb.config import Settings
    import ollama
    from pathlib import Path
    
    # Initialize ChromaDB
    vector_store_dir = Path("data/vector_store")
    client = chromadb.PersistentClient(
        path=str(vector_store_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get collection
    collection = client.get_collection("arcgis_docs")
    
    # Generate query embedding
    response = ollama.embeddings(
        model='nomic-embed-text',
        prompt=query
    )
    query_embedding = response['embedding']
    
    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )
    
    # Format results
    formatted_results = []
    if results['documents'] and len(results['documents'][0]) > 0:
        for doc, metadata, distance in zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        ):
            formatted_results.append({
                'content': doc,
                'metadata': metadata,
                'distance': distance,
                'doc_type': metadata.get('doc_type', 'unknown'),
                'chunk_type': metadata.get('chunk_type', 'unknown')
            })
    
    return formatted_results

# Example usage:
if __name__ == "__main__":
    results = search_arcgis_docs("PointBarrier routing analysis")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['doc_type']} - {result['chunk_type']}")
        print(f"   Distance: {result['distance']:.3f}")
        print(f"   Content: {result['content'][:100]}...")
        print()
