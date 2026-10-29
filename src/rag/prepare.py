"""Preview extracted chunks: python -m src.rag.prepare --file policy.pdf."""

import argparse

from .chunking import prepare_document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    args = parser.parse_args()
    document_id, document, chunks = prepare_document(args.file, args.chunk_size, args.chunk_overlap)
    print(f"Document: {document.filename}")
    print(f"Document ID: {document_id}")
    print(f"SHA-256: {document.file_hash}")
    print(f"Prepared {len(chunks)} chunks; no embeddings generated or database writes performed.")
    for chunk in chunks:
        source = f"page {chunk.page_number}" if chunk.page_number else "text file"
        print(f"\nChunk {chunk.chunk_index} ({source}, {len(chunk.content)} characters)")
        print(chunk.content)


if __name__ == "__main__":
    main()
