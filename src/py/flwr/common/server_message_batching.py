import uuid
from math import ceil
from typing import List, Iterator

from minio import Minio

from flwr.minio.utils import fetch_from_minio, persist_to_minio, delete_from_minio
from flwr.proto.transport_pb2 import ServerMessage, ServerMessageChunk, MessageMinIO

SERVER_MESSAGE_CHUNK_HEADER_SIZE = 2


def get_server_message_chunk_size() -> int:
    return SERVER_MESSAGE_CHUNK_HEADER_SIZE


def batch_server_message(server_message: ServerMessage, chunk_size: int) -> List[ServerMessageChunk]:
    chunk_size -= get_server_message_chunk_size()

    server_message_bytes = server_message.SerializeToString()
    server_message_bytes_len = len(server_message_bytes)

    num_chunks = ceil(server_message_bytes_len / chunk_size)
    server_message_chunks: List[ServerMessageChunk] = []
    for chunk_num in range(num_chunks):
        chunk_bytes = server_message_bytes[
                      chunk_num * chunk_size:
                      min((chunk_num + 1) * chunk_size, server_message_bytes_len)
        ]
        server_message_chunks.append(ServerMessageChunk(
            server_message_chunk=chunk_bytes
        ))

    server_message_chunks.append(ServerMessageChunk())
    return server_message_chunks


def get_server_message_from_batches(server_message_batches: Iterator[ServerMessageChunk]) -> ServerMessage:
    server_message_bytes = b""
    while True:
        server_message_batch: ServerMessageChunk = next(server_message_batches)
        if len(server_message_batch.server_message_chunk) == 0:
            break
        server_message_bytes += server_message_batch.server_message_chunk

    server_message = ServerMessage()
    server_message.ParseFromString(server_message_bytes)
    return server_message


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

    server_message = ServerMessage()
    server_message.ParseFromString(server_message_bytes)
    return server_message
