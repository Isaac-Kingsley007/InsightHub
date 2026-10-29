"""Split each page independently into overlapping character chunks."""

from dataclasses import dataclass
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .documents import Document, read_document


@dataclass
class Chunk:
    id: str
    document_id: str
    chunk_index: int
    page_number: int | None
    content: str


def chunk_document(document: Document, document_id: str, chunk_size=1000, chunk_overlap=200):
    if chunk_size <= 0 or not 0 <= chunk_overlap < chunk_size:
        raise ValueError("Require chunk_size > 0 and 0 <= chunk_overlap < chunk_size.")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""], length_function=len,
    )
    chunks = []
    for page in document.pages:
        for text in splitter.split_text(page.text):
            if text.strip():
                chunks.append(Chunk(str(uuid4()), document_id, len(chunks), page.page_number, text))
    return chunks


def prepare_document(path, chunk_size=1000, chunk_overlap=200):
    """Return document ID, source document, and chunks without embedding or storing."""
    document = read_document(path)
    document_id = str(uuid4())
    chunks = chunk_document(document, document_id, chunk_size, chunk_overlap)
    return document_id, document, chunks
