"""Quiz generation feature."""

import json
import logging
from retrieval.retriever import retrieve
from prompts.quiz_prompt import build_quiz_prompt
from providers.factory import get_llm

logger = logging.getLogger(__name__)

def generate_quiz(
    topic: str,
    subject: str,
    semester: int,
    num_questions: int = 5
) -> dict:
    """
    Generate a multiple-choice quiz on a topic using retrieved reference materials.
    """
    chunks = retrieve(query=topic, subject=subject, semester=semester, n=5)
    
    if not chunks:
        return {
            "success": False,
            "message": f"No reference materials found for topic '{topic}' to generate a quiz.",
            "questions": []
        }
        
    prompt = build_quiz_prompt(topic, chunks, num_questions)
    
    llm = get_llm()
    raw_response = llm.generate(prompt)
    
    try:
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()
        
        questions = json.loads(clean_response)
        
        return {
            "success": True,
            "questions": questions,
            "sources": [
                {
                    "source_file": c["source_file"],
                    "page_number": c["page_number"]
                }
                for c in chunks
            ]
        }
    except Exception as e:
        logger.error(f"Failed to parse quiz response: {e}\nRaw response:\n{raw_response}")
        return {
            "success": False,
            "message": "Failed to parse the generated quiz. Please try again.",
            "questions": []
        }
