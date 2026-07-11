"""Syllabus service."""

from services.auth_service import require_teacher
from syllabus.extractor import extract_syllabus
from syllabus.comparator import compare_syllabi
from syllabus.tagger import tag_document_chunks


def upload_and_process_syllabus(
    file_path: str,
    subject: str,
    semester: int,
) -> dict:
    """
    Process an uploaded syllabus document:
    1. Upload to storage & Database as a document.
    2. Extract units/topics and save to syllabus_topics.
    """
    from services.document_service import upload_document
    
    # Upload syllabus document
    doc_res = upload_document(
        file_path=file_path,
        title="Course Syllabus",
        document_type="syllabus",
        subject=subject,
        semester=semester,
    )
    
    if not doc_res["success"]:
        return doc_res
        
    doc_id = doc_res["document_id"]
    
    # Extract syllabus units/topics
    extract_res = extract_syllabus(
        pdf_path=file_path,
        document_id=doc_id,
        subject=subject,
        semester=semester,
        version=doc_res.get("version", 1)
    )
    
    return extract_res


def get_syllabus_diff(
    subject: str,
    semester: int,
    v1: int,
    v2: int,
) -> dict:
    """
    Compare two versions of a syllabus.
    """
    return compare_syllabi(subject=subject, semester=semester, v1=v1, v2=v2)


def tag_document(
    document_id: str,
    subject: str,
    semester: int,
    # Tagging only triggered by teacher
) -> dict:
    """
    Tag a document's chunks with syllabus topics.
    """
    require_teacher()
    tagged = tag_document_chunks(
        document_id=document_id,
        subject=subject,
        semester=semester
    )
    return {
        "success": True,
        "message": f"Successfully tagged {tagged} chunks with syllabus topics.",
        "tagged_count": tagged,
    }
