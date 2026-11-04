# Customer data and read-only queries

Imports customer records into Neon and lets the agent or MCP client ask for
counts, filters, and averages using restricted SQL. Run from the project root
with the venv active and `DATABASE_URL` configured.

## Setup and import

```powershell
python -m src.db.setup
python -m src.data_tool.import_customers
python -m src.data_tool.setup_reader
```

Use an owner connection with table/write, CREATEROLE, and grant permissions.
Reader-role setup uses PostgreSQL 16+ membership options. The default import is
`datasets/customer_churn/train.csv`; override with `--file "path/to/customers.csv"`.
The test CSV is not imported by default.

The CSV must have the eight columns listed in the [root guide](../../README.md).
The importer validates UUIDs, integer ranges, login categories, churn labels,
column structure, and duplicate customer IDs before writing. One transaction
inserts new IDs and updates matching IDs. It does not delete other database rows.

## Use the query function

```python
from src.data_tool.query import run_safe_query

result = run_safe_query("SELECT COUNT(*) AS churned FROM customers WHERE churn = 1")
```

Returns `columns`, `rows`, `row_count`, and `truncated`; each row's values align
with `columns`. Errors raise `SafeQueryError`. Use lowercase database column names
from [schema.sql](../db/schema.sql). `churn` is the observed 0/1 label, not a model
prediction. No churn date or spending fields exist.

## Maintenance and debugging

- Allows one SELECT on `public.customers`, with filters, grouping, sorting,
  LIMIT/OFFSET, CASE, and common aggregate/numeric/string functions.
- Rejects writes, multiple statements, joins, CTEs, subqueries, casts, arbitrary
  functions, locking clauses, and other tables through an SQLGlot AST allowlist.
- Switches to `insighthub_customer_reader` in a read-only transaction. This
  NOLOGIN role has schema USAGE and customer-table SELECT. Reserve it for this
  tool and do not grant broader permissions; validation complements DB grants.
- Limits results to 100 rows, statements to 5 seconds, and lock waits to 2 seconds.
  Use SQL aggregates for totals rather than counting a truncated sample.
- Permission failures: rerun `setup_reader` as the owner; there is no owner fallback.
  Schema changes may need updates to the validator and shared tool descriptions.

```powershell
python -m unittest src.data_tool.test_data_tool
```
