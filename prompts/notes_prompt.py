"""Notes prompt builder."""

def build_notes_prompt(topic: str, chunks: list[dict]) -> str:
    """
    Build a structured prompt to generate study/revision notes.
    """
    if not chunks:
        return None
        
    context_str = "\n---\n".join([
        f"[Source {idx + 1}] {c['source_file']} (Page {c['page_number']}):\n{c['chunk_text']}"
        for idx, c in enumerate(chunks)
    ])
    
    prompt = f"""You are an academic summary assistant. Generate comprehensive, beautifully formatted study/revision notes for the topic '{topic}' based ONLY on the provided reference materials.

Your study notes should include:
1. An overview of the topic.
2. Key sub-concepts (with bullet points and explanations).
3. Code examples, definitions, or equations if present in the source text.
4. Inline citations of the sources (e.g. [Source X]) when introducing definitions or concepts.

REFERENCE MATERIALS:
---
{context_str}
---

Write the notes in clean, standard Markdown format. Use headers, bold text, lists, and code blocks to make it highly readable for students. Do not write any preamble (e.g. "Here are the notes:") - start directly with the title of the notes.
"""
    return prompt
