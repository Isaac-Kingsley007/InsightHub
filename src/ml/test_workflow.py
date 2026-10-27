"""Run: python -m unittest src.ml.test_workflow."""

import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .data import clean_customers
from .models import build_models
from .predict import predict_customers
from .train import train


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({
            "Customer_ID": [f"c{i}" for i in range(12)],
            "Account_Age_Days": [30, 60, 90, 120] * 3,
            "Daily_Usage_Mins": [1, 50, 2, 80] * 3,
            "Login_Frequency": [" Rarely ", "DAILY", "Weekly", "Daily"] * 3,
            "Churn": [1, 0, 1, 0] * 3,
        })

    def test_invalid_inputs_are_rejected(self):
        for column, value in [("Daily_Usage_Mins", -1), ("Account_Age_Days", np.inf),
                              ("Login_Frequency", "Sometimes"), ("Churn", 2)]:
            with self.subTest(column=column):
                invalid = self.frame.copy()
                invalid[column] = value
                with self.assertRaises(ValueError):
                    clean_customers(invalid, require_target=True)

    def test_imputation_uses_training_statistics(self):
        model = build_models()["LogisticRegression"].fit(self.frame, self.frame.Churn)
        numeric = model.named_steps["preprocess"].named_transformers_["numeric"]
        before = numeric.named_steps["impute"].statistics_.copy()
        incoming = self.frame.iloc[:2].drop(columns="Churn").copy()
        incoming["Daily_Usage_Mins"] = [np.nan, 100000]
        predictions = predict_customers(model, incoming)
        self.assertEqual(len(predictions), 2)
        self.assertTrue(predictions.churn_probability.between(0, 1).all())
        np.testing.assert_array_equal(before, numeric.named_steps["impute"].statistics_)

    def test_saved_pipeline_predicts_raw_unlabeled_rows(self):
        for name, model in build_models().items():
            with self.subTest(model=name), tempfile.TemporaryDirectory() as directory:
                model.fit(self.frame, self.frame.Churn)
                path = Path(directory) / "model.joblib"
                joblib.dump(model, path)
                incoming = self.frame.drop(columns="Churn")
                expected = predict_customers(model, incoming)
                actual = predict_customers(joblib.load(path), incoming)
                pd.testing.assert_frame_equal(expected, actual)
                self.assertEqual(actual.Customer_ID.tolist(), incoming.Customer_ID.tolist())

    def test_overlapping_customers_are_rejected_before_training(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "customers.csv"
            self.frame.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "share Customer_ID"):
                train(path, path, Path(directory) / "output")


if __name__ == "__main__":
    unittest.main()
