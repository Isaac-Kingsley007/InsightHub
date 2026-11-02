# Customer Success agent

Uses LangChain with Gemini and the two existing tools. Run the API from the
project root: `python -m uvicorn src.api.main:app --reload`.

In `/docs`, send `POST /agent`:

```json
{"query": "How many customers churned, and what does our refund policy say?", "session_id": "demo-1"}
```

Returns `answer` and `tools_used` for the current turn. Reuse a session ID for
follow-up questions. Different conversations must have different IDs. Omitting
the ID starts an isolated one-off request. IDs are caller supplied, so use unique
IDs per user/conversation; there is no authentication layer yet.

Memory lives in one API process and resets when it restarts. Use one worker for
this capstone version. The model is initialized once on first use; restart after
changing Gemini configuration. Existing database, reader-role and policy
ingestion setup must be complete for the tools to work.

Known tool errors are returned to the model so it can correct SQL or explain a
failure. Provider failures or excessive agent steps produce a clean API error.
Offline checks: `python -m unittest src.agent.test_agent`.

This agent does not implement the separate MCP server required by Part E.
