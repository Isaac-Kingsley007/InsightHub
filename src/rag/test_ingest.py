"""Offline tests: python -m unittest src.rag.test_ingest."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from src.db.documents import save_document
from .documents import Document, DocumentPage
from .embeddings import validate_vectors, embed_documents
from .ingest import ingest_document
from .chunking import chunk_document


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.document = Document("policy.txt", "hash", [DocumentPage("Refunds within 30 days.", None)])

    def test_duplicate_skips_embedding_and_storage(self):
        with patch("src.rag.ingest.read_document", return_value=self.document), \
             patch("src.rag.ingest.find_document", return_value=("existing", 3)), \
             patch("src.rag.ingest.embed_documents") as embed, \
             patch("src.rag.ingest.save_document") as save:
            self.assertEqual(ingest_document("policy.txt"), ("existing", 3, False))
            embed.assert_not_called()
            save.assert_not_called()

    def test_embedding_failure_never_writes(self):
        with patch("src.rag.ingest.read_document", return_value=self.document), \
             patch("src.rag.ingest.find_document", return_value=None), \
             patch("src.rag.ingest.embed_documents", side_effect=RuntimeError("quota")), \
             patch("src.rag.ingest.save_document") as save:
            with self.assertRaises(RuntimeError):
                ingest_document("policy.txt")
            save.assert_not_called()

    def test_invalid_vectors_rejected(self):
        for vectors in [np.zeros((1, 768)), np.ones((1, 767)),
                        np.full((1, 768), np.nan), np.ones((2, 768))]:
            with self.subTest(shape=vectors.shape), self.assertRaises(ValueError):
                validate_vectors(vectors, 1)

    def test_embedding_batches_and_normalizes(self):
        with patch("src.rag.embeddings.load_dotenv"), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "test"}), \
             patch("src.rag.embeddings.genai.Client") as factory:
            generate = factory.return_value.__enter__.return_value.models.embed_content
            generate.side_effect = [SimpleNamespace(embeddings=[SimpleNamespace(values=[1.] * 768)] * 20),
                                    SimpleNamespace(embeddings=[SimpleNamespace(values=[2.] * 768)])]
            result = embed_documents(["policy"] * 21, "policy.txt")
            self.assertEqual(result.shape, (21, 768))
            np.testing.assert_allclose(np.linalg.norm(result, axis=1), 1, atol=1e-6)
            self.assertEqual(generate.call_count, 2)
            config = generate.call_args.kwargs["config"]
            self.assertEqual(config.task_type, "RETRIEVAL_DOCUMENT")
            self.assertEqual(config.output_dimensionality, 768)

    def test_chunk_insert_failure_exits_transaction_with_error(self):
        chunks = chunk_document(self.document, "document-id")
        with patch("src.db.documents.connect_db") as connect:
            connection = connect.return_value.__enter__.return_value
            connection.execute.return_value.fetchone.return_value = ("document-id",)
            connection.cursor.return_value.__enter__.return_value.executemany.side_effect = RuntimeError("insert")
            with self.assertRaises(RuntimeError):
                save_document("document-id", self.document, chunks, np.ones((1, 768)))
            self.assertIs(connect.return_value.__exit__.call_args.args[0], RuntimeError)

    def test_concurrent_duplicate_does_not_insert_chunks(self):
        chunks = chunk_document(self.document, "document-id")
        with patch("src.db.documents.connect_db") as connect:
            connection = connect.return_value.__enter__.return_value
            connection.execute.return_value.fetchone.side_effect = [None, ("existing", 2)]
            self.assertEqual(save_document("document-id", self.document, chunks, np.ones((1, 768))),
                             ("existing", 2, False))
            connection.cursor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
