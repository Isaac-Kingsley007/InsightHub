CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.customers (
    customer_id UUID PRIMARY KEY,
    name TEXT,
    email TEXT,
    account_age_days INTEGER NOT NULL CHECK (account_age_days >= 0),
    login_frequency TEXT NOT NULL CHECK (login_frequency IN ('Daily', 'Weekly', 'Rarely')),
    daily_usage_mins INTEGER NOT NULL CHECK (daily_usage_mins >= 0),
    last_support_ticket TEXT,
    churn INTEGER NOT NULL CHECK (churn IN (0, 1))
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    embedding_model TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    page_number INTEGER CHECK (page_number >= 1),
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    embedding VECTOR(768) NOT NULL,
    UNIQUE (document_id, chunk_index)
);
