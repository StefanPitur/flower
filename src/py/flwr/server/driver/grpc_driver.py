# Copyright 2023 Flower Labs GmbH. All Rights Reserved.
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
"""Flower driver service client."""
import uuid
from logging import ERROR, INFO, WARNING
from typing import Optional, Iterator

import grpc
from minio import Minio

from flwr.common import EventType, event
from flwr.common.constant import GET_NODES_REQUEST_BATCH_HEADER_SIZE, PUSH_TASK_INS_REQUEST_BATCH_HEADER_SIZE, \
    PULL_TASK_RES_REQUEST_BATCH_HEADER_SIZE
from flwr.common.grpc import create_channel, GRPC_MAX_MESSAGE_LENGTH
from flwr.common.grpc_message_batching import get_message_from_batches, batch_grpc_message
from flwr.common.logger import log
from flwr.minio.minio_grpc_message import push_message_to_minio, get_message_from_minio
from flwr.proto.driver_pb2 import (  # pylint: disable=E0611
    CreateRunRequest,
    CreateRunResponse,
    GetNodesRequest,
    GetNodesResponse,
    PullTaskResRequest,
    PullTaskResResponse,
    PushTaskInsRequest,
    PushTaskInsResponse, CreateRunResponseBatch, GetNodesRequestBatch, GetNodesResponseBatch, PushTaskInsRequestBatch,
    PushTaskInsResponseBatch, PullTaskResRequestBatch, PullTaskResResponseBatch,
)
from flwr.proto.driver_pb2_grpc import DriverStub  # pylint: disable=E0611
from flwr.proto.minio_pb2 import MessageMinIO
from flwr.server.server_config import CommunicationType

DEFAULT_SERVER_ADDRESS_DRIVER = "[::]:9091"

ERROR_MESSAGE_DRIVER_NOT_CONNECTED = """
[Driver] Error: Not connected.

Call `connect()` on the `GrpcDriver` instance before calling any of the other
`GrpcDriver` methods.
"""


class GrpcDriver:
    """`GrpcDriver` provides access to the gRPC Driver API/service."""

    def __init__(
        self,
        driver_service_address: str = DEFAULT_SERVER_ADDRESS_DRIVER,
        root_certificates: Optional[bytes] = None,
        grpc_max_message_length: int = GRPC_MAX_MESSAGE_LENGTH,
        communication_type: CommunicationType = CommunicationType.GRPC,
        minio_client: Optional[Minio] = None,
        minio_bucket_name: Optional[str] = None
    ) -> None:
        self.driver_service_address = driver_service_address
        self.root_certificates = root_certificates
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[DriverStub] = None
        self.grpc_max_message_length = grpc_max_message_length
        self.communication_type = communication_type
        self.minio_client = minio_client
        self.minio_bucket_name = minio_bucket_name

    def connect(self) -> None:
        """Connect to the Driver API."""
        event(EventType.DRIVER_CONNECT)
        if self.channel is not None or self.stub is not None:
            log(WARNING, "Already connected")
            return
        self.channel = create_channel(
            server_address=self.driver_service_address,
            insecure=(self.root_certificates is None),
            root_certificates=self.root_certificates,
        )
        self.stub = DriverStub(self.channel)
        log(INFO, "[Driver] Connected to %s", self.driver_service_address)

    def disconnect(self) -> None:
        """Disconnect from the Driver API."""
        event(EventType.DRIVER_DISCONNECT)
        if self.channel is None or self.stub is None:
            log(WARNING, "Already disconnected")
            return
        channel = self.channel
        self.channel = None
        self.stub = None
        channel.close()
        log(INFO, "[Driver] Disconnected")

    def create_run(self, req: CreateRunRequest) -> CreateRunResponse:
        """Request for run ID."""
        # Check if channel is open
        if self.stub is None:
            log(ERROR, ERROR_MESSAGE_DRIVER_NOT_CONNECTED)
            raise ConnectionError("`GrpcDriver` instance not connected")

        # Call Driver API
        if self.communication_type == CommunicationType.GRPC:
            res_batches_iterator: Iterator[CreateRunResponseBatch] = self.stub.CreateRun(request=req)
            res: CreateRunResponse = get_message_from_batches(
                batch_messages_iterator=res_batches_iterator,
                message_type=CreateRunResponse
            )
        elif self.communication_type == CommunicationType.MINIO:
            req_minio: MessageMinIO = push_message_to_minio(
                minio_client=self.minio_client,
                bucket_name=self.minio_bucket_name,
                source_file=str(uuid.uuid4()),
                message=req,
                minio_message_type=MessageMinIO
            )
            res_minio = self.stub.CreateRunMinIO(request=req_minio)
            res: CreateRunResponse = get_message_from_minio(
                minio_client=self.minio_client,
                minio_message_iterator=iter([res_minio]),
                message_type=CreateRunResponse
            )
        else:
            raise ValueError(f"Unsupported communication type: {self.communication_type}")
        return res

    def get_nodes(self, req: GetNodesRequest) -> GetNodesResponse:
        """Get client IDs."""
        # Check if channel is open
        if self.stub is None:
            log(ERROR, ERROR_MESSAGE_DRIVER_NOT_CONNECTED)
            raise ConnectionError("`GrpcDriver` instance not connected")

        # Call gRPC Driver API
        if self.communication_type == CommunicationType.GRPC:
            req_iterator: Iterator[GetNodesRequestBatch] = iter(batch_grpc_message(
                message=req,
                batch_size=self.grpc_max_message_length,
                batch_message_type=GetNodesRequestBatch,
                batch_message_header_size=GET_NODES_REQUEST_BATCH_HEADER_SIZE
            ))
            res_iterator: Iterator[GetNodesResponseBatch] = self.stub.GetNodes(request_iterator=req_iterator)
            res: GetNodesResponse = get_message_from_batches(
                batch_messages_iterator=res_iterator,
                message_type=GetNodesResponse
            )
        elif self.communication_type == CommunicationType.MINIO:
            req_minio: MessageMinIO = push_message_to_minio(
                minio_client=self.minio_client,
                bucket_name=self.minio_bucket_name,
                source_file=str(uuid.uuid4()),
                message=req,
                minio_message_type=MessageMinIO
            )
            res_minio = self.stub.GetNodesMinIO(request=req_minio)
            res: GetNodesResponse = get_message_from_minio(
                minio_client=self.minio_client,
                minio_message_iterator=iter([res_minio]),
                message_type=GetNodesResponse
            )
        else:
            raise ValueError(f"Unsupported communication type: {self.communication_type}")
        return res

    def push_task_ins(self, req: PushTaskInsRequest) -> PushTaskInsResponse:
        """Schedule tasks."""
        # Check if channel is open
        if self.stub is None:
            log(ERROR, ERROR_MESSAGE_DRIVER_NOT_CONNECTED)
            raise ConnectionError("`GrpcDriver` instance not connected")

        # Call gRPC Driver API
        if self.communication_type == CommunicationType.GRPC:
            req_iterator: Iterator[PushTaskInsRequestBatch] = iter(batch_grpc_message(
                message=req,
                batch_size=self.grpc_max_message_length,
                batch_message_type=PushTaskInsRequestBatch,
                batch_message_header_size=PUSH_TASK_INS_REQUEST_BATCH_HEADER_SIZE
            ))
            res_iterator: Iterator[PushTaskInsResponseBatch] = self.stub.PushTaskIns(request_iterator=req_iterator)
            res: PushTaskInsResponse = get_message_from_batches(
                batch_messages_iterator=res_iterator,
                message_type=PushTaskInsResponse
            )
        elif self.communication_type == CommunicationType.MINIO:
            req_minio: MessageMinIO = push_message_to_minio(
                minio_client=self.minio_client,
                bucket_name=self.minio_bucket_name,
                source_file=str(uuid.uuid4()),
                message=req,
                minio_message_type=MessageMinIO
            )
            res_minio = self.stub.PushTaskInsMinIO(request=req_minio)
            res: PushTaskInsResponse = get_message_from_minio(
                minio_client=self.minio_client,
                minio_message_iterator=iter([res_minio]),
                message_type=PushTaskInsResponse
            )
        else:
            raise ValueError(f"Unsupported communication type: {self.communication_type}")
        return res

    def pull_task_res(self, req: PullTaskResRequest) -> PullTaskResResponse:
        """Get task results."""
        # Check if channel is open
        if self.stub is None:
            log(ERROR, ERROR_MESSAGE_DRIVER_NOT_CONNECTED)
            raise ConnectionError("`GrpcDriver` instance not connected")

        # Call Driver API
        if self.communication_type == CommunicationType.GRPC:
            req_iterator: Iterator[PullTaskResRequestBatch] = iter(batch_grpc_message(
                message=req,
                batch_size=self.grpc_max_message_length,
                batch_message_type=PullTaskResRequestBatch,
                batch_message_header_size=PULL_TASK_RES_REQUEST_BATCH_HEADER_SIZE
            ))
            res_iterator: Iterator[PullTaskResResponseBatch] = self.stub.PullTaskRes(request_iterator=req_iterator)
            res: PullTaskResResponse = get_message_from_batches(
                batch_messages_iterator=res_iterator,
                message_type=PullTaskResResponse
            )
        elif self.communication_type == CommunicationType.MINIO:
            req_minio: MessageMinIO = push_message_to_minio(
                minio_client=self.minio_client,
                bucket_name=self.minio_bucket_name,
                source_file=str(uuid.uuid4()),
                message=req,
                minio_message_type=MessageMinIO
            )
            res_minio = self.stub.PullTaskResMinIO(request=req_minio)
            res: PullTaskResResponse = get_message_from_minio(
                minio_client=self.minio_client,
                minio_message_iterator=iter([res_minio]),
                message_type=PullTaskResResponse
            )
        else:
            raise ValueError(f"Unsupported communication type: {self.communication_type}")
        return res
