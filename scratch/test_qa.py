"""Test script for the Q&A feature."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.qa import answer_question

if __name__ == "__main__":
    result = answer_question(
        query="What is UE23CS151A and what is it about?",
        subject="python",
        semester=1
    )
    
    print("\n=== QUESTION ===")
    print(result["query"])
    print("\n=== ANSWER ===")
    print(result["answer"])
    print("\n=== SOURCES ===")
    for src in result["sources"]:
        print(f"- {src['source_file']} (Page {src['page_number']}) [Score: {src['score']}]")
    print(f"\nGrounded: {result['grounded']}")