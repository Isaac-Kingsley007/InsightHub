
"""Train Part B: python -m src.torch.train (run from the project root)."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score, classification_report

from .data_load import load_train_data, load_validation_data
from .model import SentimentNet

LABELS = {"Positive": 0, "Neutral": 1, "Negative": 2}
OUTPUT_DIR = Path(__file__).resolve().parent / "artifacts"


def prepare_sentiment_data(frame):
    """Keep the three required classes and unique, nonempty messages."""
    frame = frame.dropna(subset=["text", "sentiment"]).copy()
    frame["text"] = frame["text"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    frame["sentiment"] = frame["sentiment"].astype(str).str.strip().str.capitalize()
    frame = frame.loc[frame["sentiment"].isin(LABELS) & frame["text"].ne("")].copy()
    frame["text_key"] = frame["text"].str.casefold()
    # The same text can have different entity-dependent labels in this dataset.
    # Drop ambiguous texts rather than choosing a label arbitrarily.
    conflicts = frame.groupby("text_key")["sentiment"].transform("nunique").gt(1)
    return frame.loc[~conflicts].drop_duplicates("text_key").reset_index(drop=True)


def batches(matrix, labels, batch_size, shuffle=False):
    indices = torch.randperm(matrix.shape[0]).numpy() if shuffle else np.arange(matrix.shape[0])
    for start in range(0, len(indices), batch_size):
        selected = indices[start:start + batch_size]
        # Densify only one batch, not the entire bag-of-words dataset.
        yield (torch.from_numpy(matrix[selected].toarray().astype(np.float32)),
               torch.tensor(labels[selected], dtype=torch.long))


def train(epochs=10, batch_size=256, max_features=3000, seed=42, output_dir=OUTPUT_DIR):
    if epochs < 1 or batch_size < 1 or max_features < 1:
        raise ValueError("epochs, batch-size, and max-features must be positive.")
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    training = prepare_sentiment_data(load_train_data())
    validation = prepare_sentiment_data(load_validation_data())
    overlap = training["text_key"].isin(validation["text_key"])
    overlap_removed = int(overlap.sum())
    training = training.loc[~overlap].reset_index(drop=True)
    if training.empty or validation.empty or set(training.sentiment) != set(LABELS):
        raise ValueError("Need nonempty training/held-out data and all three training classes.")

    vectorizer = CountVectorizer(max_features=max_features, dtype=np.float32)
    X_train = vectorizer.fit_transform(training["text"])
    X_valid = vectorizer.transform(validation["text"])
    y_train = training["sentiment"].map(LABELS).to_numpy()
    y_valid = validation["sentiment"].map(LABELS).to_numpy()
    model = SentimentNet(X_train.shape[1])
    loss_function = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    print(f"Training: {len(training):,} messages | Held-out: {len(validation):,} messages | Vocabulary: {X_train.shape[1]:,}")
    print(f"Removed {overlap_removed:,} training messages overlapping the held-out set.")
    losses = []
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for inputs, targets in batches(X_train, y_train, batch_size, shuffle=True):
            optimizer.zero_grad()
            loss = loss_function(model(inputs), targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(targets)
        losses.append(total_loss / len(training))
        if epoch == 1 or epoch % 2 == 0 or epoch == epochs:
            print(f"Epoch {epoch}/{epochs} | Loss: {losses[-1]:.4f}")

    model.eval()
    predictions = []
    with torch.no_grad():
        for inputs, _ in batches(X_valid, y_valid, batch_size):
            predictions.extend(model(inputs).argmax(dim=1).tolist())
    accuracy = float(accuracy_score(y_valid, predictions))
    report = classification_report(y_valid, predictions, labels=list(LABELS.values()),
                                   target_names=list(LABELS), zero_division=0, output_dict=True)
    print(f"\nHeld-out accuracy: {accuracy:.2%}")
    print(classification_report(y_valid, predictions, labels=list(LABELS.values()),
                                target_names=list(LABELS), zero_division=0))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state_dict": model.state_dict(), "input_size": X_train.shape[1],
                "hidden_size": 32, "labels": LABELS}, output_dir / "sentiment_model.pth")
    joblib.dump(vectorizer, output_dir / "sentiment_vectorizer.pkl")
    metrics = {"accuracy": accuracy, "classification_report": report, "epoch_losses": losses,
               "training_rows": len(training), "held_out_rows": len(validation),
               "overlap_removed": overlap_removed, "vocabulary_size": X_train.shape[1],
               "seed": seed, "epochs": epochs, "batch_size": batch_size,
               "torch_version": torch.__version__, "labels": LABELS}
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved model, vocabulary, and metrics to {output_dir}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--max-features", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    try:
        train(args.epochs, args.batch_size, args.max_features, args.seed, args.output_dir)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(1, f"Training failed: {exc}\n")


if __name__ == "__main__":
    main()
