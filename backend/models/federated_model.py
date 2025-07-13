import torch
import torch.nn as nn
import torch.nn.functional as F

class AdvancedModel(nn.Module):
    """
    A simple feedforward neural network with two hidden layers,
    batch normalization, and dropout for classification tasks.
    """

    def __init__(self, input_dim=2, hidden_dim=64, output_dim=2):
        super(AdvancedModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.dropout1 = nn.Dropout(0.3)

        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        self.dropout2 = nn.Dropout(0.3)

        self.fc3 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout1(x)
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        # Output logits for each class; apply CrossEntropyLoss externally
        return self.fc3(x)
