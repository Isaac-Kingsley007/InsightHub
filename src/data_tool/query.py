"""A deliberately small SQL subset for the agent's run_safe_query(sql) tool."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import psycopg
from psycopg import sql as pgsql
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from src.db.connection import database_url
from .setup_reader import READER_ROLE

COLUMNS = {"customer_id", "name", "email", "account_age_days", "login_frequency",
           "daily_usage_mins", "last_support_ticket", "churn"}
# Fail closed on every other AST node: no CTEs, joins, subqueries, casts,
# arbitrary functions, SELECT INTO, locking, set operations or DML.
ALLOWED_NODES = {
    "Select", "From", "Table", "TableAlias", "Identifier", "Column", "Star",
    "Alias", "Literal", "Null", "Boolean", "Paren", "Where", "Group", "Having",
    "Order", "Ordered", "Limit", "Offset", "Distinct", "And", "Or", "Not",
    "EQ", "NEQ", "GT", "GTE", "LT", "LTE", "Is", "In", "Between", "Like", "ILike",
    "Add", "Sub", "Mul", "Div", "Mod", "Neg", "Count", "Sum", "Avg", "Min", "Max",
    "Round", "Abs", "Coalesce", "Nullif", "Lower", "Upper", "Length",
    "Case", "If",
}


class SafeQueryError(ValueError):
    """Invalid or unsuccessful query; safe for a tool to report to the agent."""


def validate_query(sql):
    if not isinstance(sql, str) or not sql.strip() or len(sql) > 10000:
        raise SafeQueryError("Provide one SELECT query of at most 10,000 characters.")
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except (SqlglotError, RecursionError):
        raise SafeQueryError("Could not parse the PostgreSQL query.") from None
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise SafeQueryError("Only a single SELECT query is allowed.")
    tree = statements[0]
    for node in tree.walk():
        if type(node).__name__ not in ALLOWED_NODES:
            raise SafeQueryError(f"Unsupported SQL operation: {type(node).__name__}.")
    tables = list(tree.find_all(exp.Table))
    if len(tables) != 1 or tables[0].name != "customers" or tables[0].db not in ("", "public") or tables[0].catalog:
        raise SafeQueryError("Query exactly one table: public.customers.")
    table = tables[0]
    # Always bind to the real table, not a relation in a temporary/search-path schema.
    table.set("db", exp.to_identifier("public"))
    aliases = {alias.alias for alias in tree.find_all(exp.Alias)}
    for column in tree.find_all(exp.Column):
        if column.catalog or column.db or column.table not in ("", "customers", table.alias):
            raise SafeQueryError("Invalid column qualifier.")
        if not column.is_star and column.name not in COLUMNS | aliases:
            raise SafeQueryError(f"Unknown customer column: {column.name}.")
    for clause in (tree.args.get("limit"), tree.args.get("offset")):
        if clause is not None:
            value = clause.expression
            if not isinstance(value, exp.Literal) or value.is_string or not value.this.isdigit():
                raise SafeQueryError("LIMIT and OFFSET must be nonnegative integer literals.")
    return tree.sql(dialect="postgres")


def json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def run_safe_query(sql: str) -> dict:
    """Return at most 100 customer-query rows, their columns, and a truncation flag."""
    statement = validate_query(sql)
    try:
        # No pgvector registration: READ ONLY must precede all data queries.
        with psycopg.connect(database_url(), connect_timeout=10) as connection:
            connection.execute("SET TRANSACTION READ ONLY")
            connection.execute(pgsql.SQL("SET LOCAL ROLE {}").format(pgsql.Identifier(READER_ROLE)))
            connection.execute("SET LOCAL search_path = pg_catalog, public")
            connection.execute("SET LOCAL statement_timeout = '5s'")
            connection.execute("SET LOCAL lock_timeout = '2s'")
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM ({statement}) AS customer_result LIMIT 101", prepare=False)
                columns = [column.name for column in cursor.description]
                rows = cursor.fetchmany(101)
        return {"columns": columns, "rows": [[json_value(value) for value in row] for row in rows[:100]],
                "row_count": min(len(rows), 100), "truncated": len(rows) > 100}
    except psycopg.errors.QueryCanceled:
        raise SafeQueryError("Query exceeded the 5-second time limit.") from None
    except psycopg.Error:
        raise SafeQueryError("Query failed. Check the SQL, database connection, schema, and reader-role setup.") from None
    except ValueError:
        raise SafeQueryError("Configure DATABASE_URL before executing customer queries.") from None
