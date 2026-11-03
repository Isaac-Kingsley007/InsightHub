"""Batch inference: python -m src.ml.predict --data customers.csv --output predictions.csv."""

import argparse
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from .data import RAW_FEATURES, clean_customers

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "artifacts"


@lru_cache(maxsize=1)
def load_churn_model():
    """Load the trusted local training artifact once per API process."""
    return joblib.load(DEFAULT_OUTPUT / "churn_model.pkl")


def predict_customers(model, customers):
    """Accept raw customer columns, returning ID (if available), label, and probability."""
    frame = clean_customers(customers)
    result = frame[["Customer_ID"]].copy() if "Customer_ID" in frame else pd.DataFrame(index=frame.index)
    result["predicted_churn"] = model.predict(frame[RAW_FEATURES])
    positive_index = list(model.classes_).index(1)
    result["churn_probability"] = model.predict_proba(frame[RAW_FEATURES])[:, positive_index]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_OUTPUT / "churn_model.pkl")
    parser.add_argument("--data", type=Path, default=ROOT / "datasets/customer_churn/test_.csv")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT / "test_predictions.csv")
    args = parser.parse_args()
    # Load only trusted artifacts: joblib deserialization can execute code.
    model = joblib.load(args.model)
    result = predict_customers(model, pd.read_csv(args.data))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Saved {len(result)} predictions to {args.output}")


if __name__ == "__main__":
    main()
