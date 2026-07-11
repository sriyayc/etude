"""QA Prompt builder."""

def build_qa_prompt(query: str, chunks: list[dict]) -> str:
    """
    Build a structured prompt for the LLM using the query and retrieved chunks.
    
    Args:
        query: The user's question.
        chunks: List of retrieved chunks with 'chunk_text', 'source_file', 'page_number'.
        
    Returns:
        Structured prompt string, or None if no valid context is available.
    """
    if not chunks:
        return None
        
    context_blocks = []
    for idx, chunk in enumerate(chunks):
        text = chunk.get("chunk_text", "").strip()
        source = chunk.get("source_file", "unknown source")
        page = chunk.get("page_number", "?")
        if text:
            context_blocks.append(
                f"[Source {idx + 1}] {source} (Page {page}):\n{text}\n"
            )
            
    if not context_blocks:
        return None
        
    context_str = "\n---\n".join(context_blocks)
    
    prompt = f"""You are a helpful and precise teaching assistant. Your goal is to answer the student's question based ONLY on the provided reference materials.

If the answer cannot be determined or inferred from the provided context, politely decline to answer and state that you do not have that information. Do not invent details or use external knowledge.

REFERENCE MATERIALS:
---
{context_str}
---

STUDENT QUESTION: {query}

Please formulate a clear, detailed, and directly structured answer. Cite your sources inline using [Source X] notation where appropriate.
"""
    return prompt