# Customer Success agent

Answers plain-language customer and policy questions using Gemini with LangChain.
It chooses customer SQL, document search, or both, and remembers follow-ups within
a conversation. Complete the [root setup](../../README.md) before using tools.

## Use

Start FastAPI and open the web Assistant, or send `POST /agent` in `/docs`:

```json
{"query": "How many customers churned, and what does our refund policy say?", "session_id": "demo-1"}
```

Returns `answer` and the actual `tools_used` in the current turn. Reuse a unique
session ID for follow-ups; omit it for an isolated request. Session IDs are not
credentials or access control. The current app has no sign-in.

## Maintenance and debugging

- `agent.py`: Gemini setup, system prompt, memory and final response extraction.
- `tools.py`: wrappers for document answers and restricted customer SQL. Shared
  model-facing descriptions live in `src/tool_descriptions.py` and also serve MCP.
- Memory lives in one process and resets on restart. Use one API worker. The
  model is initialized once; restart after changing Gemini configuration.
- SQL needs imported customer rows and the reader role. Policy answers need
  ingested documents. Tool errors are returned to the model, not treated as data.
- Agent calls are limited to 20 graph steps; failures return a clean API error.
  Inspect individual `/ask` or data-tool calls to isolate a failing tool.
- No churn-date field exists; monthly churn counts cannot be inferred from tenure.

Offline checks: `python -m unittest src.agent.test_agent`.
