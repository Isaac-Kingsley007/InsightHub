# Part B: PyTorch sentiment classifier

Classifies messages as positive, neutral, or negative using bag-of-words tensors
and a small `Linear -> ReLU -> Linear` network. Training uses CrossEntropyLoss,
Adam, and a manual mini-batch loop; evaluation reports held-out accuracy.

## Run

From the project root with the existing venv activated:

```powershell
python -m src.torch.train
```

Uses your `data_load.py` and these labeled files:

```text
datasets/twitter_sentiment/twitter_training.csv
datasets/twitter_sentiment/twitter_validation.csv
```

These are headerless CSVs: `id, entity, sentiment, text`. This is a Twitter
sentiment benchmark, not customer support data; accuracy on it does not establish
accuracy on support messages. It follows your supplied loader. The PDF describes
support messages, so evaluating on labeled support messages would be the next
step for that domain. Churn labels are not used as sentiment labels.

`Irrelevant` and other labels are excluded rather than relabeled as neutral.
Empty messages, repeated texts and ambiguous labels within each set are removed.
Texts appearing in the held-out set are removed from training, case-insensitively.
Only training messages fit the vocabulary; held-out messages never update weights.

Defaults: 10 epochs, batch size 256, vocabulary up to 3,000 words, seed 42.
Override with `--epochs`, `--batch-size`, `--max-features`, `--seed`, or
`--output-dir`. Only a batch is converted from sparse counts to dense tensors.

## Files and maintenance

- `model.py`: `SentimentNet`; raw logits, three output classes.
- `train.py`: training, evaluation, and artifact saving.
- `artifacts/sentiment_model.pth`: weights, dimensions, and label mapping.
- `artifacts/sentiment_vectorizer.pkl`: training vocabulary.
- `artifacts/metrics.json`: held-out accuracy, per-class scores, losses and settings.
- `main.py`: your reference example; not used by this training workflow.

Label mapping: Positive=0, Neutral=1, Negative=2. Retrain after changes to vocabulary
or labels; use the saved vectorizer with its corresponding checkpoint. Load only
trusted artifacts. This training exercise is separate from Gemini `/analyze`.
Run as `python -m src.torch.train`, not from inside this folder, to avoid shadowing
the installed `torch` package.

Checks: `python -m unittest src.torch.test_sentiment`.
