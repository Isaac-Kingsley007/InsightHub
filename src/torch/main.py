
import random
from pathlib import Path

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

# Reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# 0 = Positive, 1 = Neutral, 2 = Negative
data = [
    ("The support team was very helpful", 0),
    ("I love using this application", 0),
    ("The dashboard works perfectly", 0),
    ("Your service is excellent", 0),
    ("The onboarding experience was amazing", 0),
    ("Everything is working smoothly", 0),
    ("The new features are fantastic", 0),
    ("I am happy with the support", 0),
    ("The application is fast and reliable", 0),
    ("My issue was resolved quickly", 0),
    ("The customer service is wonderful", 0),
    ("I really enjoy this product", 0),
    ("The latest update improved performance", 0),
    ("Your team did a great job", 0),
    ("I am satisfied with my subscription", 0),

    ("My subscription renewed today", 1),
    ("I updated my account details", 1),
    ("The invoice was generated", 1),
    ("My payment is scheduled for tomorrow", 1),
    ("I received the monthly report", 1),
    ("The meeting is scheduled for Monday", 1),
    ("I logged into my account", 1),
    ("The subscription expires next month", 1),
    ("I changed my profile picture", 1),
    ("The system sent a notification", 1),
    ("I downloaded the invoice", 1),
    ("My account was created yesterday", 1),
    ("The report contains five pages", 1),
    ("I submitted the registration form", 1),
    ("The billing cycle starts tomorrow", 1),

    ("The application keeps crashing", 2),
    ("I am unhappy with the service", 2),
    ("The dashboard is extremely slow", 2),
    ("The support team was unhelpful", 2),
    ("My payment failed repeatedly", 2),
    ("The latest update broke everything", 2),
    ("I cannot access my account", 2),
    ("The application has too many bugs", 2),
    ("I am frustrated with this product", 2),
    ("The customer service is terrible", 2),
    ("The website is not working", 2),
    ("My issue remains unresolved", 2),
    ("The system frequently freezes", 2),
    ("I regret purchasing this subscription", 2),
    ("The app takes forever to load", 2),
]

messages = [message for message, label in data]
labels = [label for message, label in data]

# Split BEFORE fitting the vectorizer to avoid data leakage
X_train, X_test, y_train, y_test = train_test_split(
    messages,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels,
)

# Bag-of-Words representation
vectorizer = CountVectorizer()

X_train_bow = vectorizer.fit_transform(X_train)
X_test_bow = vectorizer.transform(X_test)

X_train_tensor = torch.tensor(
    X_train_bow.toarray(), dtype=torch.float32
)
X_test_tensor = torch.tensor(
    X_test_bow.toarray(), dtype=torch.float32
)

y_train_tensor = torch.tensor(y_train, dtype=torch.long)
y_test_tensor = torch.tensor(y_test, dtype=torch.long)


# Neural network: Linear -> ReLU -> Linear
class SentimentNet(nn.Module):
    def __init__(self, input_size):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 16),
            nn.ReLU(),
            nn.Linear(16, 3),
        )

    def forward(self, x):
        return self.network(x)


model = SentimentNet(X_train_tensor.shape[1])

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

# Manual training loop
epochs = 100

for epoch in range(epochs):
    model.train()

    optimizer.zero_grad()

    outputs = model(X_train_tensor)
    loss = criterion(outputs, y_train_tensor)

    loss.backward()
    optimizer.step()

    if (epoch + 1) % 10 == 0:
        print(
            f"Epoch {epoch + 1}/{epochs} | "
            f"Loss: {loss.item():.4f}"
        )

# Evaluate on held-out test data
model.eval()

with torch.no_grad():
    test_outputs = model(X_test_tensor)
    predictions = torch.argmax(test_outputs, dim=1)

accuracy = accuracy_score(
    y_test_tensor.numpy(),
    predictions.numpy(),
)

print(f"\nTest Accuracy: {accuracy:.2%}")
print(
    classification_report(
        y_test,
        predictions.numpy(),
        labels=[0, 1, 2],
        target_names=["Positive", "Neutral", "Negative"],
        zero_division=0,
    )
)

# Save model and fitted vectorizer
output_dir = Path("models")
output_dir.mkdir(exist_ok=True)

torch.save(
    {
        "model_state_dict": model.state_dict(),
        "input_size": X_train_tensor.shape[1],
    },
    output_dir / "sentiment_model.pth",
)

joblib.dump(
    vectorizer,
    output_dir / "sentiment_vectorizer.pkl",
)

print("Model and vocabulary saved successfully!")
