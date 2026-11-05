"""The small neural network required by Part B."""

import torch.nn as nn


class SentimentNet(nn.Module):
    def __init__(self, input_size, hidden_size=32):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 3),
        )

    def forward(self, inputs):
        # Return raw logits; CrossEntropyLoss applies the required normalization.
        return self.network(inputs)
