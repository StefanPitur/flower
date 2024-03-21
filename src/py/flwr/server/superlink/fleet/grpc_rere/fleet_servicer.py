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
"""Fleet API gRPC request-response servicer."""
import uuid
from logging import INFO
from typing import Iterator, Optional

import grpc
from minio import Minio

from flwr.common.constant import (
    CREATE_NODE_RESPONSE_BATCH_HEADER_SIZE,
    PULL_TASK_INS_RESPONSE_BATCH_HEADER_SIZE,
    PUSH_TASK_RES_RESPONSE_BATCH_HEADER_SIZE,
)
from flwr.common.grpc_message_batching import get_message_from_batches, batch_grpc_message
from flwr.common.logger import log
from flwr.minio.minio_grpc_message import get_message_from_minio, push_message_to_minio
from flwr.proto import fleet_pb2_grpc  # pylint: disable=E0611
from flwr.proto.fleet_pb2 import (  # pylint: disable=E0611
    CreateNodeRequest,
    DeleteNodeRequest,
    PullTaskInsRequest,
    PushTaskResRequest,
    CreateNodeResponseBatch, DeleteNodeRequestBatch,
    PullTaskInsRequestBatch, PullTaskInsResponseBatch, PushTaskResRequestBatch,
    PushTaskResResponseBatch, DeleteNodeResponse,
)
from flwr.proto.minio_pb2 import MessageMinIO
from flwr.server.superlink.fleet.message_handler import message_handler
from flwr.server.superlink.state import StateFactory


class FleetServicer(fleet_pb2_grpc.FleetServicer):
    """Fleet API servicer."""

    def __init__(
        self,
        state_factory: StateFactory,
        max_message_length: int,
        minio_client: Optional[Minio] = None,
        minio_bucket_name: Optional[str] = None,
    ) -> None:
        self.state_factory = state_factory
        self.max_message_length = max_message_length
        self.minio_client = minio_client
        self.minio_bucket_name = minio_bucket_name

    def CreateNode(
        self,
        request: CreateNodeRequest,
        context: grpc.ServicerContext
    ) -> Iterator[CreateNodeResponseBatch]:
        """."""
        log(INFO, "FleetServicer.CreateNode")

        create_node_response = message_handler.create_node(
            request=request,
            state=self.state_factory.state(),
        )

        create_node_response_batches = batch_grpc_message(
            message=create_node_response,
            batch_size=self.max_message_length,
            batch_message_type=CreateNodeResponseBatch,
            batch_message_header_size=CREATE_NODE_RESPONSE_BATCH_HEADER_SIZE
        )
        for create_node_response_batch in create_node_response_batches:
            yield create_node_response_batch

    def DeleteNode(
        self,
        request_iterator: Iterator[DeleteNodeRequestBatch],
        context: grpc.ServicerContext
    ) -> DeleteNodeResponse:
        """."""
        log(INFO, "FleetServicer.DeleteNode")

        delete_node_request = get_message_from_batches(
            batch_messages_iterator=request_iterator,
            message_type=DeleteNodeRequest
        )

        return message_handler.delete_node(
            request=delete_node_request,
            state=self.state_factory.state(),
        )

    def PullTaskIns(
        self,
        request_iterator: Iterator[PullTaskInsRequestBatch],
        context: grpc.ServicerContext
    ) -> Iterator[PullTaskInsResponseBatch]:
        """Pull TaskIns."""
        log(INFO, "FleetServicer.PullTaskIns")

        pull_task_ins_request = get_message_from_batches(
            batch_messages_iterator=request_iterator,
            message_type=PullTaskInsRequest
        )

        pull_task_ins_response = message_handler.pull_task_ins(
            request=pull_task_ins_request,
            state=self.state_factory.state(),
        )

        pull_task_ins_response_batches = batch_grpc_message(
            message=pull_task_ins_response,
            batch_size=self.max_message_length,
            batch_message_type=PullTaskInsResponseBatch,
            batch_message_header_size=PULL_TASK_INS_RESPONSE_BATCH_HEADER_SIZE
        )

        for pull_task_ins_response_batch in pull_task_ins_response_batches:
            yield pull_task_ins_response_batch

    def PushTaskRes(
        self,
        request_iterator: Iterator[PushTaskResRequestBatch],
        context: grpc.ServicerContext
    ) -> Iterator[PushTaskResResponseBatch]:
        """Push TaskRes."""
        log(INFO, "FleetServicer.PushTaskRes")

        push_task_res_request = get_message_from_batches(
            batch_messages_iterator=request_iterator,
            message_type=PushTaskResRequest
        )

        push_task_res_response = message_handler.push_task_res(
            request=push_task_res_request,
            state=self.state_factory.state(),
        )

        push_task_res_response_batches = batch_grpc_message(
            message=push_task_res_response,
            batch_size=self.max_message_length,
            batch_message_type=PushTaskResResponseBatch,
            batch_message_header_size=PUSH_TASK_RES_RESPONSE_BATCH_HEADER_SIZE
        )

        for push_task_res_response_batch in push_task_res_response_batches:
            yield push_task_res_response_batch

    def CreateNodeMinIO(
        self,
        request: MessageMinIO,
        context: grpc.ServicerContext
    ) -> MessageMinIO:
        """."""
        log(INFO, "FleetServicer.CreateNodeMinIO")

        create_node_request = get_message_from_minio(
            minio_client=self.minio_client,
            minio_message_iterator=iter([request]),
            message_type=CreateNodeRequest,
        )

        create_node_response = message_handler.create_node(
            request=create_node_request,
            state=self.state_factory.state(),
        )

        create_node_response_minio = push_message_to_minio(
            minio_client=self.minio_client,
            bucket_name=self.minio_bucket_name,
            source_file=str(uuid.uuid4()),
            message=create_node_response,
            minio_message_type=MessageMinIO
        )
        return create_node_response_minio

    def DeleteNodeMinIO(
        self,
        request: MessageMinIO,
        context: grpc.ServicerContext
    ) -> MessageMinIO:
        """."""
        log(INFO, "FleetServicer.DeleteNodeMinIO")

        delete_node_request = get_message_from_minio(
            minio_client=self.minio_client,
            minio_message_iterator=iter([request]),
            message_type=DeleteNodeRequest
        )

        delete_node_response = message_handler.delete_node(
            request=delete_node_request,
            state=self.state_factory.state(),
        )
        delete_node_response_minio = push_message_to_minio(
            minio_client=self.minio_client,
            bucket_name=self.minio_bucket_name,
            source_file=str(uuid.uuid4()),
            message=delete_node_response,
            minio_message_type=MessageMinIO
        )
        return delete_node_response_minio

    def PullTaskInsMinIO(
        self,
        request: MessageMinIO,
        context: grpc.ServicerContext
    ) -> MessageMinIO:
        """Pull TaskIns via MinIO instance"""
        log(INFO, "FleetServicer.PullTaskInsMinIO")

        pull_task_ins_request = get_message_from_minio(
            minio_client=self.minio_client,
            minio_message_iterator=iter([request]),
            message_type=PullTaskInsRequest
        )

        pull_task_ins_response = message_handler.pull_task_ins(
            request=pull_task_ins_request,
            state=self.state_factory.state(),
        )

        pull_task_ins_response_minio = push_message_to_minio(
            minio_client=self.minio_client,
            bucket_name=self.minio_bucket_name,
            source_file=str(uuid.uuid4()),
            message=pull_task_ins_response,
            minio_message_type=MessageMinIO
        )

        return pull_task_ins_response_minio

    def PushTaskResMinIO(
        self,
        request: MessageMinIO,
        context: grpc.ServicerContext
    ) -> MessageMinIO:
        """Push TaskRes via MinIO instance"""
        log(INFO, "FleetServicer.PushTaskResMinIO")

        push_task_res_request = get_message_from_minio(
            minio_client=self.minio_client,
            minio_message_iterator=iter([request]),
            message_type=PushTaskResRequest
        )

        push_task_res_response = message_handler.push_task_res(
            request=push_task_res_request,
            state=self.state_factory.state(),
        )

        push_task_res_response_minio = push_message_to_minio(
            minio_client=self.minio_client,
            bucket_name=self.minio_bucket_name,
            source_file=str(uuid.uuid4()),
            message=push_task_res_response,
            minio_message_type=MessageMinIO
        )

        return push_task_res_response_minio
