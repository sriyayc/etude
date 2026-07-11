"""Simple scratch script to test retrieval."""

import os
import sys

# Ensure project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.retriever import retrieve_relevant_chunks

if __name__ == "__main__":
    # Test retrieval with mock parameters (make sure you've ingested documents first!)
    results = retrieve_relevant_chunks(
        query="Explain variables in Python",
        subject="python",
        semester=1,
        n=3
    )
    
    print(f"Retrieved {len(results)} chunks:")
    for idx, chunk in enumerate(results):
        print(f"\n[{idx + 1}] Score: {chunk['score']:.4f} | Source: {chunk['source_file']} (Page {chunk['page_number']})")
        print(f"Text snippet: {chunk['chunk_text'][:150]}...")