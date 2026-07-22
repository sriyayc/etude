import fitz


# NUL and the other C0 control chars (except tab/newline/CR) cannot live in a
# Postgres text/jsonb column. PyMuPDF sometimes emits NUL when extracting from
# certain PDFs, and writing the slides then failed with a 22P05 error,
# aborting the whole upload. These characters carry no meaning here, so strip
# them at the source, before either the DB slides or the embeddings see them.
_CONTROL_CHAR_MAP = {
    c: None for c in range(0x20) if c not in (0x09, 0x0A, 0x0D)
}


def _sanitize(text: str) -> str:
    if not text:
        return text
    return text.translate(_CONTROL_CHAR_MAP)


def extract_pages(pdf_path: str) -> list[dict]:
    """ extracting from the pdf using fitz and paging them"""
    doc = fitz.open(pdf_path)  # PyMuPDF
    pages = []

    for page_num, page in enumerate(doc, start=1):
        text = _sanitize(page.get_text())
        if text.strip():
            pages.append({
                "page_number": page_num,
                "text": text
            })

    doc.close()
    return pages
