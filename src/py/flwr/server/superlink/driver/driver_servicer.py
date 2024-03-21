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
"""Driver API servicer."""
import uuid
from logging import DEBUG, INFO
from typing import List, Optional, Set, Iterator
from uuid import UUID

import grpc
from minio import Minio

from flwr.common.constant import CREATE_RUN_RESPONSE_BATCH_HEADER_SIZE, GET_NODES_RESPONSE_BATCH_HEADER_SIZE, \
    PUSH_TASK_INS_RESPONSE_BATCH_HEADER_SIZE, PULL_TASK_RES_RESPONSE_BATCH_HEADER_SIZE
from flwr.common.grpc_message_batching import get_message_from_batches, batch_grpc_message
from flwr.common.logger import log
from flwr.minio.minio_grpc_message import push_message_to_minio, get_message_from_minio
from flwr.proto import driver_pb2_grpc  # pylint: disable=E0611
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
from flwr.proto.minio_pb2 import MessageMinIO
from flwr.proto.node_pb2 import Node  # pylint: disable=E0611
from flwr.proto.task_pb2 import TaskRes  # pylint: disable=E0611
from flwr.server.superlink.state import State, StateFactory
from flwr.server.utils.validator import validate_task_ins_or_res


class DriverServicer(driver_pb2_grpc.DriverServicer):
    """Driver API servicer."""

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

    def GetNodes(
        self,
        request_iterator: Iterator[GetNodesRequestBatch],
        context: grpc.ServicerContext
    ) -> Iterator[GetNodesResponseBatch]:
        """Get available nodes."""
        log(INFO, "DriverServicer.GetNodes")
        state: State = self.state_factory.state()

        request = get_message_from_batches(
            batch_messages_iterator=request_iterator,
            message_type=GetNodesRequest
        )

        all_ids: Set[int] = state.get_nodes(request.run_id)
        nodes: List[Node] = [
            Node(node_id=node_id, anonymous=False) for node_id in all_ids
        ]

        response = GetNodesResponse(nodes=nodes)
        get_nodes_response_batches = batch_grpc_message(
            message=response,
            batch_size=self.max_message_length,
            batch_message_type=GetNodesResponse,
            batch_message_header_size=GET_NODES_RESPONSE_BATCH_HEADER_SIZE
        )

        for get_nodes_response_batch in get_nodes_response_batches:
            yield get_nodes_response_batch

    def CreateRun(
        self, request: CreateRunRequest, context: grpc.ServicerContext
    ) -> Iterator[CreateRunResponseBatch]:
        """Create run ID."""
        log(INFO, "DriverServicer.CreateRun")
        state: State = self.state_factory.state()
        run_id = state.create_run()

        create_run_response = CreateRunResponse(run_id=run_id)
        create_run_response_batches = batch_grpc_message(
            message=create_run_response,
            batch_size=self.max_message_length,
            batch_message_type=CreateRunResponseBatch,
            batch_message_header_size=CREATE_RUN_RESPONSE_BATCH_HEADER_SIZE
        )

        for create_run_response_batch in create_run_response_batches:
            yield create_run_response_batch

    def PushTaskIns(
        self,
        request_iterator: Iterator[PushTaskInsRequestBatch],
        context: grpc.ServicerContext
    ) -> Iterator[PushTaskInsResponse]:
        """Push a set of TaskIns."""
        log(DEBUG, "DriverServicer.PushTaskIns")

        request = get_message_from_batches(
            batch_messages_iterator=request_iterator,
            message_type=PushTaskInsRequest
        )

        # Validate request
        _raise_if(len(request.task_ins_list) == 0, "`task_ins_list` must not be empty")
        for task_ins in request.task_ins_list:
            validation_errors = validate_task_ins_or_res(task_ins)
            _raise_if(bool(validation_errors), ", ".join(validation_errors))

        # Init state
        state: State = self.state_factory.state()

        # Store each TaskIns
        task_ids: List[Optional[UUID]] = []
        for task_ins in request.task_ins_list:
            task_id: Optional[UUID] = state.store_task_ins(task_ins=task_ins)
            task_ids.append(task_id)

        push_task_ins_response = PushTaskInsResponse(
            task_ids=[str(task_id) if task_id else "" for task_id in task_ids]
        )

        push_task_ins_response_batches = batch_grpc_message(
            message=push_task_ins_response,
            batch_size=self.max_message_length,
            batch_message_type=PushTaskInsResponseBatch,
            batch_message_header_size=PUSH_TASK_INS_RESPONSE_BATCH_HEADER_SIZE
        )

        for push_task_ins_response_batch in push_task_ins_response_batches:
            yield push_task_ins_response_batch

    def PullTaskRes(
        self,
        request_iterator: Iterator[PullTaskResRequestBatch],
        context: grpc.ServicerContext
    ) -> Iterator[PullTaskResResponseBatch]:
        """Pull a set of TaskRes."""
        log(DEBUG, "DriverServicer.PullTaskRes")

        request = get_message_from_batches(
            batch_messages_iterator=request_iterator,
            message_type=PullTaskResRequest
        )

        # Convert each task_id str to UUID
        task_ids: Set[UUID] = {UUID(task_id) for task_id in request.task_ids}

        # Init state
        state: State = self.state_factory.state()

        # Register callback
        def on_rpc_done() -> None:
            log(DEBUG, "DriverServicer.PullTaskRes callback: delete TaskIns/TaskRes")

            if context.is_active():
                return
            if context.code() != grpc.StatusCode.OK:
                return

            # Delete delivered TaskIns and TaskRes
            state.delete_tasks(task_ids=task_ids)

        context.add_callback(on_rpc_done)

        # Read from state
        task_res_list: List[TaskRes] = state.get_task_res(task_ids=task_ids, limit=None)

        context.set_code(grpc.StatusCode.OK)

        pull_task_res_response = PullTaskResResponse(task_res_list=task_res_list)
        pull_task_res_response_batches = batch_grpc_message(
            message=pull_task_res_response,
            batch_size=self.max_message_length,
            batch_message_type=PullTaskResResponseBatch,
            batch_message_header_size=PULL_TASK_RES_RESPONSE_BATCH_HEADER_SIZE
        )

        for pull_task_res_response_batch in pull_task_res_response_batches:
            yield pull_task_res_response_batch

    def CreateRunMinIO(self, request: MessageMinIO, context: grpc.ServicerContext) -> MessageMinIO:
        """CreateRunMinIO"""
        log(INFO, "DriverServicer.CreateRunMinIO")
        state: State = self.state_factory.state()
        run_id = state.create_run()

        create_run_response = CreateRunResponse(run_id=run_id)
        create_run_response_minio = push_message_to_minio(
            minio_client=self.minio_client,
            bucket_name=self.minio_bucket_name,
            source_file=str(uuid.uuid4()),
            message=create_run_response,
            minio_message_type=MessageMinIO
        )
        return create_run_response_minio

    def GetNodesMinIO(self, request: MessageMinIO, context: grpc.ServicerContext) -> MessageMinIO:
        """GetNodesMinIO"""
        log(INFO, "DriverServicer.GetNodesMinIO")
        state: State = self.state_factory.state()

        get_nodes_request = get_message_from_minio(
            minio_client=self.minio_client,
            minio_message_iterator=iter([request]),
            message_type=GetNodesRequest
        )

        all_ids: Set[int] = state.get_nodes(get_nodes_request.run_id)
        nodes: List[Node] = [
            Node(node_id=node_id, anonymous=False) for node_id in all_ids
        ]

        get_nodes_response = GetNodesResponse(nodes=nodes)
        get_nodes_response_minio = push_message_to_minio(
            minio_client=self.minio_client,
            bucket_name=self.minio_bucket_name,
            source_file=str(uuid.uuid4()),
            message=get_nodes_response,
            minio_message_type=MessageMinIO
        )

        return get_nodes_response_minio

    def PushTaskInsMinIO(self, request: MessageMinIO, context: grpc.ServicerContext) -> MessageMinIO:
        """PushTaskInsMinIO"""
        log(DEBUG, "DriverServicer.PushTaskInsMinIO")

        push_task_ins_request = get_message_from_minio(
            minio_client=self.minio_client,
            minio_message_iterator=iter([request]),
            message_type=PushTaskInsRequest
        )

        # Validate request
        _raise_if(len(push_task_ins_request.task_ins_list) == 0, "`task_ins_list` must not be empty")
        for task_ins in push_task_ins_request.task_ins_list:
            validation_errors = validate_task_ins_or_res(task_ins)
            _raise_if(bool(validation_errors), ", ".join(validation_errors))

        # Init state
        state: State = self.state_factory.state()

        # Store each TaskIns
        task_ids: List[Optional[UUID]] = []
        for task_ins in push_task_ins_request.task_ins_list:
            task_id: Optional[UUID] = state.store_task_ins(task_ins=task_ins)
            task_ids.append(task_id)

        push_task_ins_response = PushTaskInsResponse(
            task_ids=[str(task_id) if task_id else "" for task_id in task_ids]
        )

        push_task_ins_response_minio = push_message_to_minio(
            minio_client=self.minio_client,
            bucket_name=self.minio_bucket_name,
            source_file=str(uuid.uuid4()),
            message=push_task_ins_response,
            minio_message_type=MessageMinIO
        )
        return push_task_ins_response_minio

    def PullTaskResMinIO(self, request: MessageMinIO, context: grpc.ServicerContext) -> MessageMinIO:
        """PullTaskMinIO"""
        log(DEBUG, "DriverServicer.PullTaskResMinIO")

        pull_task_ins_request = get_message_from_minio(
            minio_client=self.minio_client,
            minio_message_iterator=iter([request]),
            message_type=PullTaskResRequest
        )

        # Convert each task_id str to UUID
        task_ids: Set[UUID] = {UUID(task_id) for task_id in pull_task_ins_request.task_ids}

        # Init state
        state: State = self.state_factory.state()

        # Register callback
        def on_rpc_done() -> None:
            log(DEBUG, "DriverServicer.PullTaskRes callback: delete TaskIns/TaskRes")

            if context.is_active():
                return
            if context.code() != grpc.StatusCode.OK:
                return

            # Delete delivered TaskIns and TaskRes
            state.delete_tasks(task_ids=task_ids)

        context.add_callback(on_rpc_done)

        # Read from state
        task_res_list: List[TaskRes] = state.get_task_res(task_ids=task_ids, limit=None)

        context.set_code(grpc.StatusCode.OK)

        pull_task_res_response = PullTaskResResponse(task_res_list=task_res_list)
        pull_task_res_response_minio = push_message_to_minio(
            minio_client=self.minio_client,
            bucket_name=self.minio_bucket_name,
            source_file=str(uuid.uuid4()),
            message=pull_task_res_response,
            minio_message_type=MessageMinIO
        )

        return pull_task_res_response_minio


def _raise_if(validation_error: bool, detail: str) -> None:
    if validation_error:
        raise ValueError(f"Malformed PushTaskInsRequest: {detail}")
