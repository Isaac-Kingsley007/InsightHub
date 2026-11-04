# Churn prediction

Estimates whether a customer may leave using account age, login frequency, and
daily usage. `1` means predicted churn; `0` means predicted retention. Estimates
support review, not guaranteed outcomes. See the [root guide](../../README.md)
for dependencies and CSV locations. Run commands from the project root.

## Train and predict

```powershell
python -m src.ml.train
python -m src.ml.predict --data datasets/customer_churn/test_.csv --output src/ml/artifacts/test_predictions.csv
```

Training compares Logistic Regression and Random Forest using an 80/20 stratified
split of `train.csv`. Highest validation F1 wins (ties: recall, then accuracy).
The selected pipeline is refitted on all training rows and evaluated once on
`test_.csv`. Never use test scores to tune the model. Options: `--data`,
`--test-data`, `--output-dir`, `--seed`, and `--validation-size`.

The web prediction form uses `POST /predict-churn`. API request:

```json
{"Account_Age_Days": 790, "Login_Frequency": "Weekly", "Daily_Usage_Mins": 28}
```

Returns `predicted_churn` and `churn_probability` (0-1), using a 0.5 classification
threshold. All three fields are required; numbers must be nonnegative and login
frequency must be Daily, Weekly, or Rarely. Invalid inputs return 422.

## Features and saved files

The pipeline derives `tenure_months = Account_Age_Days / 30` (replaces raw age)
and `log_daily_usage = log1p(Daily_Usage_Mins)` (alongside raw usage). Login
frequency is one-hot encoded; Logistic Regression numeric inputs are scaled.
Training-only medians/modes fill missing predictors. Identifiers, support text,
and the target `Churn` are not model inputs. Duplicate rows are removed;
invalid labels, duplicate remaining IDs, and train/test ID overlap are rejected.

`src/ml/artifacts/` contains:

- `churn_model.pkl`: Joblib pipeline, including preprocessing and feature creation.
- `metrics.json` and `validation_metrics.csv`: cleaning/split details and scores.
- Confusion-matrix charts, login-frequency summary CSV, and churn-rate chart.

Terminal output follows the project example's format with actual validation
scores. Full F1, confusion matrices and final test results stay in the reports.
Matrices use rows=actual, columns=predicted, ordered [0, 1]: `[[TN, FP], [FN, TP]]`.

## Maintenance and debugging

The API loads the model lazily and caches it per process. After retraining,
restart FastAPI. A missing/unloadable model returns 503; prediction failures return
500. The API expects the default artifact path even if training used `--output-dir`.
Load only trusted Joblib files, using compatible package versions.

The model and customer prediction exports are Git-ignored; train after a fresh
checkout. CSV inference preserves Customer_ID when present and accepts unlabeled
rows. No spending or churn-date features exist in this dataset.

```powershell
python -m unittest src.ml.test_workflow src.api.test_predict_churn
```
