from math import ceil
from typing import List, Iterator
from flwr.proto.transport_pb2 import ClientMessageChunk, ClientMessage


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

