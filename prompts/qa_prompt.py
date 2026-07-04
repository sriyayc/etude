"""Q&A prompt builder."""


def build_qa_prompt(query: str, chunks: list[dict]) -> str | None:
    """
    Build a structured prompt for grounded Q&A with citations.

    Returns None if chunks is empty — caller should use fallback response.
    """
    if not chunks:
        return None

    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            f"[Source {i}] {chunk['source_file']}, page {chunk['page_number']}\n"
            f"{chunk['chunk_text']}"
        )
    context = "\n\n".join(context_blocks)

    prompt = f"""You are a study assistant helping a student deeply understand their syllabus material before an exam.

Your job is to extract and organize EVERYTHING relevant to the student's question from the context provided — do not summarize away detail, do not skip related points that appear in the context even if not directly asked.

STRICT RULES:
1. Use ONLY the context provided. Never use outside knowledge even if you are certain it is correct. If it is not in the context, it does not exist for this answer.
2. Cite every fact using [Source N] notation immediately after the claim it supports.
3. If the context mentions a closely related or contrasting concept — for example the context discusses TCP and also mentions UDP — include that connection. It helps the student understand the full picture, not just the narrow question asked.
4. If the context only partially answers the question, clearly state what IS covered and what is NOT, rather than filling gaps with assumptions.
5. If nothing in the context is relevant to the question at all, respond with exactly this and nothing else:
   "This topic is not covered in the provided material. Please refer to your textbook directly."

ANSWER STRUCTURE — always follow this order:
1. Direct answer: One clear sentence directly answering the question in plain language.
2. Explanation: Full technical detail drawn from the context — definitions, mechanisms, steps, diagrams described in text, formulae if present. Pull in everything the context offers, organized logically, not just copied in source order.
3. Related concepts: If the context surfaces comparisons, contrasting mechanisms, or prerequisite concepts, include a short section here connecting them. Label it "Related:".
4. Exam note: One sentence highlighting what about this topic is most likely to appear in an exam question, based on how the context emphasizes it.

LANGUAGE:
- Write in clear, precise English suitable for a third-year computer science student.
- Avoid unnecessary jargon but do not oversimplify to the point of losing technical accuracy.
- Use short paragraphs. Do not write walls of text.
- Never start your answer with "Certainly", "Of course", "Great question", or any filler phrase. Start directly with the answer.

Context:
{context}

Question: {query}

Answer:"""

    return prompt
