"""Offline rate-limit tests; no real requests or waits."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from google.genai import errors

from .embeddings import embed_documents, rate_limit_info


def quota_error(delay="56s", limit="100", quota_id="RequestsPerMinute", metric="embed_content_free_tier_requests"):
    return errors.APIError(429, {"error": {"details": [
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay},
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [
            {"quotaMetric": metric, "quotaId": quota_id, "quotaValue": limit}]}]}})


def response(count):
    return SimpleNamespace(embeddings=[SimpleNamespace(values=[1.] * 768) for _ in range(count)])


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        patches = [patch("src.rag.embeddings.load_dotenv"),
                   patch.dict("os.environ", {"GEMINI_API_KEY": "test", "EMBEDDING_BATCH_SIZE": "20",
                                             "EMBEDDING_CHUNKS_PER_MINUTE": "60"}),
                   patch("src.rag.embeddings.time.monotonic", return_value=0),
                   patch("src.rag.embeddings.time.sleep"),
                   patch("src.rag.embeddings.random.uniform", return_value=0),
                   patch("src.rag.embeddings.genai.Client")]
        values = [item.start() for item in patches]
        for item in patches:
            self.addCleanup(item.stop)
        self.sleep = values[3]
        self.generate = values[5].return_value.__enter__.return_value.models.embed_content

    def test_retries_same_batch_without_reembedding_completed_chunks(self):
        self.generate.side_effect = [response(20), quota_error(), response(1)]
        texts = [str(index) for index in range(21)]
        self.assertEqual(embed_documents(texts, "policy").shape, (21, 768))
        contents = [call.kwargs["contents"] for call in self.generate.call_args_list]
        self.assertEqual(contents, [texts[:20], texts[20:], texts[20:]])
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [20, 76])

    def test_retries_are_bounded_and_backoff_increases(self):
        self.generate.side_effect = quota_error()
        with self.assertRaisesRegex(RuntimeError, "five retries"):
            embed_documents(["policy"], "policy")
        self.assertEqual(self.generate.call_count, 6)
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [76, 120, 240, 300, 300])

    def test_daily_and_zero_quotas_do_not_retry(self):
        for failure in [quota_error(limit="0"), quota_error(quota_id="RequestsPerDay")]:
            with self.subTest(failure=failure):
                self.generate.reset_mock()
                self.generate.side_effect = failure
                with self.assertRaisesRegex(RuntimeError, "daily quota"):
                    embed_documents(["policy"], "policy")
                self.generate.assert_called_once()
        self.sleep.assert_not_called()

    def test_other_api_errors_do_not_retry(self):
        self.generate.side_effect = errors.APIError(403, {"error": {"message": "private"}})
        with self.assertRaisesRegex(RuntimeError, "request failed"):
            embed_documents(["policy"], "policy")
        self.generate.assert_called_once()
        self.sleep.assert_not_called()

    def test_lower_reported_quota_slows_following_batches(self):
        self.generate.side_effect = [quota_error(limit="10"), response(20), response(1)]
        embed_documents(["policy"] * 21, "policy")
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [200, 200])

    def test_missing_or_malformed_retry_info_has_safe_fallback(self):
        self.assertEqual(rate_limit_info(errors.APIError(429, {})), (None, None, False))
        self.assertEqual(rate_limit_info(quota_error(delay="NaNs")), (None, 100, False))
        self.generate.side_effect = [errors.APIError(429, {}), response(1)]
        embed_documents(["policy"], "policy")
        self.sleep.assert_called_once_with(80)

    def test_invalid_settings_fail_before_api_calls(self):
        with patch.dict("os.environ", {"EMBEDDING_CHUNKS_PER_MINUTE": "nan"}):
            with self.assertRaises(ValueError):
                embed_documents(["policy"], "policy")
        self.generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
