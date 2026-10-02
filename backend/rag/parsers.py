import pypdf
import pymupdf
import docx
import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

def parse_pdf(file_path: str) -> List[Tuple[int, str]]:
    """
    Parses PDF and returns a list of tuples containing (page_number_1_indexed, text).
    """
    logger.info(f"Parsing PDF file: {file_path}")
    try:
        reader = pypdf.PdfReader(file_path)
        pages_data = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_data.append((i + 1, text))
        return pages_data
    except Exception as e:
        logger.warning(
            "pypdf could not extract %s (%s); retrying with PyMuPDF",
            file_path,
            e,
        )

    try:
        with pymupdf.open(file_path) as document:
            return [
                (page_number, page.get_text("text") or "")
                for page_number, page in enumerate(document, start=1)
            ]
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path} with both PDF parsers: {e}")
        raise e

def parse_docx(file_path: str) -> List[Tuple[int, str]]:
    """
    Parses DOCX and returns a single page list containing (0, text).
    """
    logger.info(f"Parsing DOCX file: {file_path}")
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text:
                full_text.append(para.text)
        text = "\n".join(full_text)
        return [(0, text)]
    except Exception as e:
        logger.error(f"Error parsing DOCX {file_path}: {e}")
        raise e

def parse_text(file_path: str) -> List[Tuple[int, str]]:
    """
    Parses plain text / MD and returns a single page list containing (0, text).
    """
    logger.info(f"Parsing Text/MD file: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return [(0, text)]
    except Exception as e:
        logger.error(f"Error parsing text file {file_path}: {e}")
        raise e

def parse_document(file_path: str, mime_type: str | None = None) -> Tuple[List[Tuple[int, str]], int]:
    """
    Parses document based on type and returns (pages_data, total_pages).
    """
    ext = os.path.splitext(file_path)[1].lower()
    mime = (mime_type or "").lower()
    
    if ext == ".pdf" or "pdf" in mime:
        pages = parse_pdf(file_path)
        return pages, len(pages)
    elif ext == ".docx" or "officedocument" in mime:
        pages = parse_docx(file_path)
        return pages, 1
    elif ext in [".txt", ".md", ".json"] or "text" in mime:
        pages = parse_text(file_path)
        return pages, 1
    else:
        # Fallback to text parsing
        pages = parse_text(file_path)
        return pages, 1
