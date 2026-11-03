# InsightHub

Customer Success workspace combining churn prediction, document-grounded answers,
and a Gemini agent that can query customer data and company policies.

## Run locally

Use the existing Python `.venv` with the project dependencies installed. Backend
configuration lives in root `.env` (see `.env.example`): Gemini API key/model,
Neon `DATABASE_URL`, retrieval and embedding settings. Keep credentials private.

From the repository root, initialize only the pieces you have not already set up:

```powershell
.\.venv\Scripts\Activate.ps1
python -m src.db.setup
python -m src.data_tool.import_customers
python -m src.data_tool.setup_reader
python -m src.ml.train
```

Start FastAPI:

```powershell
python -m uvicorn src.api.main:app --reload
```

In a second terminal, start the Next.js frontend:

```powershell
cd web
pnpm install
pnpm dev
```

Open http://localhost:3000. API documentation: http://127.0.0.1:8000/docs.
The frontend proxies `/api/*` to FastAPI, keeping credentials server-side and
avoiding cross-origin browser configuration. Optional `web/.env.local` can set
`API_BASE_URL`; it defaults to `http://127.0.0.1:8000`.

## Architecture

- `web/`: Next.js App Router frontend; Assistant, Knowledge base, Churn predictions.
- `src/api/`: one FastAPI app: `/agent`, `/ask`, `/analyze`, `/predict-churn`,
  `/ingest` (multipart document upload), and `/documents` (metadata listing).
- `src/agent/`: LangChain + Gemini, short-term memory and tool routing.
- `src/rag/`: PDF/TXT preparation, paced Gemini embeddings, Neon pgvector retrieval
  and cited JSON answers. Uploads reuse the same ingestion service as the CLI.
- `src/data_tool/`: CSV import and restricted, SELECT-only customer analytics.
- `src/ml/`: classical training and saved churn pipeline.
- `src/mcp/`: the same tools exposed using MCP on port 8001.

Neon PostgreSQL stores customer rows, documents and vector chunks. No local
Docker is needed for this setup. Gemini calls need available project quota.

See `web/README.md` for UI behavior and upload limits; the individual
Python service directories document their detailed setup and tests.
