"""Syllabus service."""

from services.auth_service import require_admin
from syllabus.extractor import extract_syllabus, save_syllabus_json, load_syllabus_json
from syllabus.comparator import compare_syllabi, compare_syllabi_json
from syllabus.tagger import tag_document_chunks, apply_syllabus_diff


def upload_and_process_syllabus(
    file_path: str,
    subject: str,
    semester: int,
    academic_year: str = None,
) -> dict:
    """
    Process an uploaded syllabus:
    1. Upload to storage as a document
    2. Extract topics and save to syllabus_topics table
    3. Return rich JSON with embeddings for comparison
    """
    from services.document_service import upload_document

    doc_res = upload_document(
        file_path=file_path,
        title="Course Syllabus",
        document_type="syllabus",
        subject=subject,
        semester=semester,
    )

    if not doc_res["success"]:
        return doc_res

    extract_res = extract_syllabus(
        pdf_path=file_path,
        document_id=doc_res["document_id"],
        subject=subject,
        semester=semester,
        academic_year=academic_year,
        version=doc_res.get("version", 1),
    )

    return extract_res


def get_syllabus_diff(
    subject: str,
    semester: int,
    v1: int,
    v2: int,
) -> dict:
    """Quick set-based diff from DB — no embeddings needed."""
    return compare_syllabi(subject=subject, semester=semester, v1=v1, v2=v2)


def get_rich_syllabus_diff(
    old_json_path: str,
    new_json_path: str,
) -> dict:
    """
    Full 3-pass embedding-based diff from saved JSON files.
    Call this after upload_and_process_syllabus() saves the JSON.
    """
    old = load_syllabus_json(old_json_path)
    new = load_syllabus_json(new_json_path)
    return compare_syllabi_json(old, new)


def tag_document(
    document_id: str,
    subject: str,
    semester: int,
) -> dict:
    """Tag a document's chunks with syllabus topics. Admin only."""
    require_admin()
    tagged = tag_document_chunks(
        document_id=document_id,
        subject=subject,
        semester=semester,
    )
    return {
        "success":      True,
        "message":      f"Successfully tagged {tagged} chunks with syllabus topics.",
        "tagged_count": tagged,
    }


def apply_diff_to_qdrant(
    diff: dict,
    subject: str,
    semester: int,
) -> dict:
    """Apply a rich diff result to Qdrant — marks stale, confirms current."""
    require_admin()
    return apply_syllabus_diff(diff=diff, subject=subject, semester=semester)
