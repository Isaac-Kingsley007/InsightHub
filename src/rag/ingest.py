"""Ingest a document: python -m src.rag.ingest --file refund_policy.pdf."""

import argparse
from uuid import uuid4

import psycopg
from pypdf.errors import PdfReadError

from src.db.documents import find_document, save_document
from .chunking import chunk_document
from .documents import read_document
from .embeddings import embed_documents


def ingest_document(path, chunk_size=1000, chunk_overlap=200):
    document = read_document(path)
    existing = find_document(document.file_hash)
    if existing:
        return str(existing[0]), existing[1], False
    document_id = str(uuid4())
    chunks = chunk_document(document, document_id, chunk_size, chunk_overlap)
    vectors = embed_documents([chunk.content for chunk in chunks], document.filename)
    return save_document(document_id, document, chunks, vectors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    args = parser.parse_args()
    try:
        _, count, created = ingest_document(args.file, args.chunk_size, args.chunk_overlap)
    except psycopg.Error:
        parser.exit(1, "Ingestion failed: database operation failed. Check DATABASE_URL, network access, "
                    "and run python -m src.db.setup first.\n")
    except (OSError, ValueError, RuntimeError, PdfReadError) as exc:
        parser.exit(1, f"Ingestion failed: {exc}\n")
    from pathlib import Path
    filename = Path(args.file).name
    if created:
        print(f"Ingested {filename}: {count} chunks -> stored in pgvector.")
    else:
        print(f"Skipped {filename}: already ingested ({count} chunks stored in pgvector).")


if __name__ == "__main__":
    main()
