import flwr as fl
import torch
from models.federated_model import SimpleModel
import numpy as np

# Initialize model
model = SimpleModel()

class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return [val.detach().cpu().numpy() for val in model.parameters()]

    def set_parameters(self, parameters):
        for param, new_val in zip(model.parameters(), parameters):
            param.data = torch.tensor(new_val, dtype=param.dtype)

    def fit(self, parameters, config):
        self.set_parameters(parameters)

        # TODO: Replace with actual local training on your dataset
        # For now, we simulate a training step and return updated parameters
        # Example: one step of gradient descent, or a dummy pass

        # Here is a no-op (no actual training)
        return self.get_parameters(config), 1, {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)

        # TODO: Replace with evaluation on local test dataset
        loss = 0.0
        num_examples = 0
        return float(loss), num_examples, {}

if __name__ == "__main__":
    # Connect to the Flower server running on localhost:8080
    fl.client.start_numpy_client(server_address="localhost:8080", client=FlowerClient())
