"""Gemini document embeddings in the vector space used by our database."""

import os
import math
import random
import time
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def rate_limit_info(exc):
    """Read Google's structured quota details without parsing the error prose."""
    payload = exc.details if isinstance(exc.details, dict) else {}
    error = payload.get("error", payload)
    delay, minute_limit, permanent = None, None, False
    for detail in error.get("details", []):
        if detail.get("@type", "").endswith("RetryInfo"):
            try:
                value = float(detail.get("retryDelay", "").removesuffix("s"))
                if math.isfinite(value) and value >= 0:
                    delay = value
            except (ValueError, TypeError, AttributeError):
                pass
        for violation in detail.get("violations", []):
            metric = violation.get("quotaMetric", "").lower()
            quota_id = violation.get("quotaId", "").lower()
            try:
                limit = float(violation.get("quotaValue"))
            except (TypeError, ValueError):
                limit = None
            if limit == 0 or "perday" in quota_id or "per_day" in metric:
                permanent = True
            if "request" in metric and ("perminute" in quota_id or "per_minute" in metric):
                if limit is not None and math.isfinite(limit) and limit > 0:
                    minute_limit = limit if minute_limit is None else min(minute_limit, limit)
    return delay, minute_limit, permanent


def embed_query(question: str) -> np.ndarray:
    """Use the document vector space, optimized for search queries."""
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in the project root .env or environment.")
    with genai.Client(api_key=api_key, http_options=types.HttpOptions(
        timeout=60000, retry_options=types.HttpRetryOptions(attempts=1)
    )) as client:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, contents=question,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY", output_dimensionality=EMBEDDING_DIMENSIONS
            ),
        )
        return validate_vectors([item.values for item in (response.embeddings or [])], 1)[0]


def validate_vectors(vectors, expected_count):
    array = np.asarray(vectors, dtype=np.float32)
    if array.shape != (expected_count, EMBEDDING_DIMENSIONS) or not np.isfinite(array).all():
        raise ValueError("Gemini returned an invalid embedding count, dimension, or value.")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if not np.isfinite(norms).all() or (norms == 0).any():
        raise ValueError("Gemini returned an invalid zero-length embedding.")
    return array / norms


def embed_documents(texts: list[str], title: str) -> np.ndarray:
    """Embed paced batches, retrying only the failed batch on temporary 429s."""
    if not texts or any(not text.strip() for text in texts):
        raise ValueError("Embedding input must contain nonempty chunks.")
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in the project root .env or environment.")
    try:
        batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "20"))
        chunks_per_minute = float(os.getenv("EMBEDDING_CHUNKS_PER_MINUTE", "60"))
        if not 1 <= batch_size <= 100 or not math.isfinite(chunks_per_minute) or chunks_per_minute <= 0:
            raise ValueError
    except ValueError:
        raise ValueError("EMBEDDING_BATCH_SIZE must be 1-100 and EMBEDDING_CHUNKS_PER_MINUTE must be positive.") from None
    vectors = []
    next_request = 0.0
    try:
        with genai.Client(api_key=api_key, http_options=types.HttpOptions(
            timeout=60000, retry_options=types.HttpRetryOptions(attempts=1)
        )) as client:
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]
                for retry in range(6):  # Initial attempt plus at most five retries.
                    wait = max(0.0, next_request - time.monotonic())
                    if wait:
                        print(f"Pacing embedding requests: waiting {wait:.1f}s.", flush=True)
                        time.sleep(wait)
                    next_request = time.monotonic() + len(batch) * 60 / chunks_per_minute
                    try:
                        response = client.models.embed_content(
                            model=EMBEDDING_MODEL, contents=batch,
                            config=types.EmbedContentConfig(
                                task_type="RETRIEVAL_DOCUMENT", title=title,
                                output_dimensionality=EMBEDDING_DIMENSIONS,
                            ),
                        )
                        break
                    except errors.APIError as exc:
                        if exc.code != 429:
                            raise
                        delay, quota, permanent = rate_limit_info(exc)
                        if permanent:
                            raise RuntimeError("Gemini embedding daily quota is exhausted or quota is zero. "
                                               "Check AI Studio limits; minute retries will not resolve this.") from None
                        if retry == 5:
                            raise RuntimeError("Gemini embedding rate limit persisted after five retries. "
                                               "Lower EMBEDDING_CHUNKS_PER_MINUTE or check project usage.") from None
                        if quota is not None:
                            chunks_per_minute = min(chunks_per_minute, quota * 0.6)
                        backoff = min(60 * 2 ** retry, 300)
                        wait = max((delay if delay is not None else 60) + 20,
                                   backoff, len(batch) * 60 / chunks_per_minute) + random.uniform(0, 2)
                        next_request = time.monotonic() + wait
                        print(f"Gemini embedding rate limit; retry {retry + 1}/5 in {wait:.1f}s "
                              f"for chunks {start + 1}-{start + len(batch)}.", flush=True)
                batch_vectors = [embedding.values for embedding in (response.embeddings or [])]
                vectors.extend(validate_vectors(batch_vectors, len(batch)))
                print(f"Embedded {len(vectors)}/{len(texts)} chunks.", flush=True)
    except errors.APIError as exc:
        raise RuntimeError("Gemini embedding request failed. Check your API key and model access.") from None
    except httpx.RequestError:
        raise RuntimeError("Could not reach Gemini or the embedding request timed out.") from None
    return np.asarray(vectors, dtype=np.float32)
