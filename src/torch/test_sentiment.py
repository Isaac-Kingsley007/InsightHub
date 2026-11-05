"""Offline checks: python -m unittest src.torch.test_sentiment."""

import io
import unittest

import numpy as np
import pandas as pd
import torch
from scipy.sparse import csr_matrix

from .model import SentimentNet
from .train import batches, prepare_sentiment_data


class SentimentTests(unittest.TestCase):
    def test_cleaning_preserves_only_unambiguous_three_class_messages(self):
        frame = pd.DataFrame({"text": [" good ", "GOOD", "bad", "plain", "ignore", " ", "conflict", "CONFLICT"],
                              "sentiment": ["Positive", "Positive", "Negative", "Neutral", "Irrelevant", "Neutral", "Positive", "Negative"]})
        result = prepare_sentiment_data(frame)
        self.assertEqual(set(result.text_key), {"good", "bad", "plain"})

    def test_batches_keep_inputs_and_targets_aligned(self):
        matrix = csr_matrix(np.arange(15).reshape(5, 3))
        labels = np.arange(5)
        result = list(batches(matrix, labels, 2))
        self.assertEqual([len(targets) for _, targets in result], [2, 2, 1])
        self.assertEqual(result[0][0].dtype, torch.float32)
        self.assertEqual(result[0][1].dtype, torch.long)
        np.testing.assert_array_equal(torch.cat([inputs for inputs, _ in result]).numpy(), matrix.toarray())

    def test_training_step_and_checkpoint_round_trip(self):
        torch.manual_seed(42)
        model = SentimentNet(4)
        inputs = torch.ones(3, 4)
        targets = torch.tensor([0, 1, 2])
        original = model.network[0].weight.detach().clone()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        loss = torch.nn.CrossEntropyLoss()(model(inputs), targets)
        loss.backward()
        optimizer.step()
        self.assertFalse(torch.equal(original, model.network[0].weight))
        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)
        buffer.seek(0)
        restored = SentimentNet(4)
        restored.load_state_dict(torch.load(buffer, weights_only=True))
        torch.testing.assert_close(restored(inputs), model(inputs))
        self.assertEqual(model(inputs).shape, (3, 3))


if __name__ == "__main__":
    unittest.main()
