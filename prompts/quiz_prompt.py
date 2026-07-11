"""Quiz prompt builder."""

def build_quiz_prompt(topic: str, chunks: list[dict], num_questions: int = 5) -> str:
    """
    Build a structured prompt to generate a multiple-choice quiz.
    """
    if not chunks:
        return None
        
    context_str = "\n---\n".join([
        f"[Source {idx + 1}] {c['source_file']} (Page {c['page_number']}):\n{c['chunk_text']}"
        for idx, c in enumerate(chunks)
    ])
    
    prompt = f"""You are an expert exam creator. Generate a multiple-choice quiz of exactly {num_questions} questions about the topic '{topic}' based ONLY on the provided reference materials.

For each question:
1. Provide exactly 4 options.
2. Identify the correct answer (must match one of the options exactly).
3. Provide a brief explanation citing the sources where the answer is found.

REFERENCE MATERIALS:
---
{context_str}
---

Your response MUST be a valid JSON list of objects, and nothing else. Do not write any conversational text before or after the JSON.

JSON Schema:
[
  {{
    "question": "Question text here...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A",
    "explanation": "Explanation here citing [Source X]..."
  }}
]
"""
    return prompt
