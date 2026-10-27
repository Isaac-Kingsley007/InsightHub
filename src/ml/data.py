"""Validation and deterministic features shared by training and inference."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

RAW_FEATURES = ["Account_Age_Days", "Login_Frequency", "Daily_Usage_Mins"]
NUMERIC_FEATURES = ["tenure_months", "Daily_Usage_Mins", "log_daily_usage"]
LOGIN_VALUES = {"daily": "Daily", "weekly": "Weekly", "rarely": "Rarely"}


def clean_customers(frame, require_target=False):
    """Normalize inputs; reject invalid observed values; preserve missing predictors.

    Missing predictors are imputed by the training pipeline, never from test data.
    Identifiers and support text are retained for reporting but never modeled.
    """
    required = RAW_FEATURES + (["Churn"] if require_target else [])
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if frame.empty:
        raise ValueError("Customer data must contain at least one row.")
    result = frame.copy()
    for column in ["Account_Age_Days", "Daily_Usage_Mins"]:
        source = result[column].replace(r"^\s*$", np.nan, regex=True)
        numeric = pd.to_numeric(source, errors="coerce")
        invalid = source.notna() & (numeric.isna() | ~np.isfinite(numeric) | (numeric < 0))
        if invalid.any():
            raise ValueError(f"{column}: {int(invalid.sum())} invalid or negative values.")
        result[column] = numeric
    login = result["Login_Frequency"].astype("string").str.strip().str.lower()
    login = login.replace("", pd.NA)
    invalid = login.notna() & ~login.isin(LOGIN_VALUES)
    if invalid.any():
        raise ValueError(f"Unknown Login_Frequency values: {login[invalid].unique().tolist()}")
    result["Login_Frequency"] = login.map(LOGIN_VALUES).astype(object)
    result.loc[login.isna(), "Login_Frequency"] = np.nan
    if require_target:
        target = pd.to_numeric(result["Churn"], errors="coerce")
        if not target.isin([0, 1]).all():
            raise ValueError("Churn must contain only 0 or 1, with no missing labels.")
        result["Churn"] = target.astype(int)
    return result


def load_customers(path):
    frame = pd.read_csv(path)
    original_rows = len(frame)
    frame = clean_customers(frame, require_target=True).drop_duplicates().reset_index(drop=True)
    if "Customer_ID" not in frame or frame["Customer_ID"].isna().any():
        raise ValueError("Training CSV requires nonmissing Customer_ID values.")
    frame["Customer_ID"] = frame["Customer_ID"].astype(str).str.strip()
    if frame["Customer_ID"].eq("").any() or frame["Customer_ID"].duplicated().any():
        raise ValueError("Customer_ID must be nonempty and unique after duplicate-row removal.")
    return frame, {"input_rows": original_rows, "clean_rows": len(frame),
                   "duplicates_removed": original_rows - len(frame),
                   "missing_predictors": frame[RAW_FEATURES].isna().sum().to_dict()}


class CustomerFeatures(TransformerMixin, BaseEstimator):
    """Stateless feature engineering packaged inside the persisted pipeline."""

    def fit(self, X, y=None):
        clean_customers(X)
        return self

    def transform(self, X):
        frame = clean_customers(X)
        frame["tenure_months"] = frame["Account_Age_Days"] / 30.0
        frame["log_daily_usage"] = np.log1p(frame["Daily_Usage_Mins"])
        return frame[NUMERIC_FEATURES + ["Login_Frequency"]]
