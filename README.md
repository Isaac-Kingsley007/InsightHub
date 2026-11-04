# InsightHub

InsightHub helps a Customer Success team understand its customers and company
policies. Ask questions in plain language, upload reference documents, and estimate
which customers may leave. Answers use your stored customer data and documents;
predictions come from a trained machine-learning model.

## What you can do

- **Assistant:** ask customer and policy questions, with follow-up conversations.
- **Knowledge base:** upload PDF/TXT documents and see which are ready for search.
- **Churn predictions:** enter account activity to get a churn probability.
- **Text analysis:** use the API to get sentiment, topics, and a short summary.

## Setup from scratch

Commands below use Windows PowerShell from the repository root, unless stated
otherwise. Use Python **3.12**, Node.js **22+**, and **pnpm 12.16.1**. You also need
a Neon PostgreSQL database and a Gemini API key with model access and quota.
Docker is not needed for the current Neon setup.

### 1. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm install -g pnpm@12.16.1
pnpm --dir web install --frozen-lockfile
```

Skip creating `.venv` if it already exists. On macOS/Linux, activate it with
`source .venv/bin/activate`. Python package versions in `requirements.txt` match the
current development environment; frontend versions are in `web/pnpm-lock.yaml`.

### 2. Add configuration and data

```powershell
Copy-Item .env.example .env
```

If `.env` already exists, edit it instead of overwriting it. Set:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Your Neon connection string; keep its SSL parameters |
| `GEMINI_API_KEY` | Your Gemini API key |
| `GEMINI_MODEL` | A Gemini model available to your project with tool calling and structured output |

The example model is a default, not a guarantee of free-tier access. Keep only the
intended Google API key configured. Existing environment variables override `.env`.
Never commit credentials or put them in frontend `NEXT_PUBLIC_*` variables.

Place the provided datasets here; datasets are excluded from Git:

```text
datasets/customer_churn/train.csv
datasets/customer_churn/test_.csv
```

Both CSVs need these columns:
`Customer_ID, Name, Email, Account_Age_Days, Login_Frequency, Daily_Usage_Mins, Last_Support_Ticket, Churn`.
`Churn` must be 0 or 1. See [data validation](src/data_tool/README.md).

### 3. Prepare the database and model

Use a Neon owner connection with table creation/write and role-management
permissions. The reader setup requires PostgreSQL 16+.

```powershell
python -m src.db.setup
python -m src.data_tool.import_customers
python -m src.data_tool.setup_reader
python -m src.ml.train
```

This creates the tables, imports **train.csv only**, grants a restricted customer
reader role, and saves the churn pipeline. Reimporting updates matching customer
IDs; schema setup creates missing tables but does not migrate existing ones.
Training overwrites its generated model and reports.

### 4. Start the app

Terminal 1, from the root with the venv activated:

```powershell
python -m uvicorn src.api.main:app --reload
```

Terminal 2:

```powershell
cd web
pnpm dev
```

Open **http://localhost:3000**. Upload a policy under **Knowledge base**, wait for
confirmation, then ask the Assistant about it. For a large file, ingest from the
root terminal instead:

```powershell
python -m src.rag.ingest --file "path/to/policy.pdf"
```

Use text-based PDFs or UTF-8 text files. Web uploads are limited to 10 MB and may
take several minutes because of embedding pacing and retries.

## API and optional MCP server

Interactive API docs: **http://127.0.0.1:8000/docs**.

| Endpoint | Purpose |
| --- | --- |
| `POST /agent` | Agent answer and tools used |
| `POST /ask` | Document answer and supporting chunk IDs |
| `POST /analyze` | Sentiment, topics, and summary |
| `POST /predict-churn` | Churn label and probability |
| `POST /ingest` | PDF/TXT upload; multipart field `file` |
| `GET /documents` | Stored document metadata |

For MCP clients, run `python -m src.mcp.server` in another activated terminal.
Connect using Streamable HTTP at **http://127.0.0.1:8001/mcp**.

## Maintenance and troubleshooting

| Problem | What to check |
| --- | --- |
| Frontend cannot reach API | Start FastAPI on port 8000. For another address, set `API_BASE_URL` in `web/.env.local` and restart/rebuild Next.js. |
| Missing tables or SQL tool permission error | Check the Neon URL and rerun schema/reader setup with the owner connection. |
| Churn model unavailable | Run `python -m src.ml.train`, then restart the API. |
| Gemini quota error | Check the active project's quota. Ingestion retries temporary limits; reduce `EMBEDDING_CHUNKS_PER_MINUTE` if needed. Daily/zero quotas need quota recovery or account changes. |
| Policy answer missing | Confirm ingestion finished. Check relevant chunks and tune `RAG_TOP_K`/`RAG_MIN_SIMILARITY`; similarity is not answer confidence. |
| Empty/scanned PDF | Extract text with OCR first; this app does not perform OCR. |

Run backend checks after training: `python -m unittest discover -s src -t .`.
Tests use mocks for Gemini/Neon; prediction API tests load the local model.
Frontend build and browser-test instructions are in [web/README.md](web/README.md).

This is a local capstone app without sign-in. Agent memory resets on API restart;
use one API worker. Predictions are estimates, and the customer dataset has no
churn date or spending fields. Docker/deployment files and Part B's PyTorch
sentiment model are not implemented in this checkout.

## Code guide

| Area | Details |
| --- | --- |
| `web/`, `src/api/` | [Frontend and API connection](web/README.md) |
| `src/ml/` | [Training, predictions, and reports](src/ml/README.md) |
| `src/llm/` | [Text analysis](src/llm/README.md) |
| `src/rag/` | [Document ingestion, retrieval, and rate limits](src/rag/README.md) |
| `src/db/`, `src/data_tool/` | [Database setup](src/db/README.md) and [customer queries](src/data_tool/README.md) |
| `src/agent/`, `src/mcp/` | [Agent memory/tools](src/agent/README.md) and [MCP server](src/mcp/README.md) |
