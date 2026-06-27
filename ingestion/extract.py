import fitz

def extract(pdf_path: str) -> list[dict]:
    """ extracting from the pdf using fitz and paging them"""
    doc = fitz.open(pdf_path)  # PyMuPDF
    pages= [] 

    for page_num, page in enumerate(doc , start=1):
        text = page.get_text()
        if text.strip(): 
            pages.append({
                "page_number":page_num,
                "text": text
            })

    doc.close()
    return pages

