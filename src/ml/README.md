# Part A — customer churn

Run commands from the repository root with the existing virtual environment.

```powershell
.\.venv\Scripts\python.exe -m src.ml.train
.\.venv\Scripts\python.exe -m src.ml.predict --data datasets/customer_churn/test_.csv --output src/ml/artifacts/test_predictions.csv
.\.venv\Scripts\python.exe -m unittest src.ml.test_workflow
```

Training accepts `--data`, `--test-data`, `--output-dir`, `--seed`, and
`--validation-size`. It uses an 80/20 stratified split of `train.csv` to compare
Logistic Regression and Random Forest. The separate `test_.csv` is reserved for
one final evaluation of the selected model, after refitting on all training rows.
Choose by validation F1, with recall and accuracy as tie breakers. This balances
finding churners with avoiding false alarms. The default decision threshold is 0.5.
The test scores must not be used to tune the model.

## Data and features

Numeric values must be nonnegative and finite. Login frequency is normalized to
Daily, Weekly, or Rarely; unknown observed categories fail validation. Empty
predictors are imputed using training-only medians/modes. Missing or invalid labels
fail validation. Exact duplicate rows are removed; remaining duplicate customer
IDs and IDs shared between train and test are rejected.

The model consumes raw `Account_Age_Days`, `Login_Frequency`, and
`Daily_Usage_Mins`. Its pipeline derives `tenure_months = Account_Age_Days / 30`
and `log_daily_usage = log1p(Daily_Usage_Mins)`. Raw account age is replaced by
tenure; daily usage and its log transformation are both included. Login frequency
is one-hot encoded; numeric features are scaled for Logistic Regression.
Imputation, encoding, and scaling are fitted inside each pipeline.

`Churn` is the target (1 = churn, 0 = retained). Customer ID, name, and email are
excluded from predictors. Support messages are retained in the source data for
Part B, but excluded from this baseline. There is no spending or churn-date field:
monthly spending and date-specific churn counts cannot be inferred.

Training-only Pandas filtering and grouping produce descriptive summaries of
churn and usage by login frequency. These summaries are not target-derived model
features. No artificial spending fields or sentiment labels are generated.

## Outputs

`artifacts/` contains:

- `churn_model.pkl`: full refitted pipeline, including feature engineering (Joblib format).
- `metrics.json`: cleaning counts, split sizes, model selection rule, validation
  metrics for both models, final test metrics, and scikit-learn version.
- `validation_metrics.csv`: accuracy, precision, recall, and F1 for both models.
- Confusion-matrix PNGs for both validation models and the final test model.
- `login_frequency_summary.csv` and `churn_by_login_frequency.png`.

Confusion matrices use rows = actual and columns = predicted, ordered [0, 1]:
`[[true negatives, false positives], [false negatives, true positives]]`.

The terminal output follows the PDF page 3 example: loaded training rows, four
engineered input features before one-hot encoding, missing raw predictor cells
before imputation, an accuracy/precision/recall comparison rounded to two decimal
places, and the selected model filename. Table scores are validation scores;
F1, confusion matrices, and final held-out test scores remain in the saved reports.
Counts, scores, and the winning model reflect the actual run, rather than the
illustrative numbers in the PDF. The saved model is in the output directory
(`src/ml/artifacts` by default).

`predict_customers` in `src.ml.predict` can be reused by the later API. It accepts
unlabeled rows and returns predicted churn plus its probability, preserving
Customer_ID when provided. Run from the repository root so persisted custom
transformer imports resolve. Only load trusted Joblib artifacts, and use the same
package versions for training and serving. The model and per-customer prediction
exports are ignored by the local Git rules; regenerate them using the commands.

The existing environment and Git repository are reused. The assignment also
requires incremental commits and a GitHub repository named `insighthub`; publishing
is a separate repository setup step. No Git remote was configured at implementation.
