"""Read text-based PDFs or UTF-8 text files, preserving PDF page numbers."""

import hashlib
from io import BytesIO
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class DocumentPage:
    text: str
    page_number: int | None


@dataclass
class Document:
    filename: str
    file_hash: str
    pages: list[DocumentPage]


def clean_text(text):
    # Preserve paragraph boundaries for recursive splitting.
    return text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").strip()


def read_document(path: str | Path) -> Document:
    path = Path(path)
    if path.suffix.lower() not in {".pdf", ".txt"}:
        raise ValueError("Supported document types are .pdf and .txt.")
    content = path.read_bytes()
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported. Provide an unlocked copy.")
        pages = [DocumentPage(clean_text(page.extract_text() or ""), number)
                 for number, page in enumerate(reader.pages, start=1)]
    else:
        pages = [DocumentPage(clean_text(content.decode("utf-8-sig")), None)]
    pages = [page for page in pages if page.text]
    if not pages:
        raise ValueError("No extractable text found. Scanned PDFs need OCR before ingestion.")
    return Document(path.name, hashlib.sha256(content).hexdigest(), pages)
