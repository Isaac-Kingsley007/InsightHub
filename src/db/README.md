# Database setup

Packages: `psycopg[binary]`, `pgvector`, and `python-dotenv`.
Set `DATABASE_URL` in the project root `.env`. A PostgreSQL server with pgvector
available is required to run setup; Docker is optional.

From the project root in your venv:

```powershell
python -m src.db.setup
```

This enables the vector extension and creates `documents` and `document_chunks`
inside the database specified in the URL. Tables are created only if absent;
this script does not migrate existing table definitions. For a local server whose
database does not exist yet, use `python -m src.db.setup --create-database`.
That option connects to the server's `postgres` database and requires CREATEDB
privileges. For Neon or another provisioned database, use the regular command.

Use `with connect_db() as connection:` from `src.db.connection` for future SQL
operations. The context commits on success, rolls back on error, and closes the
connection. Vector types are registered automatically. Run setup before connecting
this way, and do not print the connection URL because it contains credentials.

The schema follows the agreed two-table design: UUID document/chunk IDs, source
filename and SHA-256 hash, embedding model, page number, chunk order/text, and
`VECTOR(768)`. A unique file hash prevents duplicate document records; embeddings
and inserts will be implemented later. Exact cosine search can be added without
an approximate index for the small initial dataset.
