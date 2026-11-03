"""Offline checks for web document ingestion."""
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from src.api.main import app


class DocumentEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_upload_reuses_ingestion_and_removes_temporary_file(self):
        paths = []
        def ingest(path):
            paths.append(path)
            self.assertEqual(path.read_text(), "Refunds within 30 days.")
            return "document-id", 2, True
        with patch("src.api.documents.ingest_document", side_effect=ingest):
            response = self.client.post("/ingest", files={"file": ("../policy.txt", b"Refunds within 30 days.", "text/plain")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": "document-id", "filename": "policy.txt", "chunk_count": 2, "created": True})
        self.assertFalse(paths[0].exists())

    def test_bad_uploads_never_call_ingestion(self):
        with patch("src.api.documents.ingest_document") as ingest:
            for filename, content, status in [("file.exe", b"no", 422), ("empty.txt", b"", 422),
                                              ("large.txt", b"x" * (10 * 1024 * 1024 + 1), 413)]:
                with self.subTest(filename=filename):
                    response = self.client.post("/ingest", files={"file": (filename, content)})
                    self.assertEqual(response.status_code, status)
            ingest.assert_not_called()

    def test_duplicate_and_quota_results(self):
        with patch("src.api.documents.ingest_document", return_value=("existing", 4, False)):
            self.assertFalse(self.client.post("/ingest", files={"file": ("policy.txt", b"policy")}).json()["created"])
        with patch("src.api.documents.ingest_document", side_effect=RuntimeError("Gemini embedding rate limit persisted.")):
            response = self.client.post("/ingest", files={"file": ("policy.txt", b"policy")})
            self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
