"""Gemini document embeddings in the vector space used by our database."""

import os
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def validate_vectors(vectors, expected_count):
    array = np.asarray(vectors, dtype=np.float32)
    if array.shape != (expected_count, EMBEDDING_DIMENSIONS) or not np.isfinite(array).all():
        raise ValueError("Gemini returned an invalid embedding count, dimension, or value.")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if not np.isfinite(norms).all() or (norms == 0).any():
        raise ValueError("Gemini returned an invalid zero-length embedding.")
    return array / norms


def embed_documents(texts: list[str], title: str) -> np.ndarray:
    """Embed in small batches and normalize reduced-dimension vectors."""
    if not texts or any(not text.strip() for text in texts):
        raise ValueError("Embedding input must contain nonempty chunks.")
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in the project root .env or environment.")
    vectors = []
    try:
        with genai.Client(api_key=api_key, http_options=types.HttpOptions(
            timeout=60000, retry_options=types.HttpRetryOptions(attempts=1)
        )) as client:
            for start in range(0, len(texts), 20):
                batch = texts[start:start + 20]
                response = client.models.embed_content(
                    model=EMBEDDING_MODEL, contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT", title=title,
                        output_dimensionality=EMBEDDING_DIMENSIONS,
                    ),
                )
                batch_vectors = [embedding.values for embedding in (response.embeddings or [])]
                vectors.extend(validate_vectors(batch_vectors, len(batch)))
    except errors.APIError as exc:
        if exc.code == 429:
            raise RuntimeError("Gemini embedding quota or rate limit reached. Try again later.") from None
        raise RuntimeError("Gemini embedding request failed. Check your API key and model access.") from None
    except httpx.RequestError:
        raise RuntimeError("Could not reach Gemini or the embedding request timed out.") from None
    return np.asarray(vectors, dtype=np.float32)
