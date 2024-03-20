from math import ceil
from typing import List, Iterator

from minio import Minio

from flwr.minio.utils import persist_to_minio, fetch_from_minio, delete_from_minio
from flwr.proto.transport_pb2 import ClientMessageChunk, ClientMessage, MessageMinIO

CLIENT_MESSAGE_CHUNK_HEADER_SIZE = 2


def get_client_message_chunk_size() -> int:
    return CLIENT_MESSAGE_CHUNK_HEADER_SIZE


def batch_client_message(client_message: ClientMessage, chunk_size: int) -> List[ClientMessageChunk]:
    chunk_size -= get_client_message_chunk_size()

    client_message_bytes = client_message.SerializeToString()
    client_message_bytes_len = len(client_message_bytes)

    num_chunks = ceil(client_message_bytes_len / chunk_size)
    client_message_chunks: List[ClientMessageChunk] = []
    for chunk_num in range(num_chunks):
        chunk_bytes = client_message_bytes[
                        chunk_num * chunk_size:
                        min((chunk_num + 1) * chunk_size, client_message_bytes_len)
        ]

        client_message_chunks.append(ClientMessageChunk(client_message_chunk=chunk_bytes))

    client_message_chunks.append(ClientMessageChunk())
    return client_message_chunks


def get_client_message_from_batches(client_message_batches: Iterator[ClientMessageChunk]) -> ClientMessage:
    client_message_bytes = b""
    while True:
        client_message_batch: ClientMessageChunk = next(client_message_batches)
        if len(client_message_batch.client_message_chunk) == 0:
            break
        client_message_bytes += client_message_batch.client_message_chunk

    client_message = ClientMessage()
    client_message.ParseFromString(client_message_bytes)
    return client_message


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

    client_message = ClientMessage()
    client_message.ParseFromString(client_message_bytes)
    return client_message
