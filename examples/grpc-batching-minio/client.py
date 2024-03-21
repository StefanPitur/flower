from datetime import datetime

import flwr as fl
import numpy as np

from flwr.common import ConfigsRecord
from flwr.server.server_config import CommunicationType

SUBSET_SIZE = 1000
STATE_VAR = 'timestamp'


model_params = np.array([1])
objective = 5


class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return model_params

    def _record_timestamp_to_state(self):
        """Record timestamp to client's state."""
        t_stamp = datetime.now().timestamp()
        value = str(t_stamp)
        if STATE_VAR in self.context.state.configs_records.keys():
            value = self.context.state.configs_records[STATE_VAR][STATE_VAR]  # type: ignore
            value += f",{t_stamp}"

        self.context.state.configs_records[STATE_VAR] = ConfigsRecord({STATE_VAR: value})

    def _retrieve_timestamp_from_state(self):
        return self.context.state.configs_records[STATE_VAR][STATE_VAR]

    def fit(self, parameters, config):
        model_params = parameters
        model_params = [param * (objective / np.mean(param)) for param in model_params]
        self._record_timestamp_to_state()
        return model_params, 1, {STATE_VAR: self._retrieve_timestamp_from_state()}

    def evaluate(self, parameters, config):
        model_params = parameters
        loss = min(np.abs(1 - np.mean(model_params) / objective), 1)
        accuracy = 1 - loss
        self._record_timestamp_to_state()
        return loss, 1, {"accuracy": accuracy, STATE_VAR: self._retrieve_timestamp_from_state()}


if __name__ == "__main__":
    fl.client.start_client(
        server_address="localhost:8080",
        client=FlowerClient().to_client(),
        communication_type=CommunicationType.MINIO,
        minio_url="localhost:9000",
        minio_access_key="KiCzggMrhevUXL7qEBaX",
        minio_secret_key="LmFrozQ4eRAnBcjzPRAjr77HAa7Bz3YYVmkv72MT",
        minio_bucket_name="test-bucket"
    )
