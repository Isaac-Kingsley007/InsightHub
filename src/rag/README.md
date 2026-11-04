# Document ingestion and answers

Upload policies so the assistant can answer questions using their text and cite
supporting chunks. Complete [database and Gemini setup](../../README.md) first.
All commands below run from the project root with the venv active.

## Add a document

Use **Knowledge base** in the web app, or run:

```powershell
python -m src.rag.ingest --file "path/to/policy.pdf"
```

For extraction/chunking preview without API or database access:

```powershell
python -m src.rag.prepare --file "path/to/policy.pdf"
```

Supports unlocked, text-based PDFs and UTF-8 `.txt` files. Scans need OCR first.
PDF page numbers are preserved; empty pages are skipped. Recursive splitting uses
paragraphs, newlines, spaces, then characters. Defaults: 1,000 characters and a
200-character target overlap, within each page. Override with `--chunk-size` and
`--chunk-overlap`; actual overlap depends on split boundaries.

The web endpoint `POST /ingest` accepts multipart field `file` (up to 10 MB).
Original uploads are deleted after processing; chunk text and metadata remain.
`GET /documents` lists stored documents. Keep the upload page open until confirmation;
for long jobs, prefer the CLI over a web request with a proxy timeout.

## Ask a question

Send `POST /ask` through the API docs:

```json
{"question": "How many days do I have to request a refund?"}
```

Returns `answer` and `source_chunks`. Citation IDs are the stored UUIDs.
Useful partial answers are allowed; missing evidence must be stated. If no chunks
qualify, the API returns `I don't have enough information` with an empty citation
list without generating an answer. The model can also decline after reading chunks.

## Settings and rate limits

| Root `.env` setting | Default | Meaning |
| --- | --- | --- |
| `RAG_TOP_K` | `5` | Maximum retrieved candidates; allowed 1-20 |
| `RAG_MIN_SIMILARITY` | `0.5` | Minimum cosine similarity; allowed -1 to 1 |
| `EMBEDDING_BATCH_SIZE` | `20` | Chunks per ingestion call; allowed 1-100 |
| `EMBEDDING_CHUNKS_PER_MINUTE` | `60` | Positive ingestion pacing budget |

The similarity threshold is a starting point, not answer confidence. Compare known
policy questions and unrelated questions before tuning it. Lowering it admits
more context but can introduce unrelated text.

Ingestion batches are paced by chunk count: at the defaults a 20-chunk batch
reserves 20 seconds before the next request, including API time. Temporary 429s
retry the same batch up to five times, using Google's retry delay plus 20 seconds,
backoff and jitter. Reported minute quotas can reduce the pace; explicit daily/zero
quotas stop immediately. Other clients share project quota, so pacing one run
cannot guarantee no 429s. Query embeddings and text generation do not use these
long ingestion retries.

## Maintenance and debugging

- `documents.py` / `chunking.py`: extraction and source metadata.
- `embeddings.py`: fixed `gemini-embedding-001`, 768 dimensions, L2 normalization;
  document task `RETRIEVAL_DOCUMENT`, query task `RETRIEVAL_QUERY`.
- `ingest.py`: check file hash, embed, then store document/chunks in one transaction.
  Exact duplicate files skip API calls even under another name. Changed contents
  create a separate document; changing chunk settings alone does not reingest it.
  Old policy versions are not automatically replaced or excluded from search.
- Completed embeddings survive retries in memory, not process exits. No partial
  document is saved on failure; concurrent ingestions may still duplicate API work.
- `retrieval.py`: exact cosine search (`1 - distance`) for the matching model.
  `ask.py`: prompt, JSON validation, allowed citation IDs, and one output retry.
  Valid citation IDs do not prove an answer is factually supported; review evidence.
- If embeddings change model/dimensions, regenerate stored vectors and update
  query embedding and database schema together. `GEMINI_MODEL` is generation only.
- Missing answers: check document count, inspect source text, review scores and
  policy versions. Invalid output/provider errors return 502; unavailable DB,
  configuration or quota returns 503; Gemini timeout returns 504.

Offline checks:

```powershell
python -m unittest src.rag.test_ingest src.rag.test_rate_limits src.rag.test_retrieval src.api.test_documents
```
