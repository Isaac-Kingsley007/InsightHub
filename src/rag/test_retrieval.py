"""Offline retrieval/API checks: python -m unittest src.rag.test_retrieval."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient
from google.genai import errors

from src.api.main import app
from .ask import INSUFFICIENT
from .embeddings import embed_query
from .retrieval import retrieve_chunks

CHUNK = {"id": "chunk-1", "content": "Refunds are allowed within 30 days.",
         "filename": "policy.pdf", "page_number": 1, "similarity": 0.8}
ANSWER = {"answer": "You have 30 days to request a refund.", "source_chunks": ["chunk-1"]}


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        patches = [patch.dict("os.environ", {"GEMINI_API_KEY": "test", "DATABASE_URL": "test",
                                             "RAG_TOP_K": "5", "RAG_MIN_SIMILARITY": "0.5"}),
                   patch("src.rag.ask.load_dotenv"),
                   patch("src.rag.ask.embed_query", return_value=np.ones(768)),
                   patch("src.rag.ask.retrieve_chunks", return_value=[CHUNK]),
                   patch("src.rag.ask.genai.Client")]
        values = [item.start() for item in patches]
        for item in patches:
            self.addCleanup(item.stop)
        self.embed, self.retrieve, self.factory = values[2:]
        self.generate = self.factory.return_value.__enter__.return_value.models.generate_content
        self.generate.return_value = SimpleNamespace(text=json.dumps(ANSWER))
        self.api = TestClient(app)
        self.addCleanup(self.api.close)

    def ask(self):
        return self.api.post("/ask", json={"question": "When can I request a refund?"})

    def test_success_returns_pdf_contract(self):
        response = self.ask()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ANSWER)
        self.assertEqual(self.retrieve.call_args.args[1:], (5, 0.5))
        context = json.loads(self.generate.call_args.kwargs["contents"])
        self.assertEqual(context["chunks"][0]["id"], "chunk-1")

    def test_no_relevant_chunks_skips_generation(self):
        self.retrieve.return_value = []
        self.assertEqual(self.ask().json(), {"answer": INSUFFICIENT, "source_chunks": []})
        self.generate.assert_not_called()

    def test_invalid_citations_retry_once_then_error(self):
        for output in [{**ANSWER, "source_chunks": ["invented"]},
                       {**ANSWER, "source_chunks": []}, {"answer": "missing citations field"}]:
            with self.subTest(output=output):
                self.generate.reset_mock()
                self.generate.return_value = SimpleNamespace(text=json.dumps(output))
                self.assertEqual(self.ask().status_code, 502)
                self.assertEqual(self.generate.call_count, 2)

    def test_retry_recovers_from_malformed_json(self):
        self.generate.side_effect = [SimpleNamespace(text="broken"),
                                     SimpleNamespace(text=json.dumps(ANSWER))]
        self.assertEqual(self.ask().json(), ANSWER)
        self.assertEqual(self.generate.call_count, 2)

    def test_model_can_abstain_despite_similarity(self):
        self.generate.return_value = SimpleNamespace(text=json.dumps(
            {"answer": INSUFFICIENT, "source_chunks": ["chunk-1"]}))
        self.assertEqual(self.ask().json(), {"answer": INSUFFICIENT, "source_chunks": []})

    def test_bad_requests_and_settings(self):
        self.assertEqual(self.api.post("/ask", json={"question": "  "}).status_code, 422)
        self.embed.assert_not_called()
        with patch.dict("os.environ", {"RAG_MIN_SIMILARITY": "nan"}):
            self.assertEqual(self.ask().status_code, 503)

    def test_quota_error_is_sanitized(self):
        self.embed.side_effect = errors.APIError(429, {"message": "private details"})
        response = self.ask()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private details", response.text)


class VectorSearchTests(unittest.TestCase):
    def test_query_task_and_dimensions(self):
        with patch("src.rag.embeddings.load_dotenv"), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "test"}), \
             patch("src.rag.embeddings.genai.Client") as factory:
            call = factory.return_value.__enter__.return_value.models.embed_content
            call.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[1.] * 768)])
            vector = embed_query("refund policy")
            self.assertEqual(call.call_args.kwargs["config"].task_type, "RETRIEVAL_QUERY")
            self.assertEqual(call.call_args.kwargs["config"].output_dimensionality, 768)
            self.assertAlmostEqual(float(np.linalg.norm(vector)), 1, places=5)

    def test_sql_search_filters_scores_and_model(self):
        with patch("src.rag.retrieval.connect_db") as connect:
            connection = connect.return_value.__enter__.return_value
            connection.execute.return_value.fetchall.return_value = [
                ("good", "policy", "policy.pdf", 1, 0.8),
                ("weak", "other", "policy.pdf", 2, 0.2)]
            chunks = retrieve_chunks(np.ones(768), 5, 0.5)
            self.assertEqual([chunk["id"] for chunk in chunks], ["good"])
            sql, parameters = connection.execute.call_args.args
            self.assertIn("<=>", sql)
            self.assertEqual(parameters[1], "gemini-embedding-001")
            self.assertEqual(parameters[-1], 5)


if __name__ == "__main__":
    unittest.main()
