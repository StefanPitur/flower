"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import flwr.proto.fleet_pb2
import flwr.proto.minio_pb2
import grpc
import typing

class FleetStub:
    def __init__(self, channel: grpc.Channel) -> None: ...
    CreateNode: grpc.UnaryStreamMultiCallable[
        flwr.proto.fleet_pb2.CreateNodeRequest,
        flwr.proto.fleet_pb2.CreateNodeResponseBatch]

    CreateNodeMinIO: grpc.UnaryUnaryMultiCallable[
        flwr.proto.minio_pb2.MessageMinIO,
        flwr.proto.minio_pb2.MessageMinIO]

    DeleteNode: grpc.StreamUnaryMultiCallable[
        flwr.proto.fleet_pb2.DeleteNodeRequest,
        flwr.proto.fleet_pb2.DeleteNodeResponse]

    DeleteNodeMinIO: grpc.UnaryUnaryMultiCallable[
        flwr.proto.minio_pb2.MessageMinIO,
        flwr.proto.minio_pb2.MessageMinIO]

    PullTaskIns: grpc.StreamStreamMultiCallable[
        flwr.proto.fleet_pb2.PullTaskInsRequestBatch,
        flwr.proto.fleet_pb2.PullTaskInsResponseBatch]
    """Retrieve one or more tasks, if possible

    HTTP API path: /api/v1/fleet/pull-task-ins
    """

    PullTaskInsMinIO: grpc.UnaryUnaryMultiCallable[
        flwr.proto.minio_pb2.MessageMinIO,
        flwr.proto.minio_pb2.MessageMinIO]

    PushTaskRes: grpc.StreamStreamMultiCallable[
        flwr.proto.fleet_pb2.PushTaskResRequestBatch,
        flwr.proto.fleet_pb2.PushTaskResResponseBatch]
    """Complete one or more tasks, if possible

    HTTP API path: /api/v1/fleet/push-task-res
    """

    PushTaskResMinIO: grpc.UnaryUnaryMultiCallable[
        flwr.proto.minio_pb2.MessageMinIO,
        flwr.proto.minio_pb2.MessageMinIO]


class FleetServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def CreateNode(self,
        request: flwr.proto.fleet_pb2.CreateNodeRequest,
        context: grpc.ServicerContext,
    ) -> typing.Iterator[flwr.proto.fleet_pb2.CreateNodeResponseBatch]: ...

    @abc.abstractmethod
    def CreateNodeMinIO(self,
        request: flwr.proto.minio_pb2.MessageMinIO,
        context: grpc.ServicerContext,
    ) -> flwr.proto.minio_pb2.MessageMinIO: ...

    @abc.abstractmethod
    def DeleteNode(self,
        request_iterator: typing.Iterator[flwr.proto.fleet_pb2.DeleteNodeRequest],
        context: grpc.ServicerContext,
    ) -> flwr.proto.fleet_pb2.DeleteNodeResponse: ...

    @abc.abstractmethod
    def DeleteNodeMinIO(self,
        request: flwr.proto.minio_pb2.MessageMinIO,
        context: grpc.ServicerContext,
    ) -> flwr.proto.minio_pb2.MessageMinIO: ...

    @abc.abstractmethod
    def PullTaskIns(self,
        request_iterator: typing.Iterator[flwr.proto.fleet_pb2.PullTaskInsRequestBatch],
        context: grpc.ServicerContext,
    ) -> typing.Iterator[flwr.proto.fleet_pb2.PullTaskInsResponseBatch]:
        """Retrieve one or more tasks, if possible

        HTTP API path: /api/v1/fleet/pull-task-ins
        """
        pass

    @abc.abstractmethod
    def PullTaskInsMinIO(self,
        request: flwr.proto.minio_pb2.MessageMinIO,
        context: grpc.ServicerContext,
    ) -> flwr.proto.minio_pb2.MessageMinIO: ...

    @abc.abstractmethod
    def PushTaskRes(self,
        request_iterator: typing.Iterator[flwr.proto.fleet_pb2.PushTaskResRequestBatch],
        context: grpc.ServicerContext,
    ) -> typing.Iterator[flwr.proto.fleet_pb2.PushTaskResResponseBatch]:
        """Complete one or more tasks, if possible

        HTTP API path: /api/v1/fleet/push-task-res
        """
        pass

    @abc.abstractmethod
    def PushTaskResMinIO(self,
        request: flwr.proto.minio_pb2.MessageMinIO,
        context: grpc.ServicerContext,
    ) -> flwr.proto.minio_pb2.MessageMinIO: ...


def add_FleetServicer_to_server(servicer: FleetServicer, server: grpc.Server) -> None: ...
