"""Offline tests for the Part C API and Gemini service."""

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from google.genai import errors

from src.api.main import app
from .service import analyze_text

EXAMPLE = {
    "sentiment": "mixed",
    "topics": ["onboarding", "dashboard performance", "usability"],
    "summary": "Helpful onboarding, but the dashboard is slow and confusing.",
}
TEXT = "The onboarding call was helpful but the dashboard still feels slow and confusing."


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "test-model"})
        env.start()
        self.addCleanup(env.stop)
        dotenv = patch("src.llm.service.load_dotenv")
        dotenv.start()
        self.addCleanup(dotenv.stop)
        client_patch = patch("src.llm.service.genai.Client")
        self.factory = client_patch.start()
        self.addCleanup(client_patch.stop)
        self.generate = self.factory.return_value.__enter__.return_value.models.generate_content
        self.generate.return_value = SimpleNamespace(text=json.dumps(EXAMPLE))
        self.api = TestClient(app)
        self.addCleanup(self.api.close)

    def test_pdf_contract_and_structured_output_configuration(self):
        response = self.api.post("/analyze", json={"text": TEXT})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), EXAMPLE)
        self.generate.assert_called_once()
        args = self.generate.call_args.kwargs
        self.assertEqual(args["contents"], TEXT)
        self.assertEqual(args["model"], "test-model")
        self.assertEqual(args["config"].response_mime_type, "application/json")
        self.assertFalse(args["config"].response_json_schema["additionalProperties"])

    def test_invalid_then_valid_retries_once(self):
        self.generate.side_effect = [SimpleNamespace(text="not JSON"),
                                     SimpleNamespace(text=json.dumps(EXAMPLE))]
        self.assertEqual(analyze_text(TEXT).sentiment, "mixed")
        self.assertEqual(self.generate.call_count, 2)

    def test_invalid_outputs_fail_cleanly_after_two_attempts(self):
        invalid_outputs = [None, "{broken", json.dumps({**EXAMPLE, "sentiment": "unknown"}),
                           json.dumps({**EXAMPLE, "topics": [""]}),
                           json.dumps({**EXAMPLE, "summary": "line one\nline two"}),
                           json.dumps({**EXAMPLE, "extra": "unwanted"})]
        for invalid in invalid_outputs:
            with self.subTest(output=invalid):
                self.generate.reset_mock()
                self.generate.return_value = SimpleNamespace(text=invalid)
                response = self.api.post("/analyze", json={"text": TEXT})
                self.assertEqual(response.status_code, 502)
                self.assertEqual(self.generate.call_count, 2)
                self.assertIn("after one retry", response.json()["detail"])

    def test_invalid_requests_do_not_call_provider(self):
        for payload in [{}, {"text": "   "}, {"text": 7}, {"text": TEXT, "extra": True}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.api.post("/analyze", json=payload).status_code, 422)
        self.generate.assert_not_called()

    def test_missing_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            response = self.api.post("/analyze", json={"text": TEXT})
        self.assertEqual(response.status_code, 503)
        self.factory.assert_not_called()

    def test_provider_errors_are_sanitized_without_output_retry(self):
        for failure, status in [(errors.APIError(429, {"message": "private provider detail"}), 503),
                                (errors.APIError(500, {"message": "private provider detail"}), 502),
                                (httpx.ReadTimeout("private provider detail"), 504),
                                (httpx.ConnectError("private provider detail"), 503)]:
            with self.subTest(status=status):
                self.generate.reset_mock()
                self.generate.side_effect = failure
                response = self.api.post("/analyze", json={"text": TEXT})
                self.assertEqual(response.status_code, status)
                self.assertNotIn("private provider detail", response.text)
                self.generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
