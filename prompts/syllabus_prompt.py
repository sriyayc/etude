"""Syllabus extraction prompt builder."""

def build_syllabus_prompt(syllabus_text: str) -> str:
    """
    Build a prompt to extract structured units and topics from syllabus text.
    """
    prompt = f"""You are an academic curriculum compiler. Analyze the provided syllabus text and extract a structured list of units, unit titles, and topics.

SYLLABUS TEXT:
---
{syllabus_text}
---

Your response MUST be a valid JSON list of objects, and nothing else. Do not write any conversational text before or after the JSON.

JSON Schema:
[
  {{
    "unit_number": 1,
    "unit_title": "Unit Title...",
    "topics": ["Topic 1", "Topic 2", "Topic 3"]
  }}
]
"""
    return prompt
