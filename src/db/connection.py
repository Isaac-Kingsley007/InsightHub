"""Connections shared by schema setup and future RAG services."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector


def database_url():
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise ValueError("Set DATABASE_URL in the project root .env or environment.")
    return url


def connect_db():
    """Return a connection with vector support; use it as a context manager.

    Run src.db.setup first so the vector extension exists.
    """
    connection = psycopg.connect(database_url(), connect_timeout=10)
    try:
        register_vector(connection)
    except Exception:
        connection.close()
        raise
    return connection
