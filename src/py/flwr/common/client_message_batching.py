from math import ceil
from typing import List, Iterator
from flwr.proto.transport_pb2 import ClientMessageChunk, ClientMessage


def get_client_message_chunk_size() -> int:
    return len(ClientMessageChunk(client_message_chunk=b"").SerializeToString()) + 16


def batch_client_message(client_message: ClientMessage, chunk_size: int) -> List[ClientMessageChunk]:
    print(f"Sending chunk of size {chunk_size} to")
    client_message_bytes = client_message.SerializeToString()
    client_message_bytes_len = len(client_message_bytes)

    num_chunks = ceil(client_message_bytes_len / chunk_size)
    client_message_chunks: List[ClientMessageChunk] = []
    for chunk_num in range(1, num_chunks + 1):
        chunk_bytes = client_message_bytes[
                      (chunk_num - 1) * chunk_size:
                      min(chunk_num * chunk_size, client_message_bytes_len)
                      ]

        cm = ClientMessageChunk(
            batch_number=chunk_num,
            num_batches=num_chunks,
            client_message_chunk=chunk_bytes
        )

        print(f"cm size = {len(cm.SerializeToString())}")

        client_message_chunks.append(cm)

    return client_message_chunks


def get_client_message_from_batches(client_message_batches: Iterator[ClientMessageChunk]) -> ClientMessage:
    chunk_num = 0
    client_message_bytes = b""
    while True:
        chunk_num += 1
        client_message_batch: ClientMessageChunk = next(client_message_batches)
        client_message_bytes += client_message_batch.client_message_chunk
        if chunk_num == client_message_batch.num_batches:
            break

    client_message = ClientMessage()
    client_message.ParseFromString(client_message_bytes)
    return client_message

