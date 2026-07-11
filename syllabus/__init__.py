"""Syllabus extraction, comparison, and tagging package."""

from syllabus.extractor import extract_syllabus
from syllabus.comparator import compare_syllabi
from syllabus.tagger import tag_document_chunks

__all__ = [
    "extract_syllabus",
    "compare_syllabi",
    "tag_document_chunks",
]
