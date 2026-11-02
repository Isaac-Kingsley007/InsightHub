# InsightHub MCP server

Uses the installed MCP 2.x SDK (`MCPServer`) and the existing RAG and customer
query services. The same tool descriptions are shared with the LangChain agent.
Known tool failures are reported with MCP's error flag, not as successful data.

Run from the project root with the existing venv activated:

```powershell
python -m src.mcp.server
```

Connect an MCP client using Streamable HTTP at `http://127.0.0.1:8001/mcp`.
FastAPI can continue using port 8000. The server uses root `.env` configuration
through the existing services. Customer import/reader-role setup and policy
ingestion must already be complete. This is a local, unauthenticated server.

Available tools: `search_documents(query)` and `run_safe_query(sql)`.

Offline checks:

```powershell
python -m unittest src.mcp.test_server
```
