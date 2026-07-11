"""Doubts prompt builder."""

def build_doubts_prompt(doubt: str, chunks: list[dict]) -> str:
    """
    Build a structured prompt to resolve a student doubt.
    """
    if not chunks:
        return None
        
    context_str = "\n---\n".join([
        f"[Source {idx + 1}] {c['source_file']} (Page {c['page_number']}):\n{c['chunk_text']}"
        for idx, c in enumerate(chunks)
    ])
    
    prompt = f"""You are a patient and knowledgeable tutor. A student has expressed a doubt or confusion about a concept. Use ONLY the provided reference materials to clarify their doubt.

REFERENCE MATERIALS:
---
{context_str}
---

STUDENT'S DOUBT:
{doubt}

Explain the concept clearly, address their specific confusion step-by-step, and cite the source materials where applicable. If the reference material doesn't contain the answer to resolve their doubt, state that the provided notes do not contain this information.
"""
    return prompt
