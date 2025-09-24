"""
Analyze content length distribution to understand document quality
"""

from src.simple_corpus_loader import SimpleCorpusLoader
import statistics

def analyze_content_distribution():
    """Analyze the actual content lengths in our corpus."""
    
    loader = SimpleCorpusLoader()
    documents = loader.load_corpus()
    
    if not documents:
        print("No documents loaded")
        return
    
    # Analyze content lengths
    content_lengths = [len(doc['content']) for doc in documents]
    
    print("\n" + "="*60)
    print("CONTENT LENGTH ANALYSIS")
    print("="*60)
    
    print(f"Total documents: {len(documents)}")
    print(f"Average content length: {statistics.mean(content_lengths):.0f} characters")
    print(f"Median content length: {statistics.median(content_lengths):.0f} characters")
    print(f"Min content length: {min(content_lengths)} characters")
    print(f"Max content length: {max(content_lengths)} characters")
    
    # Content length distribution
    ranges = [
        (0, 100, "Very short (0-100 chars)"),
        (101, 500, "Short (101-500 chars)"),
        (501, 2000, "Medium (501-2000 chars)"),
        (2001, 10000, "Long (2001-10000 chars)"),
        (10001, float('inf'), "Very long (10000+ chars)")
    ]
    
    print(f"\nContent length distribution:")
    for min_len, max_len, label in ranges:
        count = len([l for l in content_lengths if min_len <= l <= max_len])
        percentage = (count / len(content_lengths)) * 100
        print(f"  {label}: {count} docs ({percentage:.1f}%)")
    
    # Sample documents from each category
    print(f"\nSample documents:")
    
    # Find examples of different lengths
    by_type = {}
    for doc in documents:
        doc_type = doc['type']
        if doc_type not in by_type:
            by_type[doc_type] = []
        by_type[doc_type].append(doc)
    
    for doc_type, docs in by_type.items():
        # Sort by content length and show range
        docs_sorted = sorted(docs, key=lambda x: len(x['content']))
        shortest = docs_sorted[0]
        longest = docs_sorted[-1]
        median_idx = len(docs_sorted) // 2
        median = docs_sorted[median_idx]
        
        print(f"\n{doc_type.upper()} documents:")
        print(f"  Shortest: {len(shortest['content'])} chars - '{shortest['title'][:50]}...'")
        print(f"  Median: {len(median['content'])} chars - '{median['title'][:50]}...'")
        print(f"  Longest: {len(longest['content'])} chars - '{longest['title'][:50]}...'")
        
        # Show content preview for the median document
        content_preview = median['content'][:200].replace('\n', ' ')
        print(f"  Content preview: '{content_preview}...'")

if __name__ == "__main__":
    analyze_content_distribution()