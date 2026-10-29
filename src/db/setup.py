"""Create the database optionally, then enable pgvector and create RAG tables."""

import argparse
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from .connection import database_url


def create_database(url):
    """For a local server: connect to postgres and create the URL's database."""
    name = conninfo_to_dict(url).get("dbname")
    if not name:
        raise ValueError("DATABASE_URL must include a database name.")
    admin_url = make_conninfo(url, dbname="postgres")
    with psycopg.connect(admin_url, autocommit=True, connect_timeout=10) as connection:
        exists = connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if not exists:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


def initialize_schema(url):
    # Do not register the vector type until its extension has been created.
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(url, connect_timeout=10) as connection:
        connection.execute(schema)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-database", action="store_true",
                        help="Create the database on an existing local server (requires CREATEDB).")
    args = parser.parse_args()
    url = database_url()
    if args.create_database:
        create_database(url)
    initialize_schema(url)
    print("Database schema ready: documents and document_chunks (768 dimensions).")


if __name__ == "__main__":
    main()
