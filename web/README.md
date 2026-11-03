# InsightHub frontend

Next.js App Router + React + Tailwind CSS. Three pages share a persistent navigation
layout, using Next.js Links for client-side navigation:

- `/chat`: agent chat, conversation session IDs, tool-source badges and new chat.
- `/documents`: PDF/TXT upload (10 MB limit), real document library and duplicate feedback.
- `/predictions`: model-backed churn probability and the last five predictions on the page.

Start the Python API from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api.main:app --reload
```

In a second terminal:

```powershell
cd web
pnpm install
pnpm dev
```

Open http://localhost:3000. Requests to `/api/*` are proxied to FastAPI at
`http://127.0.0.1:8000`. To change this, set `API_BASE_URL` in `web/.env.local`, then
restart Next.js. Backend Gemini/Neon secrets stay in the root `.env`.

The upload form calls `POST /ingest` with multipart field `file`. The backend
validates the file, temporarily saves it, calls the existing RAG ingestion service,
and removes the temporary upload. `GET /documents` lists stored metadata. Uploaded
originals are not retained. No mock statistics or successful results are displayed.

Uploads run synchronously: keep the page open until confirmation. API pacing and
429 retries can take several minutes. The local Next.js proxy timeout is 30
minutes; hosted services may impose shorter limits. For larger jobs, use the
existing ingestion CLI. Avoid submitting the same file concurrently.

Chat and prediction history are page-local and reset on navigation/reload. Agent
follow-ups reuse the same session while on the chat page; New conversation resets
it. The backend's agent memory is process-local. This capstone UI has no sign-in.

Prerequisites: installed Python dependencies including `python-multipart`, working
Neon schema, the trained `src/ml/artifacts/churn_model.pkl`, and Gemini credentials.
See the root README and the service READMEs for setup.

Production check: `pnpm build`. Production run: `pnpm start`.

## Browser checks

Playwright uses the installed Microsoft Edge browser by default (no browser download).
With the API and frontend running, point tests at your frontend URL:

```powershell
$env:TEST_BASE_URL="http://127.0.0.1:3000"
pnpm exec playwright test --reporter=line
```

Set `PLAYWRIGHT_CHANNEL=chrome` to use installed Google Chrome instead. Chat and
upload browser tests use mocked service responses; the churn test calls the real
local model API. Backend upload tests cover validation, temporary-file cleanup,
duplicates and quota failures without consuming Gemini quota.
