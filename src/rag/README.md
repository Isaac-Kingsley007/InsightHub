# Document preparation

Packages: `pypdf` and `langchain-text-splitters`.
From the project root in your venv:

```powershell
python -m src.rag.prepare --file InsightHub_Project_Question.pdf
```

PDFs are read page by page; `.txt` files must be UTF-8. Empty pages are skipped
without renumbering the original pages. Scanned PDFs require OCR separately.
Encrypted PDFs and files without extractable text are rejected.

`prepare_document(path)` returns a new document UUID, a document object containing
filename, content hash and extracted pages, and a list of chunks. Every chunk has
a UUID, document ID, zero-based document-wide index, content, and a one-based PDF
page number (or `None` for text files).

Recursive character splitting uses paragraphs, newlines, spaces, then characters.
Defaults are 1,000 characters with a target overlap of 200; actual overlap depends
on split boundaries. Chunks never cross page boundaries. Override the settings
with `--chunk-size` and `--chunk-overlap`. The CLI previews all chunk text.

This step does not need a database or Gemini key. Embedding generation, storage,
duplicate lookup, retrieval, and API endpoints are intentionally left for later.
