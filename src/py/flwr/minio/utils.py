from io import BytesIO
from minio import Minio
from tqdm import tqdm


def create_minio_client(minio_url: str, access_key: str, secret_key: str) -> Minio:
    return Minio(
        endpoint=minio_url,
        access_key=access_key,
        secret_key=secret_key,
        secure=False
    )


def create_bucket_if_not_exists(client: Minio, bucket_name: str) -> None:
    if not (client.bucket_exists(bucket_name)):
        client.make_bucket(bucket_name)


def persist_to_minio(client: Minio, bucket_name: str, destination_file: str, buffer: bytes, buffer_size: int) -> None:
    client.put_object(
        bucket_name=bucket_name,
        object_name=destination_file,
        data=BytesIO(buffer),
        length=buffer_size
    )


def fetch_from_minio(
    client: Minio, bucket_name: str, source_file: str, buffer_size: int, chunk_size: int = 1024 ** 2
) -> bytearray:
    result = bytearray()
    for offset in tqdm(range(0, buffer_size, chunk_size), desc="Fetching data from MinIO"):
        try:
            response = client.get_object(
                bucket_name=bucket_name,
                object_name=source_file,
                offset=offset,
                length=chunk_size
            )
            result.extend(response.read())
        finally:
            response.close()
            response.release_conn()
    return result
