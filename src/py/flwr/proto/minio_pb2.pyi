"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.message
import typing
import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class MessageMinIO(google.protobuf.message.Message):
    """MinIO messages"""
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    BUCKET_NAME_FIELD_NUMBER: builtins.int
    SOURCE_FILE_FIELD_NUMBER: builtins.int
    bucket_name: typing.Text
    source_file: typing.Text
    def __init__(self,
        *,
        bucket_name: typing.Text = ...,
        source_file: typing.Text = ...,
        ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["bucket_name",b"bucket_name","source_file",b"source_file"]) -> None: ...
global___MessageMinIO = MessageMinIO
