# Customer data tool — Part E

This adds the `public.customers` table to database initialization, imports only
`datasets/customer_churn/train.csv` by default, and provides `run_safe_query(sql)`
for the future agent and MCP server. Nothing here calls an LLM.

## Setup and import

From the project root, activate the existing venv and ensure the root `.env`
contains your Neon `DATABASE_URL`, including its SSL parameters.

```powershell
.\.venv\Scripts\Activate.ps1
python -m src.db.setup
python -m src.data_tool.import_customers
python -m src.data_tool.setup_reader
```

`setup_reader` uses PostgreSQL 16+ role membership options (supported on current
Neon versions). Use the database owner's connection for these setup commands:
it needs table creation/write privileges, CREATEROLE, and permission to grant
SELECT on customers. The dedicated `insighthub_customer_reader` role is NOLOGIN
and receives schema USAGE and SELECT on customers only. The tool explicitly
switches to that role; it never falls back to the owner if setup is missing.
Reserve this role name for this tool; do not grant it broader permissions.

The importer validates UUIDs, integer ranges, login categories, binary churn
labels, CSV structure, and duplicate IDs before writing. All records commit in
one transaction. Repeating the command updates matching customer IDs and inserts
new ones; it does not remove other existing rows. `test_.csv` is not imported.
An optional `--file` argument accepts another CSV with the same eight columns.

## Query function

```python
from src.data_tool.query import run_safe_query

result = run_safe_query(
    "SELECT login_frequency, COUNT(*) AS customers "
    "FROM customers WHERE churn = 1 GROUP BY login_frequency"
)
```

Returns `columns`, `rows` (lists of values aligned to columns), `row_count`, and
`truncated`. UUIDs and aggregate decimals are converted to JSON-compatible values.
Failures raise `SafeQueryError` with a safe message instead of database internals.

Supported SQL is deliberately limited: one SELECT on customers, filters,
grouping, sorting, LIMIT/OFFSET, CASE, and common aggregates/numeric/string
functions. Use lowercase snake_case column names from `src/db/schema.sql`.
CTEs, joins, subqueries, arbitrary functions, casts, other tables, multiple
statements, writes, SELECT INTO, and locking clauses are rejected by an AST
allowlist. SQL is regenerated from the validated tree before execution, with the
customer table explicitly bound to `public.customers`.

Each execution uses a read-only transaction and the restricted reader role,
with pg_catalog first in the search path, a 5-second statement timeout,
2-second lock timeout, and a maximum of 100 returned rows. A 101st row is used
only to mark truncation. These controls complement SQL validation; keep normal
PostgreSQL PUBLIC grants restricted and do not expose the administrative database
credentials to the model or MCP clients.

The dataset has no churn date. Questions such as “churned last month” cannot be
answered from these columns. `churn` is an observed label, not a model prediction.

Dependencies already used by the project: `psycopg[binary]`, `python-dotenv`;
SQL validation additionally uses `sqlglot`.

```powershell
python -m unittest src.data_tool.test_data_tool
```
