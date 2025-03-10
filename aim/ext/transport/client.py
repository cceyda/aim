import logging
import os
import threading
import uuid
import weakref
from collections import defaultdict
from copy import deepcopy
from typing import Tuple

import aim.ext.transport.remote_tracking_pb2 as rpc_messages
import aim.ext.transport.remote_router_pb2 as router_messages
import aim.ext.transport.remote_tracking_pb2_grpc as remote_tracking_pb2_grpc
import aim.ext.transport.remote_router_pb2_grpc as remote_router_pb2_grpc

from aim.ext.transport.message_utils import pack_stream, unpack_stream, raise_exception
from aim.ext.transport.rpc_queue import RpcQueueWithRetry
from aim.ext.transport.heartbeat import RPCHeartbeatSender
from aim.ext.transport.config import (
    AIM_CLIENT_SSL_CERTIFICATES_FILE,
    AIM_RT_MAX_MESSAGE_SIZE,
    AIM_RT_DEFAULT_MAX_MESSAGE_SIZE,
    AIM_CLIENT_QUEUE_MAX_MEMORY,
)
from aim.storage.treeutils import encode_tree, decode_tree


DEFAULT_RETRY_INTERVAL = 0.1  # 100 ms
DEFAULT_RETRY_COUNT = 5

logger = logging.getLogger(__name__)


class Client:
    _thread_local = threading.local()

    # per run queues. based on run's hash
    _queues = defaultdict(lambda: RpcQueueWithRetry(
        'remote_tracker', max_queue_memory=os.getenv(AIM_CLIENT_QUEUE_MAX_MEMORY, 1024 * 1024 * 1024),
        retry_count=DEFAULT_RETRY_COUNT, retry_interval=DEFAULT_RETRY_INTERVAL))

    def __init__(self, remote_path: str):
        # temporary workaround for M1 build
        import grpc

        self._id = str(uuid.uuid4())
        self._remote_path = remote_path

        self._resource_pool = weakref.WeakValueDictionary()

        ssl_certfile = os.getenv(AIM_CLIENT_SSL_CERTIFICATES_FILE)
        msg_max_size = int(os.getenv(AIM_RT_MAX_MESSAGE_SIZE, AIM_RT_DEFAULT_MAX_MESSAGE_SIZE))
        options = [
            ('grpc.max_send_message_length', msg_max_size),
            ('grpc.max_receive_message_length', msg_max_size)
        ]

        # open a channel with router
        if ssl_certfile:
            with open(ssl_certfile, 'rb') as f:
                root_certificates = grpc.ssl_channel_credentials(f.read())
            self._remote_router_channel = grpc.secure_channel(remote_path, root_certificates, options=options)
        else:
            self._remote_router_channel = grpc.insecure_channel(remote_path, options=options)
        self._remote_router_stub = remote_router_pb2_grpc.RemoteRouterServiceStub(self._remote_router_channel)

        # check client/server version compatibility
        self._check_remote_version_compatibility()

        # get the available worker address
        self._remote_worker_address = self._get_worker_address()

        # open a channel with worker for further communication
        if ssl_certfile:
            self._remote_channel = grpc.secure_channel(self._remote_worker_address,
                                                       root_certificates,
                                                       options=options)
        else:
            self._remote_channel = grpc.insecure_channel(self._remote_worker_address, options=options)

        self._remote_stub = remote_tracking_pb2_grpc.RemoteTrackingServiceStub(self._remote_channel)

        self._heartbeat_sender = RPCHeartbeatSender(self)
        self._heartbeat_sender.start()
        self._thread_local.atomic_instructions = None

    def reinitialize_resource(self, handler):
        # write some request to get a resource on server side with an already given handler
        resource = self._resource_pool[handler]
        self.get_resource_handler(resource, resource.resource_type, handler, resource.init_args)

    def _reinitialize_all_resources(self):
        handlers_list = list(self._resource_pool.keys())
        for handler in handlers_list:
            self.reinitialize_resource(handler)

    def _check_remote_version_compatibility(self):
        from aim.__version__ import __version__ as client_version
        import grpc

        error_message_template = 'The Aim Remote tracking server version ({}) '\
                                 'is not compatible with the Aim client version ({}).'\
                                 'Please upgrade either the Aim Client or the Aim Remote.'

        warning_message_template = 'The Aim Remote tracking server version ({}) ' \
                                   'and the Aim client version ({}) do not match.' \
                                   'Consider upgrading either the client or remote tracking server.'

        try:
            remote_version = self.get_version()
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNIMPLEMENTED:
                remote_version = '<3.14.0'
            else:
                raise

        # server doesn't yet have the `get_version()` method implemented
        if remote_version == '<3.14.0':
            RuntimeError(error_message_template.format(remote_version, client_version))

        # compare versions
        if client_version == remote_version:
            return

        # if the server has a newer version always force to upgrade the client
        if client_version < remote_version:
            raise RuntimeError(error_message_template.format(remote_version, client_version))

        # for other mismatching versions throw a warning for now
        logger.warning(warning_message_template.format(remote_version, client_version))
        # further incompatibility list will be added manually

    def _get_worker_address(self):
        worker_host = self._remote_path.rsplit(':', maxsplit=1)[0]
        worker_port = self._get_worker_port()
        return f'{worker_host}:{worker_port}'

    def _get_worker_port(self):
        request = router_messages.ConnectRequest(
            client_uri=self.uri
        )
        response = self._remote_router_stub.connect(request)
        if response.status == router_messages.ConnectResponse.Status.ERROR:
            raise_exception(response.exception)
        return response.port

    def client_heartbeat(self):
        request = router_messages.HeartbeatRequest(
            client_uri=self.uri,
        )
        response = self._remote_router_stub.client_heartbeat(request)
        return response

    def reconnect(self):
        request = router_messages.ReconnectRequest(
            client_uri=self.uri
        )
        response = self._remote_router_stub.reconnect(request)
        if response.status == router_messages.ReconnectResponse.Status.ERROR:
            raise_exception(response.exception)

        self._reinitialize_all_resources()

        return response

    def disconnect(self):
        request = router_messages.DisconnectRequest(
            client_uri=self.uri
        )
        response = self._remote_router_stub.disconnect(request)

        if response.status == router_messages.DisconnectResponse.Status.ERROR:
            raise_exception(response.exception)

    def get_version(self,):
        request = router_messages.VersionRequest()
        response = self._remote_router_stub.get_version(request)

        if response.status == router_messages.VersionResponse.Status.ERROR:
            raise_exception(response.exception)
        return response.version

    def get_resource_handler(self, resource, resource_type, handler='', args=()):
        request = rpc_messages.ResourceRequest(
            resource_type=resource_type,
            handler=handler,
            client_uri=self.uri,
            args=args
        )
        response = self.remote.get_resource(request)
        if response.status == rpc_messages.ResourceResponse.Status.ERROR:
            raise_exception(response.exception)

        self._resource_pool[response.handler] = resource

        return response.handler

    def release_resource(self, resource_handler):
        request = rpc_messages.ReleaseResourceRequest(
            handler=resource_handler,
            client_uri=self.uri
        )
        response = self.remote.release_resource(request)
        if response.status == rpc_messages.ReleaseResourceResponse.Status.ERROR:
            raise_exception(response.exception)

        del self._resource_pool[resource_handler]

    def run_instruction(self, queue_id, resource, method, args=(), is_write_only=False):
        args = deepcopy(args)

        # self._thread_local can be empty in the 'clean up' phase.
        if getattr(self._thread_local, 'atomic_instructions', None) is not None:
            assert is_write_only
            self._thread_local.atomic_instructions.append((resource, method, args))
            return

        if is_write_only:
            assert queue_id != -1
            self.get_queue(queue_id).register_task(
                self,
                self._run_write_instructions, list(encode_tree([(resource, method, args)])))
            return

        return self._run_read_instructions(queue_id, resource, method, args)

    def _run_read_instructions(self, queue_id, resource, method, args):
        def message_stream_generator():
            header = rpc_messages.InstructionRequest(
                header=rpc_messages.RequestHeader(
                    version='0.1',
                    handler=resource,
                    client_uri=self.uri,
                    method_name=method
                )
            )
            yield header

            stream = pack_stream(encode_tree(args))
            for chunk in stream:
                yield rpc_messages.InstructionRequest(message=chunk)

        if queue_id != -1:
            self.get_queue(queue_id).wait_for_finish()
        resp = self.remote.run_instruction(message_stream_generator())
        status_msg = next(resp)

        assert status_msg.WhichOneof('instruction') == 'header'
        if status_msg.header.status == rpc_messages.ResponseHeader.Status.ERROR:
            raise_exception(status_msg.header.exception)
        return decode_tree(unpack_stream(resp))

    def _run_write_instructions(self, instructions: [Tuple[bytes, bytes]]):
        stream = pack_stream(iter(instructions))

        def message_stream_generator():
            for chunk in stream:
                yield rpc_messages.WriteInstructionsRequest(
                    version='0.1',
                    client_uri=self.uri,
                    message=chunk
                )

        response = self.remote.run_write_instructions(message_stream_generator())
        if response.status == rpc_messages.WriteInstructionsResponse.Status.ERROR:
            raise_exception(response.header.exception)

    def start_instructions_batch(self):
        self._thread_local.atomic_instructions = []

    def flush_instructions_batch(self, queue_id):
        if self._thread_local.atomic_instructions is None:
            return

        self.get_queue(queue_id).register_task(
            self,
            self._run_write_instructions, list(encode_tree(self._thread_local.atomic_instructions)))
        self._thread_local.atomic_instructions = None

    @property
    def remote(self):  # access to low-level interface
        return self._remote_stub

    @property
    def uri(self):
        return self._id

    @property
    def remote_path(self):
        return self._remote_path

    def get_queue(self, queue_id):
        return self._queues[queue_id]

    def remove_queue(self, queue_id):
        del self._queues[queue_id]
