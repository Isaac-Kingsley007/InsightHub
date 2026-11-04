# Database

PostgreSQL stores customer records, document metadata, and searchable document
chunks. The app uses Neon; a local PostgreSQL server with pgvector also works.
Complete the [root setup](../../README.md) first. Run commands from the root.

## Initialize

```powershell
python -m src.db.setup
```

Uses root `.env` variable `DATABASE_URL`. Enables pgvector and creates:

| Table | Stores |
| --- | --- |
| `customers` | Customer CSV records; UUID primary key |
| `documents` | Filename, unique SHA-256 file hash, embedding model, timestamp |
| `document_chunks` | Chunk text, UUID, document ID, order, PDF page, `VECTOR(768)` |

Setup preserves existing rows and only creates missing tables. It does **not**
change existing table definitions; write an explicit migration for schema changes.
For a local server only, `python -m src.db.setup --create-database` can create the
database named in the URL via the server's `postgres` database (requires CREATEDB).
Do not use that option for an already-provisioned Neon database.

## Developer notes

- `connection.py`: `with connect_db() as connection:` registers vector types,
  commits on success, rolls back on failure, and closes the connection.
- `documents.py`: duplicate lookup and atomic document/chunk inserts. Duplicate
  hashes are skipped; deleting a document cascades to its chunks.
- The SQL tool uses a separate connection to set READ ONLY before any data query.
  [Customer import and reader-role setup](../data_tool/README.md) live separately.
- Keep SSL options in the Neon URL. On connection errors check configuration,
  network access, database availability, and grants. Do not log the connection URL.
