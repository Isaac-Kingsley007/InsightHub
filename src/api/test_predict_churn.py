"""Check the API against the saved pipeline and invalid requests."""

import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from src.api.main import app
from src.ml.predict import load_churn_model, predict_customers

CUSTOMER = {"Account_Age_Days": 790, "Login_Frequency": "Weekly", "Daily_Usage_Mins": 28}


class ChurnEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_matches_saved_pipeline_prediction(self):
        expected = predict_customers(load_churn_model(), pd.DataFrame([CUSTOMER])).iloc[0]
        response = self.client.post("/predict-churn", json=CUSTOMER)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["predicted_churn"], int(expected.predicted_churn))
        self.assertAlmostEqual(response.json()["churn_probability"], expected.churn_probability)

    def test_invalid_input_rejected_before_loading_model(self):
        with patch("src.api.main.load_churn_model") as load:
            for change in [{"Account_Age_Days": -1}, {"Login_Frequency": "Monthly"},
                           {"Daily_Usage_Mins": -5}, {"Account_Age_Days": True}, {"Churn": 1}]:
                with self.subTest(change=change):
                    self.assertEqual(self.client.post("/predict-churn", json={**CUSTOMER, **change}).status_code, 422)
            self.assertEqual(self.client.post("/predict-churn", json={}).status_code, 422)
            load.assert_not_called()

    def test_missing_model_returns_clean_error(self):
        with patch("src.api.main.load_churn_model", side_effect=FileNotFoundError("private path")):
            response = self.client.post("/predict-churn", json=CUSTOMER)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private path", response.text)


if __name__ == "__main__":
    unittest.main()
