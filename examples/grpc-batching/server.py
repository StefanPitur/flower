import flwr as fl
from flwr.server.server_config import CommunicationType

if __name__ == "__main__":
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        communication_type=CommunicationType.GRPC,
        minio_url="localhost:9000",
        minio_access_key="KiCzggMrhevUXL7qEBaX",
        minio_secret_key="LmFrozQ4eRAnBcjzPRAjr77HAa7Bz3YYVmkv72MT",
        minio_bucket_name="test-bucket"
    )

# https://github.com/StefanPitur/flower/compare/46c4faa..ee7ea9d
# 46c4faa808e3af0d300a664969acbfa734c0c829
