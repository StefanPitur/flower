from typing import Iterator, Type

import google.protobuf.message
from minio import Minio

from flwr.minio.utils import persist_to_minio, fetch_from_minio, delete_from_minio


def push_message_to_minio(
        minio_client: Minio,
        bucket_name: str,
        source_file: str,
        message: google.protobuf.message.Message,
        minio_message_type: Type[google.protobuf.message.Message]
) -> google.protobuf.message.Message:
    message_bytes = message.SerializeToString()

    persist_to_minio(
        client=minio_client,
        bucket_name=bucket_name,
        destination_file=source_file,
        buffer=message_bytes,
        buffer_size=len(message_bytes)
    )
    return minio_message_type(
        bucket_name=bucket_name,
        source_file=source_file,
    )


def get_message_from_minio(
        minio_client: Minio,
        minio_message_iterator: Iterator[google.protobuf.message.Message],
        message_type: Type[google.protobuf.message.Message]
) -> google.protobuf.message.Message:

    minio_message = next(minio_message_iterator)
    message_bytes = fetch_from_minio(
        client=minio_client,
        bucket_name=minio_message.bucket_name,
        source_file=minio_message.source_file
    )

    delete_from_minio(
        client=minio_client,
        bucket_name=minio_message.bucket_name,
        source_file=minio_message.source_file
    )

    message = message_type()
    message.ParseFromString(message_bytes)
    return message
