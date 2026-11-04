# InsightHub web app

A Next.js App Router frontend styled with Tailwind CSS. Three pages share a sidebar
and client-side navigation:

| Page | Purpose |
| --- | --- |
| `/chat` | Agent conversation, follow-ups and source-tool badges |
| `/documents` | PDF/TXT uploads and the stored document library |
| `/predictions` | Churn probability, label and five recent predictions |

## Run

Complete [root setup](../README.md) and start FastAPI on port 8000. In this folder:

```powershell
pnpm install --frozen-lockfile
pnpm dev
```

Open **http://localhost:3000**. Browser `/api/*` requests are proxied to FastAPI.
To change the backend address, set `API_BASE_URL` in `web/.env.local` using
[.env.example](.env.example), then restart Next.js. Rebuild for production changes.
Gemini and Neon credentials belong only in root `.env`, never browser variables.

## Behavior and maintenance

- Chat and prediction history are page-local; they reset on a fresh page session.
  Follow-ups reuse the chat session ID; New conversation starts another.
  Backend agent memory also resets when FastAPI restarts.
- Uploads use multipart `POST /ingest`, field `file`, with a 10 MB limit.
  `GET /documents` lists metadata. Original uploads are deleted after processing.
- Keep the upload page open until confirmation. Pacing/retries can take minutes;
  the Next.js proxy timeout is 30 minutes, but hosting may impose a shorter one.
  Prefer the ingestion CLI for large jobs. Do not submit the same file concurrently.
- UI errors: check FastAPI `/docs` first. A missing model needs training; a missing
  library needs DB setup; quota errors need Gemini quota recovery or slower pacing.
- This app has no sign-in. Keep deployments private until access control exists.

Build and run the production frontend with `pnpm build`, then `pnpm start`.
The Python API must still run separately.

## Browser checks

With both services running, execute from `web/`:

```powershell
$env:TEST_BASE_URL="http://127.0.0.1:3000"
pnpm exec playwright test --reporter=line
```

Tests use installed Microsoft Edge by default. For installed Chrome, set
`$env:PLAYWRIGHT_CHANNEL="chrome"`. Chat/upload responses are mocked; the churn
check calls the real local model API. No Gemini quota is consumed. Without
`TEST_BASE_URL`, the test configuration targets port 3001.
