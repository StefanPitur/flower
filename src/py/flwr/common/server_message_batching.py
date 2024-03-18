from math import ceil
from typing import List, Iterator

from flwr.proto.transport_pb2 import ServerMessage, ServerMessageChunk


def batch_server_message(server_message: ServerMessage, chunk_size: int) -> List[ServerMessageChunk]:
    server_message_bytes = server_message.SerializeToString()
    server_message_bytes_len = len(server_message_bytes)

    num_chunks = ceil(server_message_bytes_len / chunk_size)
    server_message_chunks: List[ServerMessageChunk] = []
    for chunk_num in range(1, num_chunks + 1):
        chunk_bytes = server_message_bytes[
                      (chunk_num - 1) * chunk_size:
                      min(chunk_num * chunk_size, server_message_bytes_len)
        ]
        server_message_chunks.append(ServerMessageChunk(
            batch_number=chunk_num,
            num_batches=num_chunks,
            server_message_chunk=chunk_bytes
        ))

    return server_message_chunks


def get_server_message_from_batches(server_message_batches: Iterator[ServerMessageChunk]) -> ServerMessage:
    chunk_num = 0
    server_message_bytes = b""
    while True:
        chunk_num += 1
        server_message_batch: ServerMessageChunk = next(server_message_batches)
        server_message_bytes += server_message_batch.server_message_chunk
        if chunk_num == server_message_batch.num_batches:
            break

    server_message = ServerMessage()
    server_message.ParseFromString(server_message_bytes)
    return server_message
