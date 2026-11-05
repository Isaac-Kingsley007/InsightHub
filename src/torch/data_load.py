import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets/twitter_sentiment"

def load_clean_data(file_path):

    train_data = pd.read_csv(
        file_path, 
        header=None,
        names = ['id', 'entity', 'sentiment', 'text']
    )

    train_data = train_data.dropna(subset=['text'])
    train_data = train_data.drop_duplicates(subset=['entity', 'text'])
    train_data = train_data[['text', 'sentiment']]

    return train_data

def load_train_data():
    return load_clean_data(DATA_DIR / "twitter_training.csv")

def load_validation_data():
    return load_clean_data(DATA_DIR / "twitter_validation.csv")

if __name__ == "__main__":
    train_data = load_validation_data()

    print("Train Data:")
    print(train_data.head())
    print(f"Train Data Shape: {train_data.shape}")
    print(train_data.describe())
