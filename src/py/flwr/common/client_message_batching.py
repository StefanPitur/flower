from math import ceil
from typing import List, Iterator

from minio import Minio

from flwr.minio.utils import persist_to_minio, fetch_from_minio, delete_from_minio
from flwr.proto.transport_pb2 import ClientMessageChunk, ClientMessage, MessageMinIO


def push_client_message_to_minio(
        minio_client: Minio,
        bucket_name: str,
        source_file: str,
        client_message: ClientMessage
) -> MessageMinIO:
    client_message_bytes = client_message.SerializeToString()
    persist_to_minio(
        client=minio_client,
        bucket_name=bucket_name,
        destination_file=source_file,
        buffer=client_message_bytes,
        buffer_size=len(client_message_bytes)
    )
    return MessageMinIO(
        bucket_name=bucket_name,
        source_file=source_file,
    )


def get_client_message_from_minio(
        minio_client: Minio,
        client_message_minio_iterator: Iterator[MessageMinIO]
) -> ClientMessage:
    client_message_minio: MessageMinIO = next(client_message_minio_iterator)
    client_message_bytes = fetch_from_minio(
        client=minio_client,
        bucket_name=client_message_minio.bucket_name,
        source_file=client_message_minio.source_file
    )

    delete_from_minio(
        client=minio_client,
        bucket_name=client_message_minio.bucket_name,
        source_file=client_message_minio.source_file
    )

    client_message = ClientMessage()
    client_message.ParseFromString(client_message_bytes)
    return client_message
