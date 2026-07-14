"""Syllabus extraction, comparison, and tagging package."""

from syllabus.extractor import extract_syllabus, save_syllabus_json, load_syllabus_json
from syllabus.comparator import compare_syllabi, compare_syllabi_json
from syllabus.tagger import tag_document_chunks, apply_syllabus_diff, cleanup_old_stale_chunks

__all__ = [
    "extract_syllabus",
    "save_syllabus_json",
    "load_syllabus_json",
    "compare_syllabi",
    "compare_syllabi_json",
    "tag_document_chunks",
    "apply_syllabus_diff",
    "cleanup_old_stale_chunks",
]
