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
"""Servicer for FlowerService.

Relevant knowledge for reading this modules code:
- https://github.com/grpc/grpc/blob/master/doc/statuscodes.md
"""

import uuid
from typing import Callable, Iterator, Optional

import grpc
from iterators import TimeoutIterator
from minio import Minio

from flwr.common.constant import SERVER_MESSAGE_BATCH_HEADER_SIZE
from flwr.common.grpc_message_batching import get_message_from_batches, batch_grpc_message
from flwr.minio.minio_grpc_message import get_message_from_minio, push_message_to_minio
from flwr.proto import transport_pb2_grpc  # pylint: disable=E0611
from flwr.proto.transport_pb2 import (  # pylint: disable=E0611
    ServerMessageChunk,
    ClientMessageChunk, MessageMinIO, ClientMessage
)
from flwr.server.client_manager import ClientManager
from flwr.server.superlink.fleet.grpc_bidi.grpc_bridge import (
    GrpcBridge,
    InsWrapper,
    ResWrapper,
)
from flwr.server.superlink.fleet.grpc_bidi.grpc_client_proxy import GrpcClientProxy


def default_bridge_factory() -> GrpcBridge:
    """Return GrpcBridge instance."""
    return GrpcBridge()


def default_grpc_client_proxy_factory(cid: str, bridge: GrpcBridge) -> GrpcClientProxy:
    """Return GrpcClientProxy instance."""
    return GrpcClientProxy(cid=cid, bridge=bridge)


def register_client_proxy(
    client_manager: ClientManager,
    client_proxy: GrpcClientProxy,
    context: grpc.ServicerContext,
) -> bool:
    """Try registering GrpcClientProxy with ClientManager."""
    is_success = client_manager.register(client_proxy)
    if is_success:

        def rpc_termination_callback() -> None:
            client_proxy.bridge.close()
            client_manager.unregister(client_proxy)

        context.add_callback(rpc_termination_callback)
    return is_success


class FlowerServiceServicer(transport_pb2_grpc.FlowerServiceServicer):
    """FlowerServiceServicer for bi-directional gRPC message stream."""

    def __init__(
        self,
        max_message_length: int,
        client_manager: ClientManager,
        grpc_bridge_factory: Callable[[], GrpcBridge] = default_bridge_factory,
        grpc_client_proxy_factory: Callable[
            [str, GrpcBridge], GrpcClientProxy
        ] = default_grpc_client_proxy_factory,
        minio_client: Optional[Minio] = None,
        minio_bucket_name: Optional[str] = None,
    ) -> None:
        self.max_message_length = max_message_length
        self.client_manager: ClientManager = client_manager
        self.grpc_bridge_factory = grpc_bridge_factory
        self.client_proxy_factory = grpc_client_proxy_factory
        self.minio_client = minio_client
        self.minio_bucket_name = minio_bucket_name

    def Join(  # pylint: disable=invalid-name
        self,
        request_iterator: Iterator[ClientMessageChunk],
        context: grpc.ServicerContext,
    ) -> Iterator[ServerMessageChunk]:
        """Facilitate bi-directional streaming of messages between server and client.

        Invoked by each gRPC client which participates in the network.

        Protocol:
        - The first message is sent from the server to the client
        - Both `ServerMessage` and `ClientMessage` are message "wrappers"
          wrapping the actual message
        - The `Join` method is (pretty much) unaware of the protocol
        """
        # When running Flower behind a proxy, the peer can be the same for
        # different clients, so instead of `cid: str = context.peer()` we
        # use a `UUID4` that is unique.
        cid: str = uuid.uuid4().hex
        bridge = self.grpc_bridge_factory()
        client_proxy = self.client_proxy_factory(cid, bridge)
        is_success = register_client_proxy(self.client_manager, client_proxy, context)

        if is_success:
            # Get iterators
            client_message_iterator = TimeoutIterator(
                iterator=request_iterator, reset_on_next=True
            )
            ins_wrapper_iterator = bridge.ins_wrapper_iterator()

            # All messages will be pushed to client bridge directly
            while True:
                try:
                    # Get ins_wrapper from bridge and yield server_message
                    ins_wrapper: InsWrapper = next(ins_wrapper_iterator)
                    server_message = ins_wrapper.server_message

                    server_message_chunks = batch_grpc_message(
                        message=server_message,
                        batch_size=self.max_message_length,
                        batch_message_type=ServerMessageChunk,
                        batch_message_header_size=SERVER_MESSAGE_BATCH_HEADER_SIZE
                    )
                    for server_message_chunk in server_message_chunks:
                        yield server_message_chunk

                    # Set current timeout, might be None
                    if ins_wrapper.timeout is not None:
                        client_message_iterator.set_timeout(ins_wrapper.timeout)

                    # Wait for client message
                    client_message = get_message_from_batches(
                        batch_messages_iterator=client_message_iterator,
                        message_type=ClientMessage
                    )

                    if client_message is client_message_iterator.get_sentinel():
                        # Important: calling `context.abort` in gRPC always
                        # raises an exception so that all code after the call to
                        # `context.abort` will not run. If subsequent code should
                        # be executed, the `rpc_termination_callback` can be used
                        # (as shown in the `register_client` function).
                        details = f"Timeout of {ins_wrapper.timeout}sec was exceeded."
                        context.abort(
                            code=grpc.StatusCode.DEADLINE_EXCEEDED,
                            details=details,
                        )
                        # This return statement is only for the linter so it understands
                        # that client_message in subsequent lines is not None
                        # It does not understand that `context.abort` will terminate
                        # this execution context by raising an exception.
                        return

                    bridge.set_res_wrapper(
                        res_wrapper=ResWrapper(client_message=client_message)
                    )
                except StopIteration:
                    break

    def JoinMinIO(
        self,
        request_iterator: Iterator[MessageMinIO],
        context: grpc.ServicerContext,
    ) -> Iterator[MessageMinIO]:
        cid: str = uuid.uuid4().hex
        bridge = self.grpc_bridge_factory()
        client_proxy = self.client_proxy_factory(cid, bridge)
        is_success = register_client_proxy(self.client_manager, client_proxy, context)

        if is_success:
            message_minio_iterator = TimeoutIterator(
                iterator=request_iterator, reset_on_next=True
            )
            ins_wrapper_iterator = bridge.ins_wrapper_iterator()

            while True:
                try:
                    # Get ins_wrapper from bridge and yield server_message
                    ins_wrapper: InsWrapper = next(ins_wrapper_iterator)
                    server_message = ins_wrapper.server_message

                    server_message_minio = push_message_to_minio(
                        minio_client=self.minio_client,
                        bucket_name=self.minio_bucket_name,
                        source_file=str(uuid.uuid4()),
                        message=server_message,
                        minio_message_type=MessageMinIO
                    )
                    yield server_message_minio

                    # Set current timeout, might be None
                    if ins_wrapper.timeout is not None:
                        message_minio_iterator.set_timeout(ins_wrapper.timeout)

                    client_message = get_message_from_minio(
                        minio_client=self.minio_client,
                        minio_message_iterator=message_minio_iterator,
                        message_type=ClientMessage
                    )
                    bridge.set_res_wrapper(res_wrapper=ResWrapper(client_message=client_message))

                except StopIteration:
                    break
