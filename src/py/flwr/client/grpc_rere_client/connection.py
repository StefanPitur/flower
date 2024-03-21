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
"""Contextmanager for a gRPC request-response channel to the Flower server."""
import uuid
from contextlib import contextmanager
from copy import copy
from logging import DEBUG, ERROR
from pathlib import Path
from typing import Callable, Dict, Iterator, Optional, Tuple, Union, cast

from minio import Minio

from flwr.client.message_handler.message_handler import validate_out_message
from flwr.client.message_handler.task_handler import get_task_ins, validate_task_ins
from flwr.common import GRPC_MAX_MESSAGE_LENGTH
from flwr.common.constant import DELETE_NODE_REQUEST_BATCH_HEADER_SIZE, \
    PULL_TASK_INS_REQUEST_BATCH_HEADER_SIZE, PUSH_TASK_RES_REQUEST_BATCH_HEADER_SIZE
from flwr.common.grpc import create_channel
from flwr.common.grpc_message_batching import batch_grpc_message, get_message_from_batches
from flwr.common.logger import log, warn_experimental_feature
from flwr.common.message import Message, Metadata
from flwr.common.serde import message_from_taskins, message_to_taskres
from flwr.minio.minio_grpc_message import push_message_to_minio, get_message_from_minio
from flwr.proto.fleet_pb2 import (  # pylint: disable=E0611
    CreateNodeRequest,
    DeleteNodeRequest,
    PullTaskInsRequest,
    PushTaskResRequest, CreateNodeResponse, DeleteNodeRequestBatch, PullTaskInsRequestBatch,
    PullTaskInsResponse, PushTaskResRequestBatch,
)
from flwr.proto.fleet_pb2_grpc import FleetStub  # pylint: disable=E0611
from flwr.proto.minio_pb2 import MessageMinIO
from flwr.proto.node_pb2 import Node  # pylint: disable=E0611
from flwr.proto.task_pb2 import TaskIns  # pylint: disable=E0611
from flwr.server.server_config import CommunicationType

KEY_NODE = "node"
KEY_METADATA = "in_message_metadata"


def on_channel_state_change(channel_connectivity: str) -> None:
    """Log channel connectivity."""
    log(DEBUG, channel_connectivity)


@contextmanager
def grpc_request_response(
    server_address: str,
    insecure: bool,
    max_message_length: int = GRPC_MAX_MESSAGE_LENGTH,  # pylint: disable=W0613
    root_certificates: Optional[Union[bytes, str]] = None,
    communication_type: CommunicationType = CommunicationType.GRPC,  # pylint: disable=unused-argument
    minio_client: Optional[Minio] = None,  # pylint: disable=unused-argument
    minio_bucket_name: Optional[str] = None,  # pylint: disable=unused-argument
) -> Iterator[
    Tuple[
        Callable[[], Optional[Message]],
        Callable[[Message], None],
        Optional[Callable[[], None]],
        Optional[Callable[[], None]],
    ]
]:
    """Primitives for request/response-based interaction with a server.

    One notable difference to the grpc_connection context manager is that
    `receive` can return `None`.

    Parameters
    ----------
    server_address : str
        The IPv6 address of the server with `http://` or `https://`.
        If the Flower server runs on the same machine
        on port 8080, then `server_address` would be `"http://[::]:8080"`.
    max_message_length : int
        Ignored, only present to preserve API-compatibility.
    root_certificates : Optional[Union[bytes, str]] (default: None)
        Path of the root certificate. If provided, a secure
        connection using the certificates will be established to an SSL-enabled
        Flower server. Bytes won't work for the REST API.
    communication_type : CommunicationType
        Ignored, only present to preserve API-compatibility
    minio_client : Optional[Minio] (default: None)
        Ignored, only present to preserve API-compatibility
    minio_bucket_name : Optional[str] (default: None)
        Ignored, only present to preserve API-compatibility

    Returns
    -------
    receive : Callable
    send : Callable
    create_node : Optional[Callable]
    delete_node : Optional[Callable]
    """
    warn_experimental_feature("`grpc-rere`")

    if communication_type == CommunicationType.MINIO and (minio_client is None or minio_bucket_name is None):
        raise ValueError("When using MINIO, you must provide both minio_client and minio_bucket_name")

    if isinstance(root_certificates, str):
        root_certificates = Path(root_certificates).read_bytes()

    channel = create_channel(
        server_address=server_address,
        insecure=insecure,
        root_certificates=root_certificates,
        max_message_length=max_message_length,
    )
    channel.subscribe(on_channel_state_change)
    stub = FleetStub(channel)

    # Necessary state to validate messages to be sent
    state: Dict[str, Optional[Metadata]] = {KEY_METADATA: None}

    # Enable create_node and delete_node to store node
    node_store: Dict[str, Optional[Node]] = {KEY_NODE: None}

    ###########################################################################
    # receive/send functions
    ###########################################################################

    def create_node() -> None:
        """Set create_node."""
        create_node_request = CreateNodeRequest()

        if communication_type == CommunicationType.GRPC:
            create_node_response_iterator = stub.CreateNode(
                request=create_node_request,
            )

            create_node_response = get_message_from_batches(
                batch_messages_iterator=create_node_response_iterator,
                message_type=CreateNodeResponse
            )
        elif communication_type == CommunicationType.MINIO:
            create_node_request_minio = push_message_to_minio(
                minio_client=minio_client,
                bucket_name=minio_bucket_name,
                source_file=str(uuid.uuid4()),
                message=create_node_request,
                minio_message_type=MessageMinIO
            )

            create_node_response_minio: MessageMinIO = stub.CreateNodeMinIO(request=create_node_request_minio)

            create_node_response = get_message_from_minio(
                minio_client=minio_client,
                minio_message_iterator=iter([create_node_response_minio]),
                message_type=CreateNodeResponse
            )

        else:
            raise ValueError(f"Unknown communication type - {communication_type}")

        node_store[KEY_NODE] = create_node_response.node

    def delete_node() -> None:
        """Set delete_node."""
        # Get Node
        if node_store[KEY_NODE] is None:
            log(ERROR, "Node instance missing")
            return
        node: Node = cast(Node, node_store[KEY_NODE])

        delete_node_request = DeleteNodeRequest(node=node)

        if communication_type == CommunicationType.GRPC:
            delete_node_request_iterator = iter(
                batch_grpc_message(
                    message=delete_node_request,
                    batch_size=max_message_length,
                    batch_message_type=DeleteNodeRequestBatch,
                    batch_message_header_size=DELETE_NODE_REQUEST_BATCH_HEADER_SIZE
                )
            )

            stub.DeleteNode(request_iterator=delete_node_request_iterator)
        elif communication_type == CommunicationType.MINIO:
            delete_node_request_minio = push_message_to_minio(
                minio_client=minio_client,
                bucket_name=minio_bucket_name,
                source_file=str(uuid.uuid4()),
                message=delete_node_request,
                minio_message_type=MessageMinIO
            )
            stub.DeleteNodeMinIO(request=delete_node_request_minio)
        else:
            raise ValueError(f"Unknown communication type - {communication_type}")
        del node_store[KEY_NODE]

    def receive() -> Optional[Message]:
        """Receive next task from server."""
        # Get Node
        if node_store[KEY_NODE] is None:
            log(ERROR, "Node instance missing")
            return None
        node: Node = cast(Node, node_store[KEY_NODE])

        # Request instructions (task) from server
        request = PullTaskInsRequest(node=node)

        if communication_type == CommunicationType.GRPC:
            request_iterator = iter(
                batch_grpc_message(
                    message=request,
                    batch_size=max_message_length,
                    batch_message_type=PullTaskInsRequestBatch,
                    batch_message_header_size=PULL_TASK_INS_REQUEST_BATCH_HEADER_SIZE
                )
            )

            response_iterator = stub.PullTaskIns(request_iterator=request_iterator)

            response = get_message_from_batches(
                batch_messages_iterator=response_iterator,
                message_type=PullTaskInsResponse
            )
        elif communication_type == CommunicationType.MINIO:
            pull_task_ins_request_minio = push_message_to_minio(
                minio_client=minio_client,
                bucket_name=minio_bucket_name,
                source_file=str(uuid.uuid4()),
                message=request,
                minio_message_type=MessageMinIO
            )

            pull_task_ins_response_minio: MessageMinIO = stub.PullTaskInsMinIO(request=pull_task_ins_request_minio)

            response = get_message_from_minio(
                minio_client=minio_client,
                minio_message_iterator=iter([pull_task_ins_response_minio]),
                message_type=CreateNodeResponse
            )
        else:
            raise ValueError(f"Unknown communication type - {communication_type}")

        # Get the current TaskIns
        task_ins: Optional[TaskIns] = get_task_ins(response)

        # Discard the current TaskIns if not valid
        if task_ins is not None and not (
            task_ins.task.consumer.node_id == node.node_id
            and validate_task_ins(task_ins)
        ):
            task_ins = None

        # Construct the Message
        in_message = message_from_taskins(task_ins) if task_ins else None

        # Remember `metadata` of the in message
        state[KEY_METADATA] = copy(in_message.metadata) if in_message else None

        # Return the message if available
        return in_message

    def send(message: Message) -> None:
        """Send task result back to server."""
        # Get Node
        if node_store[KEY_NODE] is None:
            log(ERROR, "Node instance missing")
            return

        # Get incoming message
        in_metadata = state[KEY_METADATA]
        if in_metadata is None:
            log(ERROR, "No current message")
            return

        # Validate out message
        if not validate_out_message(message, in_metadata):
            log(ERROR, "Invalid out message")
            return

        # Construct TaskRes
        task_res = message_to_taskres(message)

        # Serialize ProtoBuf to bytes
        request = PushTaskResRequest(task_res_list=[task_res])

        if communication_type == CommunicationType.GRPC:
            request_iterator = iter(
                batch_grpc_message(
                    message=request,
                    batch_size=max_message_length,
                    batch_message_type=PushTaskResRequestBatch,
                    batch_message_header_size=PUSH_TASK_RES_REQUEST_BATCH_HEADER_SIZE
                )
            )

            _ = stub.PushTaskRes(request_iterator=request_iterator)
        elif communication_type == CommunicationType.MINIO:
            push_task_res_request_minio = push_message_to_minio(
                minio_client=minio_client,
                bucket_name=minio_bucket_name,
                source_file=str(uuid.uuid4()),
                message=request,
                minio_message_type=MessageMinIO
            )

            stub.PushTaskResMinIO(request=push_task_res_request_minio)
        else:
            raise ValueError(f"Unknown communication type - {communication_type}")

        state[KEY_METADATA] = None

    try:
        # Yield methods
        yield (receive, send, create_node, delete_node)
    except Exception as exc:  # pylint: disable=broad-except
        log(ERROR, exc)
