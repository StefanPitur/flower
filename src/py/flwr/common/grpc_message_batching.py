from math import ceil
from typing import List, Type, Iterator

import google.protobuf.message


def batch_grpc_message(
        message: google.protobuf.message.Message,
        batch_size: int,
        batch_message_type: Type[google.protobuf.message.Message],
        batch_message_header_size: int,
) -> List[google.protobuf.message.Message]:
    batch_size -= batch_message_header_size

    message_bytes = message.SerializeToString()
    message_bytes_len = len(message_bytes)

    num_batches = ceil(message_bytes_len / batch_size)
    batch_messages: List[batch_message_type] = []
    for batch_num in range(num_batches):
        batch_message_bytes = message_bytes[
            batch_num * batch_size:
            min((batch_num + 1) * batch_size, message_bytes_len)
        ]

        batch_messages.append(batch_message_type(message_batch_bytes=batch_message_bytes))

    batch_messages.append(batch_message_type())
    return batch_messages


def get_message_from_batches(
        batch_messages_iterator: Iterator[google.protobuf.message.Message],
        message_type: Type[google.protobuf.message.Message]
) -> google.protobuf.message.Message:
    message_batches_bytes = b""
    while True:
        batch_message = next(batch_messages_iterator)
        if len(batch_message.message_batch_bytes) == 0:
            break
        message_batches_bytes += batch_message.message_batch_bytes

    message = message_type()
    message.ParseFromString(message_batches_bytes)
    return message
