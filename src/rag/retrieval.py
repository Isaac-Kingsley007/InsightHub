"""Exact cosine retrieval over the stored Gemini document vectors."""

from src.db.connection import connect_db
from .embeddings import EMBEDDING_MODEL


def retrieve_chunks(vector, k, min_similarity):
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT c.id, c.content, d.filename, c.page_number, "
            "1 - (c.embedding <=> %s) AS similarity "
            "FROM document_chunks c JOIN documents d ON d.id = c.document_id "
            "WHERE d.embedding_model = %s "
            "ORDER BY c.embedding <=> %s, c.id LIMIT %s",
            (vector, EMBEDDING_MODEL, vector, k),
        ).fetchall()
    return [{"id": str(row[0]), "content": row[1], "filename": row[2],
             "page_number": row[3], "similarity": float(row[4])}
            for row in rows if row[4] is not None and row[4] >= min_similarity]
