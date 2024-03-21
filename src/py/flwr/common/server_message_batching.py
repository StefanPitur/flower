import uuid
from math import ceil
from typing import List, Iterator

from minio import Minio

from flwr.minio.utils import fetch_from_minio, persist_to_minio, delete_from_minio
from flwr.proto.transport_pb2 import ServerMessage, ServerMessageChunk, MessageMinIO


def push_server_message_to_minio(
        minio_client: Minio,
        bucket_name: str,
        server_message: ServerMessage
) -> MessageMinIO:
    source_file = str(uuid.uuid4())
    server_message_bytes = server_message.SerializeToString()
    persist_to_minio(
        client=minio_client,
        bucket_name=bucket_name,
        destination_file=source_file,
        buffer=server_message_bytes,
        buffer_size=len(server_message_bytes)
    )
    return MessageMinIO(
        bucket_name=bucket_name,
        source_file=source_file,
    )


def get_server_message_from_minio(
        minio_client: Minio,
        server_message_minio_iterator: Iterator[MessageMinIO]
) -> ServerMessage:
    server_message_minio: MessageMinIO = next(server_message_minio_iterator)
    server_message_bytes = fetch_from_minio(
        client=minio_client,
        bucket_name=server_message_minio.bucket_name,
        source_file=server_message_minio.source_file
    )

    delete_from_minio(
        client=minio_client,
        bucket_name=server_message_minio.bucket_name,
        source_file=server_message_minio.source_file
    )

    server_message = ServerMessage()
    server_message.ParseFromString(server_message_bytes)
    return server_message
