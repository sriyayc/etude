"""Flashcard prompt builder."""

def build_flashcard_prompt(topic: str, chunks: list[dict], num_cards: int = 8) -> str:
    """
    Build a structured prompt to generate revision flashcards.
    """
    if not chunks:
        return None
        
    context_str = "\n---\n".join([
        f"[Source {idx + 1}] {c['source_file']} (Page {c['page_number']}):\n{c['chunk_text']}"
        for idx, c in enumerate(chunks)
    ])
    
    prompt = f"""You are a study helper. Generate exactly {num_cards} flashcards for study/revision on the topic '{topic}' based ONLY on the provided reference materials.

Each flashcard must have:
1. 'front': A question, concept, or term.
2. 'back': A concise answer, definition, or explanation citing sources (e.g. [Source X]).

REFERENCE MATERIALS:
---
{context_str}
---

Your response MUST be a valid JSON list of objects, and nothing else. Do not write any conversational text before or after the JSON.

JSON Schema:
[
  {{
    "front": "Question/Term...",
    "back": "Answer/Definition citing [Source X]..."
  }}
]
"""
    return prompt
