"""Provision a restricted role for the query tool; run once after src.db.setup."""

import psycopg
from psycopg import sql

from src.db.connection import database_url

READER_ROLE = "insighthub_customer_reader"


def setup_reader():
    with psycopg.connect(database_url(), connect_timeout=10) as connection:
        exists = connection.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (READER_ROLE,)).fetchone()
        if not exists:
            connection.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT").format(
                sql.Identifier(READER_ROLE)))
        connection.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(READER_ROLE)))
        connection.execute(sql.SQL("GRANT SELECT ON public.customers TO {}").format(sql.Identifier(READER_ROLE)))
        current_user = connection.execute("SELECT current_user").fetchone()[0]
        connection.execute(sql.SQL("GRANT {} TO {} WITH INHERIT FALSE, SET TRUE").format(
            sql.Identifier(READER_ROLE), sql.Identifier(current_user)))


if __name__ == "__main__":
    try:
        setup_reader()
    except psycopg.Error:
        raise SystemExit("Reader setup failed. Run schema setup first and use a role with CREATEROLE and customer-table grant privileges.") from None
    print("Customer reader role ready; the query tool switches to it inside each read-only transaction.")
