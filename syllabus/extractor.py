"""Syllabus extraction module."""

import json
import logging
from ingestion.extract import extract_pages
from prompts.syllabus_prompt import build_syllabus_prompt
from providers.factory import get_llm
from db.syllabus_repo import create_topic, list_current_topics, mark_outdated

logger = logging.getLogger(__name__)


def extract_syllabus(
    pdf_path: str,
    document_id: str,
    subject: str,
    semester: int,
    version: int = 1,
) -> dict:
    """
    Extract syllabus units and topics from a syllabus PDF and save them to the DB.
    Also handles versioning by marking previous versions as outdated.
    """
    # 1. Extract text from PDF
    print(f"Extracting syllabus text from {pdf_path}...")
    pages = extract_pages(pdf_path)
    full_text = "\n".join([p["text"] for p in pages])

    if not full_text.strip():
        return {
            "success": False,
            "message": "Syllabus PDF is empty or text could not be extracted.",
            "topics_count": 0,
        }

    # 2. Call LLM to parse text into structured units/topics
    print("Parsing syllabus text with LLM...")
    prompt = build_syllabus_prompt(full_text)
    llm = get_llm()
    raw_response = llm.generate(prompt)

    try:
        # Strip markdown wrapping if present
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        units = json.loads(clean_response)

        # 3. Handle versioning: Mark existing current syllabus topics as outdated
        current_topics = list_current_topics(subject=subject, semester=semester)
        if current_topics:
            old_version = max(t["version"] for t in current_topics)
            mark_outdated(subject=subject, semester=semester, version=old_version)
            version = old_version + 1

        # 4. Insert new topics to Database
        topics_count = 0
        inserted_topics = []
        for unit in units:
            unit_num = unit.get("unit_number")
            unit_title = unit.get("unit_title", "")
            topics = unit.get("topics", [])

            for topic in topics:
                create_topic(
                    document_id=document_id,
                    subject=subject,
                    semester=semester,
                    unit_number=unit_num,
                    unit_title=unit_title,
                    topic=topic,
                    version=version,
                    is_current=True,
                )
                topics_count += 1
                inserted_topics.append({
                    "unit_number": unit_num,
                    "unit_title": unit_title,
                    "topic": topic,
                })

        return {
            "success": True,
            "message": f"Successfully extracted and saved {topics_count} topics.",
            "topics_count": topics_count,
            "version": version,
            "topics": inserted_topics,
        }

    except Exception as e:
        logger.error(f"Failed to parse syllabus extraction: {e}\nRaw response:\n{raw_response}")
        return {
            "success": False,
            "message": f"Failed to extract syllabus. Error: {str(e)}",
            "topics_count": 0,
        }
