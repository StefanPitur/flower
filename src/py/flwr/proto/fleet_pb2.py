# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: flwr/proto/fleet.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from flwr.proto import minio_pb2 as flwr_dot_proto_dot_minio__pb2
from flwr.proto import node_pb2 as flwr_dot_proto_dot_node__pb2
from flwr.proto import task_pb2 as flwr_dot_proto_dot_task__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x16\x66lwr/proto/fleet.proto\x12\nflwr.proto\x1a\x16\x66lwr/proto/minio.proto\x1a\x15\x66lwr/proto/node.proto\x1a\x15\x66lwr/proto/task.proto\"6\n\x17\x43reateNodeResponseBatch\x12\x1b\n\x13message_batch_bytes\x18\x01 \x01(\x0c\"\x13\n\x11\x43reateNodeRequest\"4\n\x12\x43reateNodeResponse\x12\x1e\n\x04node\x18\x01 \x01(\x0b\x32\x10.flwr.proto.Node\"5\n\x16\x44\x65leteNodeRequestBatch\x12\x1b\n\x13message_batch_bytes\x18\x01 \x01(\x0c\"3\n\x11\x44\x65leteNodeRequest\x12\x1e\n\x04node\x18\x01 \x01(\x0b\x32\x10.flwr.proto.Node\"\x14\n\x12\x44\x65leteNodeResponse\"6\n\x17PullTaskInsRequestBatch\x12\x1b\n\x13message_batch_bytes\x18\x01 \x01(\x0c\"7\n\x18PullTaskInsResponseBatch\x12\x1b\n\x13message_batch_bytes\x18\x01 \x01(\x0c\"F\n\x12PullTaskInsRequest\x12\x1e\n\x04node\x18\x01 \x01(\x0b\x32\x10.flwr.proto.Node\x12\x10\n\x08task_ids\x18\x02 \x03(\t\"k\n\x13PullTaskInsResponse\x12(\n\treconnect\x18\x01 \x01(\x0b\x32\x15.flwr.proto.Reconnect\x12*\n\rtask_ins_list\x18\x02 \x03(\x0b\x32\x13.flwr.proto.TaskIns\"6\n\x17PushTaskResRequestBatch\x12\x1b\n\x13message_batch_bytes\x18\x01 \x01(\x0c\"7\n\x18PushTaskResResponseBatch\x12\x1b\n\x13message_batch_bytes\x18\x01 \x01(\x0c\"@\n\x12PushTaskResRequest\x12*\n\rtask_res_list\x18\x01 \x03(\x0b\x32\x13.flwr.proto.TaskRes\"\xae\x01\n\x13PushTaskResResponse\x12(\n\treconnect\x18\x01 \x01(\x0b\x32\x15.flwr.proto.Reconnect\x12=\n\x07results\x18\x02 \x03(\x0b\x32,.flwr.proto.PushTaskResResponse.ResultsEntry\x1a.\n\x0cResultsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\r:\x02\x38\x01\"\x1e\n\tReconnect\x12\x11\n\treconnect\x18\x01 \x01(\x04\x32\x94\x05\n\x05\x46leet\x12T\n\nCreateNode\x12\x1d.flwr.proto.CreateNodeRequest\x1a#.flwr.proto.CreateNodeResponseBatch\"\x00\x30\x01\x12G\n\x0f\x43reateNodeMinIO\x12\x18.flwr.proto.MessageMinIO\x1a\x18.flwr.proto.MessageMinIO\"\x00\x12O\n\nDeleteNode\x12\x1d.flwr.proto.DeleteNodeRequest\x1a\x1e.flwr.proto.DeleteNodeResponse\"\x00(\x01\x12G\n\x0f\x44\x65leteNodeMinIO\x12\x18.flwr.proto.MessageMinIO\x1a\x18.flwr.proto.MessageMinIO\"\x00\x12^\n\x0bPullTaskIns\x12#.flwr.proto.PullTaskInsRequestBatch\x1a$.flwr.proto.PullTaskInsResponseBatch\"\x00(\x01\x30\x01\x12H\n\x10PullTaskInsMinIO\x12\x18.flwr.proto.MessageMinIO\x1a\x18.flwr.proto.MessageMinIO\"\x00\x12^\n\x0bPushTaskRes\x12#.flwr.proto.PushTaskResRequestBatch\x1a$.flwr.proto.PushTaskResResponseBatch\"\x00(\x01\x30\x01\x12H\n\x10PushTaskResMinIO\x12\x18.flwr.proto.MessageMinIO\x1a\x18.flwr.proto.MessageMinIO\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'flwr.proto.fleet_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_PUSHTASKRESRESPONSE_RESULTSENTRY']._options = None
  _globals['_PUSHTASKRESRESPONSE_RESULTSENTRY']._serialized_options = b'8\001'
  _globals['_CREATENODERESPONSEBATCH']._serialized_start=108
  _globals['_CREATENODERESPONSEBATCH']._serialized_end=162
  _globals['_CREATENODEREQUEST']._serialized_start=164
  _globals['_CREATENODEREQUEST']._serialized_end=183
  _globals['_CREATENODERESPONSE']._serialized_start=185
  _globals['_CREATENODERESPONSE']._serialized_end=237
  _globals['_DELETENODEREQUESTBATCH']._serialized_start=239
  _globals['_DELETENODEREQUESTBATCH']._serialized_end=292
  _globals['_DELETENODEREQUEST']._serialized_start=294
  _globals['_DELETENODEREQUEST']._serialized_end=345
  _globals['_DELETENODERESPONSE']._serialized_start=347
  _globals['_DELETENODERESPONSE']._serialized_end=367
  _globals['_PULLTASKINSREQUESTBATCH']._serialized_start=369
  _globals['_PULLTASKINSREQUESTBATCH']._serialized_end=423
  _globals['_PULLTASKINSRESPONSEBATCH']._serialized_start=425
  _globals['_PULLTASKINSRESPONSEBATCH']._serialized_end=480
  _globals['_PULLTASKINSREQUEST']._serialized_start=482
  _globals['_PULLTASKINSREQUEST']._serialized_end=552
  _globals['_PULLTASKINSRESPONSE']._serialized_start=554
  _globals['_PULLTASKINSRESPONSE']._serialized_end=661
  _globals['_PUSHTASKRESREQUESTBATCH']._serialized_start=663
  _globals['_PUSHTASKRESREQUESTBATCH']._serialized_end=717
  _globals['_PUSHTASKRESRESPONSEBATCH']._serialized_start=719
  _globals['_PUSHTASKRESRESPONSEBATCH']._serialized_end=774
  _globals['_PUSHTASKRESREQUEST']._serialized_start=776
  _globals['_PUSHTASKRESREQUEST']._serialized_end=840
  _globals['_PUSHTASKRESRESPONSE']._serialized_start=843
  _globals['_PUSHTASKRESRESPONSE']._serialized_end=1017
  _globals['_PUSHTASKRESRESPONSE_RESULTSENTRY']._serialized_start=971
  _globals['_PUSHTASKRESRESPONSE_RESULTSENTRY']._serialized_end=1017
  _globals['_RECONNECT']._serialized_start=1019
  _globals['_RECONNECT']._serialized_end=1049
  _globals['_FLEET']._serialized_start=1052
  _globals['_FLEET']._serialized_end=1712
# @@protoc_insertion_point(module_scope)
