from math import ceil
from typing import List, Iterator

from flwr.proto.transport_pb2 import ServerMessage, ServerMessageChunk


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
