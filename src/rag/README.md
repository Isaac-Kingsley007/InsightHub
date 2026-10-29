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

Document preview does not need a database or Gemini key.

## Full ingestion into Neon

1. Activate the existing environment from the project root:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. In the root `.env`, set `DATABASE_URL` to your Neon PostgreSQL connection
   string (keep its SSL parameters, such as `sslmode=require`) and set
   `GEMINI_API_KEY`. Do not commit this file. The existing `GEMINI_MODEL` setting
   controls text generation only; ingestion uses `gemini-embedding-001` explicitly.

3. Initialize the schema (safe to rerun):

   ```powershell
   python -m src.db.setup
   ```

   Neon already provides the database, so do not pass `--create-database`.
   Setup enables pgvector and creates the tables; no Docker is required.

4. Ingest your policy document:

   ```powershell
   python -m src.rag.ingest --file "path/to/refund_policy.pdf"
   ```

   Example output, with the actual chunk count:

   ```text
   Ingested refund_policy.pdf: 42 chunks -> stored in pgvector.
   ```

5. Optionally inspect the result in Neon's SQL editor:

   ```sql
   SELECT d.id, d.filename, d.embedding_model, count(c.id) AS chunks
   FROM documents d
   LEFT JOIN document_chunks c ON c.document_id = d.id
   GROUP BY d.id;
   ```

The pipeline checks the SHA-256 file hash before embedding. Repeating the same
file skips ingestion, even under a different filename. Changed file contents are
a separate document; existing versions are not automatically replaced. Changing
chunk settings alone does not reprocess an already-ingested file.

Chunks are embedded in batches of up to 20 with `gemini-embedding-001`, task type
`RETRIEVAL_DOCUMENT`, and 768 dimensions, then L2-normalized. Invalid counts,
dimensions, nonfinite values, and zero vectors are rejected. Document and chunk
rows commit together; a failed insert rolls back the entire document. Embedding
failures happen before storage, so retrying the command is safe. Concurrent
ingestions may both call Gemini, but the database permits only one stored copy.

If Gemini reports a quota limit, wait for quota to recover or check the Google
project's embedding access. If database operations fail, verify the Neon URL,
network access, and schema setup. Empty/scanned PDFs require OCR separately.

Tests: `python -m unittest src.rag.test_ingest`. Retrieval and API upload endpoints
will be added later. The eventual query embedder must use the same model and
dimensions with task type `RETRIEVAL_QUERY`.
