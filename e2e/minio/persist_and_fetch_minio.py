from src.py.flwr.minio.utils import *


if __name__ == "__main__":
    client = create_minio_client(
        minio_url="localhost:9000",
        access_key="KiCzggMrhevUXL7qEBaX",
        secret_key="LmFrozQ4eRAnBcjzPRAjr77HAa7Bz3YYVmkv72MT",
    )

    bucket_name = "test-bucket"
    destination_file = "test-destination-file.txt"

    buffer = "testing MinIO fetch persist and fetch".encode("utf-8")
    buffer_length = len(buffer)

    create_bucket_if_not_exists(client, bucket_name)
    persist_to_minio(client, bucket_name, destination_file, buffer, buffer_length)
    fetched_data = fetch_from_minio(client, bucket_name, destination_file, buffer_length)

    assert fetched_data == buffer
