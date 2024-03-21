# Copyright 2020 Flower Labs GmbH. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Contextmanager for a gRPC streaming channel to the Flower server."""


import uuid
from contextlib import contextmanager
from logging import DEBUG
from pathlib import Path
from queue import Queue
from typing import Callable, Iterator, Optional, Tuple, Union, cast

from minio import Minio

from flwr.common import (
    GRPC_MAX_MESSAGE_LENGTH,
    ConfigsRecord,
    Message,
    Metadata,
    RecordSet,
)
from flwr.common import recordset_compat as compat
from flwr.common import serde
from flwr.common.client_message_batching import push_client_message_to_minio
from flwr.common.constant import (
    MESSAGE_TYPE_EVALUATE,
    MESSAGE_TYPE_FIT,
    MESSAGE_TYPE_GET_PARAMETERS,
    MESSAGE_TYPE_GET_PROPERTIES, CLIENT_MESSAGE_BATCH_HEADER_SIZE,
)
from flwr.common.grpc import create_channel
from flwr.common.grpc_message_batching import batch_grpc_message, get_message_from_batches
from flwr.common.logger import log
from flwr.common.server_message_batching import get_server_message_from_minio
from flwr.proto.transport_pb2 import (  # pylint: disable=E0611
    ClientMessage,
    Reason,
    ServerMessageChunk, MessageMinIO, ClientMessageChunk, ServerMessage,
)
from flwr.proto.transport_pb2_grpc import FlowerServiceStub  # pylint: disable=E0611
from flwr.server.server_config import CommunicationType


# The following flags can be uncommented for debugging. Other possible values:
# https://github.com/grpc/grpc/blob/master/doc/environment_variables.md
# import os
# os.environ["GRPC_VERBOSITY"] = "debug"
# os.environ["GRPC_TRACE"] = "tcp,http"


def on_channel_state_change(channel_connectivity: str) -> None:
    """Log channel connectivity."""
    log(DEBUG, channel_connectivity)


@contextmanager
def grpc_connection(  # pylint: disable=R0915
    server_address: str,
    insecure: bool,
    max_message_length: int = GRPC_MAX_MESSAGE_LENGTH,
    root_certificates: Optional[Union[bytes, str]] = None,
    communication_type: CommunicationType = CommunicationType.GRPC,
    minio_client: Optional[Minio] = None,
    minio_bucket_name: Optional[str] = None,
) -> Iterator[
    Tuple[
        Callable[[], Optional[Message]],
        Callable[[Message], None],
        Optional[Callable[[], None]],
        Optional[Callable[[], None]],
    ]
]:
    """Establish a gRPC connection to a gRPC server.

    Parameters
    ----------
    server_address : str
        The IPv4 or IPv6 address of the server. If the Flower server runs on the same
        machine on port 8080, then `server_address` would be `"0.0.0.0:8080"` or
        `"[::]:8080"`.
    max_message_length : int
        The maximum length of gRPC messages that can be exchanged with the Flower
        server. The default should be sufficient for most models. Users who train
        very large models might need to increase this value. Note that the Flower
        server needs to be started with the same value
        (see `flwr.server.start_server`), otherwise it will not know about the
        increased limit and block larger messages.
        (default: 536_870_912, this equals 512MB)
    root_certificates : Optional[bytes] (default: None)
        The PEM-encoded root certificates as a byte string or a path string.
        If provided, a secure connection using the certificates will be
        established to an SSL-enabled Flower server.
    communication_type : CommunicationType (default: CommunicationType.GRPC)
        Used to determine whether to use gRPC communication or MinIO.
    minio_client : Optional[Minio] (default: None)
        Used when communicating via MinIO to connect to the correct instance.
    minio_bucket_name : Optional[str] (default: None)
        Used when communicating via MinIO where you want to put the data in a specific bucket.

    Returns
    -------
    receive, send : Callable, Callable

    Examples
    --------
    Establishing a SSL-enabled connection to the server:

    >>> from pathlib import Path
    >>> with grpc_connection(
    >>>     server_address,
    >>>     max_message_length=max_message_length,
    >>>     root_certificates=Path("/crts/root.pem").read_bytes(),
    >>> ) as conn:
    >>>     receive, send = conn
    >>>     server_message = receive()
    >>>     # do something here
    >>>     send(client_message)
    """
    if isinstance(root_certificates, str):
        root_certificates = Path(root_certificates).read_bytes()

    channel = create_channel(
        server_address=server_address,
        insecure=insecure,
        root_certificates=root_certificates,
        max_message_length=max_message_length,
    )
    channel.subscribe(on_channel_state_change)

    queue_client_message: Queue[ClientMessage] = Queue()  # pylint: disable=unsubscriptable-object
    queue_client_message_minio: Queue[MessageMinIO] = Queue(maxsize=1)  # pylint: disable=unsubscriptable-object

    stub = FlowerServiceStub(channel)

    if communication_type == CommunicationType.GRPC:
        server_message_chunks_iterator: Iterator[ServerMessageChunk] = stub.Join(iter(queue_client_message.get, None))
    elif communication_type == CommunicationType.MINIO:
        message_minio_iterator: Iterator[MessageMinIO] = stub.JoinMinIO(iter(queue_client_message_minio.get, None))
    else:
        raise ValueError(f"Unknown communication type: {communication_type}")

    def receive() -> Message:
        print("STEFAN - connection.py in grpc_connection.receive()")
        # Receive ServerMessage proto
        if communication_type == CommunicationType.GRPC:
            proto = get_message_from_batches(
                batch_messages_iterator=server_message_chunks_iterator,
                message_type=ServerMessage
            )
        elif communication_type == CommunicationType.MINIO:
            proto = get_server_message_from_minio(
                minio_client=minio_client,
                server_message_minio_iterator=message_minio_iterator
            )
            print(f"grpc_connection - receive() : {proto}")
        else:
            raise ValueError(f"Unknown communication type: {communication_type}")

        # ServerMessage proto --> *Ins --> RecordSet
        field = proto.WhichOneof("msg")
        message_type = ""
        if field == "get_properties_ins":
            recordset = compat.getpropertiesins_to_recordset(
                serde.get_properties_ins_from_proto(proto.get_properties_ins)
            )
            message_type = MESSAGE_TYPE_GET_PROPERTIES
        elif field == "get_parameters_ins":
            recordset = compat.getparametersins_to_recordset(
                serde.get_parameters_ins_from_proto(proto.get_parameters_ins)
            )
            message_type = MESSAGE_TYPE_GET_PARAMETERS
        elif field == "fit_ins":
            recordset = compat.fitins_to_recordset(
                serde.fit_ins_from_proto(proto.fit_ins), False
            )
            message_type = MESSAGE_TYPE_FIT
        elif field == "evaluate_ins":
            recordset = compat.evaluateins_to_recordset(
                serde.evaluate_ins_from_proto(proto.evaluate_ins), False
            )
            message_type = MESSAGE_TYPE_EVALUATE
        elif field == "reconnect_ins":
            recordset = RecordSet()
            recordset.configs_records["config"] = ConfigsRecord(
                {"seconds": proto.reconnect_ins.seconds}
            )
            message_type = "reconnect"
        else:
            raise ValueError(
                "Unsupported instruction in ServerMessage, "
                "cannot deserialize from ProtoBuf"
            )


        # Construct Message
        message = Message(
            metadata=Metadata(
                run_id=0,
                message_id=str(uuid.uuid4()),
                src_node_id=0,
                dst_node_id=0,
                reply_to_message="",
                group_id="",
                ttl="",
                message_type=message_type,
            ),
            content=recordset,
        )
        print("connection.py - receive message:")
        print(message)
        print("----------")
        return message

    def send(message: Message) -> None:
        # Retrieve RecordSet and message_type
        recordset = message.content
        message_type = message.metadata.message_type

        # RecordSet --> *Res --> *Res proto -> ClientMessage proto
        if message_type == MESSAGE_TYPE_GET_PROPERTIES:
            getpropres = compat.recordset_to_getpropertiesres(recordset)
            msg_proto = ClientMessage(
                get_properties_res=serde.get_properties_res_to_proto(getpropres)
            )
        elif message_type == MESSAGE_TYPE_GET_PARAMETERS:
            getparamres = compat.recordset_to_getparametersres(recordset, False)
            msg_proto = ClientMessage(
                get_parameters_res=serde.get_parameters_res_to_proto(getparamres)
            )
        elif message_type == MESSAGE_TYPE_FIT:
            fitres = compat.recordset_to_fitres(recordset, False)
            msg_proto = ClientMessage(fit_res=serde.fit_res_to_proto(fitres))
        elif message_type == MESSAGE_TYPE_EVALUATE:
            evalres = compat.recordset_to_evaluateres(recordset)
            msg_proto = ClientMessage(evaluate_res=serde.evaluate_res_to_proto(evalres))
        elif message_type == "reconnect":
            reason = cast(
                Reason.ValueType, recordset.configs_records["config"]["reason"]
            )
            msg_proto = ClientMessage(
                disconnect_res=ClientMessage.DisconnectRes(reason=reason)
            )
        else:
            raise ValueError(f"Invalid message type: {message_type}")

        if communication_type == CommunicationType.GRPC:
            client_message_chunks = batch_grpc_message(
                message=msg_proto,
                batch_size=max_message_length,
                batch_message_type=ClientMessageChunk,
                batch_message_header_size=CLIENT_MESSAGE_BATCH_HEADER_SIZE
            )
            for client_message_chunk in client_message_chunks:
                queue_client_message.put(client_message_chunk, block=False)
        elif communication_type == CommunicationType.MINIO:
            client_message_minio = push_client_message_to_minio(
                minio_client=minio_client,
                bucket_name=minio_bucket_name,
                source_file=str(uuid.uuid4()),
                client_message=msg_proto
            )
            print(f"grpc_connection - send() :\n {client_message_minio}")
            queue_client_message_minio.put(client_message_minio, block=False)
        else:
            raise ValueError(f"Unknown communication type: {communication_type}")

    try:
        # Yield methods
        yield (receive, send, None, None)
    finally:
        # Make sure to have a final
        channel.close()
        log(DEBUG, "gRPC channel closed")
