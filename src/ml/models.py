"""Comparable classical models with preprocessing fitted only on training rows."""

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .data import CustomerFeatures, NUMERIC_FEATURES


def build_models(seed=42):
    models = {}
    estimators = {
        "LogisticRegression": LogisticRegression(max_iter=2000, random_state=seed),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=3, random_state=seed, n_jobs=-1
        ),
    }
    for name, estimator in estimators.items():
        numeric_steps = [("impute", SimpleImputer(strategy="median", keep_empty_features=True))]
        if name == "LogisticRegression":
            numeric_steps.append(("scale", StandardScaler()))
        preprocessing = ColumnTransformer([
            ("numeric", Pipeline(numeric_steps), NUMERIC_FEATURES),
            ("login", Pipeline([
                ("impute", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
                ("encode", OneHotEncoder(
                    categories=[["Daily", "Weekly", "Rarely"]], handle_unknown="ignore"
                )),
            ]), ["Login_Frequency"]),
        ])
        models[name] = Pipeline([
            ("features", CustomerFeatures()), ("preprocess", preprocessing), ("model", estimator)
        ])
    return models
