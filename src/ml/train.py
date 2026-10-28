"""Run from the repository root: python -m src.ml.train."""

import argparse
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import train_test_split

from .data import NUMERIC_FEATURES, RAW_FEATURES, load_customers
from .models import build_models

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "artifacts"


def evaluate(model, X, y):
    predicted = model.predict(X)
    return {"accuracy": float(accuracy_score(y, predicted)),
            "precision": float(precision_score(y, predicted, zero_division=0)),
            "recall": float(recall_score(y, predicted, zero_division=0)),
            "f1": float(f1_score(y, predicted, zero_division=0)),
            "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist()}


def plot_matrix(metrics, title, path):
    display = ConfusionMatrixDisplay(np.asarray(metrics["confusion_matrix"]),
                                     display_labels=["Retained", "Churned"])
    display.plot(cmap="Blues", colorbar=False)
    display.ax_.set_title(title)
    display.figure_.tight_layout()
    display.figure_.savefig(path, dpi=150)
    plt.close(display.figure_)


def train(data_path, test_path, output_dir, seed=42, validation_size=0.2):
    frame, cleaning = load_customers(data_path)
    test, test_cleaning = load_customers(test_path)
    if set(frame["Customer_ID"]) & set(test["Customer_ID"]):
        raise ValueError("Training and test CSVs share Customer_ID values.")
    if frame["Churn"].nunique() != 2:
        raise ValueError("Training data must contain both churn classes.")
    if not 0 < validation_size < 1:
        raise ValueError("validation-size must be between 0 and 1.")
    X_train, X_valid, y_train, y_valid = train_test_split(
        frame[RAW_FEATURES], frame["Churn"], test_size=validation_size,
        stratify=frame["Churn"], random_state=seed,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    models = build_models(seed)
    validation = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        validation[name] = evaluate(model, X_valid, y_valid)
        plot_matrix(validation[name], f"{name}: validation", output_dir / f"{name}_confusion_matrix.png")
    # Selection happens before inspecting held-out test performance.
    selected = max(validation, key=lambda name: (
        validation[name]["f1"], validation[name]["recall"], validation[name]["accuracy"]
    ))
    final_model = models[selected]
    final_model.fit(frame[RAW_FEATURES], frame["Churn"])
    test_metrics = evaluate(final_model, test[RAW_FEATURES], test["Churn"])
    plot_matrix(test_metrics, f"{selected}: final test", output_dir / "test_confusion_matrix.png")
    joblib.dump(final_model, output_dir / "churn_model.pkl")

    # Grouping and filtering provide descriptive analysis of training data only.
    groups = frame.groupby("Login_Frequency", dropna=False).agg(
        customers=("Churn", "size"), churn_rate=("Churn", "mean"),
        average_daily_usage=("Daily_Usage_Mins", "mean"),
        average_account_age_days=("Account_Age_Days", "mean"),
    )
    
    groups.to_csv(output_dir / "login_frequency_summary.csv")
    ax = groups["churn_rate"].plot.bar(title="Training data: churn rate by login frequency", rot=0)
    ax.set_ylabel("Churn rate")
    ax.set_ylim(0, 1)
    ax.figure.tight_layout()
    ax.figure.savefig(output_dir / "churn_by_login_frequency.png", dpi=150)
    plt.close(ax.figure)
    summary = pd.DataFrame(validation).T.drop(columns="confusion_matrix").astype(float)
    summary.to_csv(output_dir / "validation_metrics.csv", index_label="model")
    report = {
        "seed": seed, "sklearn_version": sklearn.__version__,
        "data_path": str(Path(data_path).resolve()), "test_path": str(Path(test_path).resolve()),
        "cleaning": cleaning, "test_cleaning": test_cleaning,
        "split_rows": {"train": len(X_train), "validation": len(X_valid), "test": len(test)},
        "raw_features": RAW_FEATURES,
        "engineered_features": {"tenure_months": "Account_Age_Days / 30",
                                "log_daily_usage": "log1p(Daily_Usage_Mins)"},
        "training_churn_rate": float(frame["Churn"].mean()),
        "training_churned_mean_usage": float(frame.loc[frame["Churn"].eq(1), "Daily_Usage_Mins"].mean()),
        "majority_baseline_validation_accuracy": float(y_valid.eq(y_train.mode().iloc[0]).mean()),
        "validation": validation, "selection_rule": "highest validation F1; ties: recall, then accuracy",
        "selected_model": selected, "test": test_metrics,
        "confusion_matrix_order": "rows=actual, columns=predicted; class order [0, 1]",
        "probability_threshold": 0.5,
    }
    (output_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    missing_values = sum(cleaning["missing_predictors"].values())
    print(f"Loaded {len(frame):,} rows, {len(NUMERIC_FEATURES) + 1} features, "
          f"{missing_values:,} missing values.")
    print()
    print(f"{'Model':<22}{'Accuracy':<12}{'Precision':<12}Recall")
    display_names = {"RandomForestClassifier": "RandomForest"}
    for name, metrics in validation.items():
        print(f"{display_names.get(name, name):<22}{metrics['accuracy']:<12.2f}"
              f"{metrics['precision']:<12.2f}{metrics['recall']:.2f}")
    print()
    print(f"Selected model: {display_names.get(selected, selected)} -> saved to churn_model.pkl")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "datasets/customer_churn/train.csv")
    parser.add_argument("--test-data", type=Path, default=ROOT / "datasets/customer_churn/test_.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-size", type=float, default=0.2)
    args = parser.parse_args()
    try:
        train(args.data, args.test_data, args.output_dir, args.seed, args.validation_size)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(1, f"Training failed: {exc}\n")


if __name__ == "__main__":
    main()
