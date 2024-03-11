from flwr.server.server_config import CommunicationType
from flwr.server.strategy import FedAvg
from e2e.bare.client import *

if __name__ == "__main__":
    # Launch the simulation
    hist = fl.simulation.start_simulation(
        # A function to run a _virtual_ client when required
        client_fn=client_fn,
        # Total number of clients available
        num_clients=50,
        # Specify number of FL rounds
        config=fl.server.ServerConfig(num_rounds=3, communication_type=CommunicationType.MINIO),
        # A Flower strategy
        strategy=FedAvg()
    )
