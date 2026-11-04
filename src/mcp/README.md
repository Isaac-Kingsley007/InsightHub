# MCP server

Lets an MCP-compatible client reuse InsightHub's document search and customer
query tools. It calls the same services as the agent, with the same tool descriptions.
Complete [root setup](../../README.md) before using either tool.

## Run and connect

From the repository root with the venv activated:

```powershell
python -m src.mcp.server
```

Connect using **Streamable HTTP** at **http://127.0.0.1:8001/mcp**.
FastAPI uses port 8000 separately; the MCP server does not require FastAPI to run.

| Tool | Input | Result |
| --- | --- | --- |
| `search_documents` | `query`: natural-language question | Document answer and citation IDs |
| `run_safe_query` | `sql`: one supported customer SELECT | Columns, rows, count and truncation flag |

## Maintenance and debugging

Uses MCP **2.x** (`MCPServer`); older FastMCP 1.x examples are not drop-in replacements.
Known service failures become MCP tool errors. Check root `.env`, Gemini quota,
document ingestion, and customer reader-role setup when tools fail.

The server binds to loopback and has no authentication. Keep it local unless
proper access control is added. If a client cannot connect, check transport,
port 8001 and the `/mcp` path; it is not a normal REST chat endpoint.

Offline protocol checks: `python -m unittest src.mcp.test_server`.
