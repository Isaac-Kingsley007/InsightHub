"""Shared model-facing descriptions for LangChain and MCP tools."""

SEARCH_DOCUMENTS = """Answer a policy or document question using ingested documents.
Pass a self-contained natural-language query, including context from follow-ups.
Returns answer and source_chunks (supporting chunk IDs), or error. Preserve those
IDs when citing the answer. Insufficient evidence means unknown, not that a policy
does not exist. This tool cannot calculate customer counts or statistics."""

RUN_SAFE_QUERY = """Read customer records or calculate customer statistics with PostgreSQL.
Pass one SELECT on public.customers. Columns: customer_id UUID, name TEXT,
email TEXT, account_age_days INTEGER, login_frequency TEXT, daily_usage_mins INTEGER,
last_support_ticket TEXT, churn INTEGER (1=churned, 0=retained). Login frequency:
Daily, Weekly, Rarely. No churn dates, spending, or predicted-risk fields exist.
Filters, aggregates, CASE, grouping, sorting, LIMIT/OFFSET and common numeric/string
functions are supported; joins, CTEs, subqueries, casts and writes are rejected.
Returns columns, rows, row_count and truncated, or error. Rows align to columns.
Use SQL aggregates for totals: at most 100 rows are returned, not the full dataset.
Example: SELECT COUNT(*) AS churned FROM customers WHERE churn = 1."""
