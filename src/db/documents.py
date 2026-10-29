"""Duplicate detection and atomic document/chunk storage."""

from .connection import connect_db
from src.rag.embeddings import EMBEDDING_MODEL, validate_vectors


def find_document(file_hash):
    with connect_db() as connection:
        return connection.execute(
            "SELECT id, (SELECT count(*) FROM document_chunks WHERE document_id = documents.id) "
            "FROM documents WHERE file_hash = %s", (file_hash,),
        ).fetchone()


def save_document(document_id, document, chunks, vectors):
    """Commit all rows together; return (document ID, chunk count, created).

    The unique file hash also handles concurrent ingestions of the same file.
    """
    if not chunks:
        raise ValueError("Cannot store a document without chunks.")
    vectors = validate_vectors(vectors, len(chunks))
    if any(chunk.document_id != document_id for chunk in chunks):
        raise ValueError("Chunk document IDs do not match the document being saved.")
    with connect_db() as connection:
        inserted = connection.execute(
            "INSERT INTO documents (id, filename, file_hash, embedding_model) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (file_hash) DO NOTHING RETURNING id",
            (document_id, document.filename, document.file_hash, EMBEDDING_MODEL),
        ).fetchone()
        if not inserted:
            existing = connection.execute(
                "SELECT id, (SELECT count(*) FROM document_chunks WHERE document_id = documents.id) "
                "FROM documents WHERE file_hash = %s", (document.file_hash,),
            ).fetchone()
            return str(existing[0]), existing[1], False
        with connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO document_chunks "
                "(id, document_id, chunk_index, page_number, content, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [(chunk.id, document_id, chunk.chunk_index, chunk.page_number, chunk.content, vector)
                 for chunk, vector in zip(chunks, vectors)],
            )
    return document_id, len(chunks), True
