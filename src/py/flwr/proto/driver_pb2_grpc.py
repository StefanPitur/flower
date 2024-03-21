# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from flwr.proto import driver_pb2 as flwr_dot_proto_dot_driver__pb2
from flwr.proto import minio_pb2 as flwr_dot_proto_dot_minio__pb2


class DriverStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreateRun = channel.unary_stream(
                '/flwr.proto.Driver/CreateRun',
                request_serializer=flwr_dot_proto_dot_driver__pb2.CreateRunRequest.SerializeToString,
                response_deserializer=flwr_dot_proto_dot_driver__pb2.CreateRunResponseBatch.FromString,
                )
        self.CreateRunMinIO = channel.unary_unary(
                '/flwr.proto.Driver/CreateRunMinIO',
                request_serializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
                response_deserializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
                )
        self.GetNodes = channel.stream_stream(
                '/flwr.proto.Driver/GetNodes',
                request_serializer=flwr_dot_proto_dot_driver__pb2.GetNodesRequestBatch.SerializeToString,
                response_deserializer=flwr_dot_proto_dot_driver__pb2.GetNodesResponseBatch.FromString,
                )
        self.GetNodesMinIO = channel.unary_unary(
                '/flwr.proto.Driver/GetNodesMinIO',
                request_serializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
                response_deserializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
                )
        self.PushTaskIns = channel.stream_stream(
                '/flwr.proto.Driver/PushTaskIns',
                request_serializer=flwr_dot_proto_dot_driver__pb2.PushTaskInsRequestBatch.SerializeToString,
                response_deserializer=flwr_dot_proto_dot_driver__pb2.PushTaskInsResponseBatch.FromString,
                )
        self.PushTaskInsMinIO = channel.unary_unary(
                '/flwr.proto.Driver/PushTaskInsMinIO',
                request_serializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
                response_deserializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
                )
        self.PullTaskRes = channel.stream_stream(
                '/flwr.proto.Driver/PullTaskRes',
                request_serializer=flwr_dot_proto_dot_driver__pb2.PullTaskResRequestBatch.SerializeToString,
                response_deserializer=flwr_dot_proto_dot_driver__pb2.PullTaskResResponseBatch.FromString,
                )
        self.PullTaskResMinIO = channel.unary_unary(
                '/flwr.proto.Driver/PullTaskResMinIO',
                request_serializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
                response_deserializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
                )


class DriverServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CreateRun(self, request, context):
        """Request run_id
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateRunMinIO(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetNodes(self, request_iterator, context):
        """Return a set of nodes
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetNodesMinIO(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PushTaskIns(self, request_iterator, context):
        """Create one or more tasks
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PushTaskInsMinIO(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PullTaskRes(self, request_iterator, context):
        """Get task results
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PullTaskResMinIO(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DriverServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CreateRun': grpc.unary_stream_rpc_method_handler(
                    servicer.CreateRun,
                    request_deserializer=flwr_dot_proto_dot_driver__pb2.CreateRunRequest.FromString,
                    response_serializer=flwr_dot_proto_dot_driver__pb2.CreateRunResponseBatch.SerializeToString,
            ),
            'CreateRunMinIO': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateRunMinIO,
                    request_deserializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
                    response_serializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
            ),
            'GetNodes': grpc.stream_stream_rpc_method_handler(
                    servicer.GetNodes,
                    request_deserializer=flwr_dot_proto_dot_driver__pb2.GetNodesRequestBatch.FromString,
                    response_serializer=flwr_dot_proto_dot_driver__pb2.GetNodesResponseBatch.SerializeToString,
            ),
            'GetNodesMinIO': grpc.unary_unary_rpc_method_handler(
                    servicer.GetNodesMinIO,
                    request_deserializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
                    response_serializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
            ),
            'PushTaskIns': grpc.stream_stream_rpc_method_handler(
                    servicer.PushTaskIns,
                    request_deserializer=flwr_dot_proto_dot_driver__pb2.PushTaskInsRequestBatch.FromString,
                    response_serializer=flwr_dot_proto_dot_driver__pb2.PushTaskInsResponseBatch.SerializeToString,
            ),
            'PushTaskInsMinIO': grpc.unary_unary_rpc_method_handler(
                    servicer.PushTaskInsMinIO,
                    request_deserializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
                    response_serializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
            ),
            'PullTaskRes': grpc.stream_stream_rpc_method_handler(
                    servicer.PullTaskRes,
                    request_deserializer=flwr_dot_proto_dot_driver__pb2.PullTaskResRequestBatch.FromString,
                    response_serializer=flwr_dot_proto_dot_driver__pb2.PullTaskResResponseBatch.SerializeToString,
            ),
            'PullTaskResMinIO': grpc.unary_unary_rpc_method_handler(
                    servicer.PullTaskResMinIO,
                    request_deserializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
                    response_serializer=flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'flwr.proto.Driver', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Driver(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CreateRun(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/flwr.proto.Driver/CreateRun',
            flwr_dot_proto_dot_driver__pb2.CreateRunRequest.SerializeToString,
            flwr_dot_proto_dot_driver__pb2.CreateRunResponseBatch.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CreateRunMinIO(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/flwr.proto.Driver/CreateRunMinIO',
            flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
            flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetNodes(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/flwr.proto.Driver/GetNodes',
            flwr_dot_proto_dot_driver__pb2.GetNodesRequestBatch.SerializeToString,
            flwr_dot_proto_dot_driver__pb2.GetNodesResponseBatch.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetNodesMinIO(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/flwr.proto.Driver/GetNodesMinIO',
            flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
            flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def PushTaskIns(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/flwr.proto.Driver/PushTaskIns',
            flwr_dot_proto_dot_driver__pb2.PushTaskInsRequestBatch.SerializeToString,
            flwr_dot_proto_dot_driver__pb2.PushTaskInsResponseBatch.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def PushTaskInsMinIO(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/flwr.proto.Driver/PushTaskInsMinIO',
            flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
            flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def PullTaskRes(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/flwr.proto.Driver/PullTaskRes',
            flwr_dot_proto_dot_driver__pb2.PullTaskResRequestBatch.SerializeToString,
            flwr_dot_proto_dot_driver__pb2.PullTaskResResponseBatch.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def PullTaskResMinIO(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/flwr.proto.Driver/PullTaskResMinIO',
            flwr_dot_proto_dot_minio__pb2.MessageMinIO.SerializeToString,
            flwr_dot_proto_dot_minio__pb2.MessageMinIO.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
