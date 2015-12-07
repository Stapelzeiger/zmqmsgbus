import unittest
from unittest.mock import Mock, patch, call
import zmqmsgbus
import zmqmsgbus.msg
import zmqmsgbus.call
import tempfile
import zmq
from logging import debug


class TestBus(unittest.TestCase):

    @patch('zmqmsgbus.zmq.Context')
    def setUp(self, ctx_mock):
        socket_mocks = {zmq.SUB: Mock(zmq.Socket), zmq.PUB: Mock(zmq.Socket)}
        ctx_mock.return_value.socket.side_effect = lambda arg: socket_mocks[arg]
        self.ctx_mock = ctx_mock
        self.bus = zmqmsgbus.Bus(sub_addr='ipc://ipc/source',
                                 pub_addr='ipc://ipc/sink')
        self.in_sock = socket_mocks[zmq.SUB]
        self.out_sock = socket_mocks[zmq.PUB]

    def test_constructor_calls_connect(self):
        sub_addr = 'ipc://ipc/source'
        pub_addr = 'ipc://ipc/sink'
        zmqmsgbus.Bus(sub_addr=sub_addr, pub_addr=pub_addr)
        self.in_sock.connect.assert_called_once_with(sub_addr)
        self.out_sock.connect.assert_called_once_with(pub_addr)

    def test_publish(self):
        self.bus.publish('test', 'hello')
        expected_msg = zmqmsgbus.msg.encode('test', 'hello')
        self.out_sock.send.assert_called_once_with(expected_msg)

    def test_subscribe(self):
        self.bus.subscribe('test/topic')
        self.in_sock.setsockopt.assert_called_once_with(zmq.SUBSCRIBE,
                                                        b'test/topic\x00')

    def test_recv(self):
        self.in_sock.recv.return_value = zmqmsgbus.msg.encode('test', 123)
        self.assertEqual(('test', 123), self.bus.recv())


class TestNode(unittest.TestCase):

    @patch('zmqmsgbus.threading.Thread')
    def setUp(self, thread_mock):
        self.bus = Mock()
        self.node = zmqmsgbus.Node(self.bus)

    def test_publish(self):
        self.node.publish('topic', 123)
        self.bus.publish.assert_called_once_with('topic', 123)

    def test_multiple_subscribe_calls_subscribe_once(self):
        self.bus.subscribe = Mock()
        self.node._subscribe_to_topic('test')
        self.node._subscribe_to_topic('test')
        self.bus.subscribe.assert_called_once_with('test')


class TestNodeServiceCalls(unittest.TestCase):

    setUp = TestNode.setUp

    def test_call_with_address(self):
        self.bus.ctx.socket.return_value.recv.return_value = zmqmsgbus.call.encode_res(456)
        ret = self.node.call_with_address('test', 123, 'ipc://ipc/node/service')
        self.assertEqual(456, ret)

    def test_service_address_subscription_handler(self):
        self.node._service_address_subscription_handler('/service_address/test', 'addr')
        self.assertEqual(self.node.service_address_table['/test'], 'addr')

    def test_service_call_uses_address(self):
        self.node._service_address_subscription_handler('/service_address/test', 'addr')
        self.node.call_with_address = Mock()
        self.node.call('/test', 'foo')
        self.node.call_with_address.assert_called_once_with('/test', 'foo', 'addr')

    def test_service_call_returns_reply(self):
        self.node._service_address_subscription_handler('/service_address/test', 'addr')
        self.node.call_with_address = Mock()
        self.node.call_with_address.return_value = 123
        ret = self.node.call('/test', 'foo')
        self.assertEqual(123, ret)


class TestNodeMessagHandlers(unittest.TestCase):

    setUp = TestNode.setUp

    def test_topic_subscriptions_for_topic(self):
        sub = self.node._topic_possible_subscriptions('/test/sub/topic')
        debug(sub)
        self.assertEqual(sub, set(['/', '/test/', '/test/sub/', '/test/sub/topic']))

    def test_topic_subscriptions_for_namespace(self):
        sub = self.node._topic_possible_subscriptions('/test/sub/')
        debug(sub)
        self.assertEqual(sub, set(['/', '/test/', '/test/sub/']))

    def test_topic_subscriptions_for_root_namespace(self):
        sub = self.node._topic_possible_subscriptions('/')
        self.assertEqual(sub, set(['/']))

    def test_register_message_handler(self):
        handler = Mock()
        self.node.register_message_handler('test', handler)
        self.node._handle_message('test', 123)
        handler.assert_called_once_with('test', 123)

    def test_handle_namespace(self):
        handler = Mock()
        self.bus.subscribe = Mock()
        self.node.register_message_handler('test/', handler)
        self.bus.subscribe.assert_called_once_with('test/')
        self.node._handle_message('test/msg', 123)
        handler.assert_called_once_with('test/msg', 123)

    def test_register_multiple_message_handlers_same_topic(self):
        handler1 = Mock()
        handler2 = Mock()
        self.node.register_message_handler('test', handler1)
        self.node.register_message_handler('test', handler2)
        self.node._handle_message('test', 123)
        handler1.assert_called_once_with('test', 123)
        handler2.assert_called_once_with('test', 123)

    def test_register_message_handler_calls_subscribe(self):
        self.bus.subscribe = Mock()
        self.node.register_message_handler('test', lambda t, m: None)
        self.bus.subscribe.assert_called_once_with('test')


class TestNodeRecv(unittest.TestCase):

    setUp = TestNode.setUp

    @patch('zmqmsgbus.queue.Queue.get')
    def test_recv_calls_subscribe(self, queue_get_mock):
        self.bus.subscribe = Mock()
        self.node.recv('test')
        self.bus.subscribe.assert_called_once_with('test')

    @patch('zmqmsgbus.queue.Queue.put_nowait')
    def test_message_buffer_register(self, queue_put_mock):
        self.node._register_message_buffer_handler('test')
        self.node._handle_message('test', 123)
        queue_put_mock.assert_called_once_with(123)

    @patch('zmqmsgbus.queue.Queue.get')
    def test_message_buffer_get(self, queue_get_mock):
        self.node._register_message_buffer_handler('test')
        queue_get_mock.return_value = 123
        self.assertEqual(123, self.node._get_message_from_buffer('test', None))

    def test_message_buffer_queue(self):
        self.node._register_message_buffer_handler('test')
        self.node._handle_message('test', 123)
        self.assertEqual(123, self.node._get_message_from_buffer('test', None))

    @patch('zmqmsgbus.queue.Queue.get')
    def test_recv_returns_from_queue(self, queue_get_mock):
        queue_get_mock.return_value = 123
        self.assertEqual(123, self.node.recv('test'))

    @patch('zmqmsgbus.queue.Queue.get')
    def test_recv_timeout(self, queue_get_mock):
        self.node.recv('test', timeout=1)
        queue_get_mock.assert_called_once_with(timeout=1)


class TestNodeServiceHanlders(unittest.TestCase):

    setUp = TestNode.setUp

    def test_handle_service(self):
        handler = Mock()
        handler.return_value = 456
        self.node.register_service('/service', handler)
        self.assertEqual(zmqmsgbus.call.encode_res(456),
                         self.node._service_handle(zmqmsgbus.call.encode_req('/service', 123)))
        handler.assert_called_once_with(123)

    def test_hanle_nonexistant_service(self):
        self.assertEqual(zmqmsgbus.call.encode_res_error("service doesn't exist"),
                         self.node._service_handle(zmqmsgbus.call.encode_req('/service', None)))

    def test_hanle_failed_service(self):
        def handler(req):
            raise zmqmsgbus.ServiceFailed('yo')
        self.node.register_service('/service', handler)
        self.assertEqual(zmqmsgbus.call.encode_res_error('yo'),
                         self.node._service_handle(zmqmsgbus.call.encode_req('/service', None)))

    def test_publish_service_address(self):
        self.node.register_service('/service_a', Mock())
        self.node.register_service('/service_b', Mock())
        self.node.register_service('/test/service_c', Mock())
        self.node._publish_service_address()
        addr = self.node.serv_addr
        expeced_calls = [call('/service_address/service_a', addr)]
        expeced_calls = [call('/service_address/service_b', addr)]
        expeced_calls = [call('/service_address/test/service_c', addr)]
        self.bus.publish.assert_has_calls(expeced_calls)

    @patch('zmqmsgbus.uuid.uuid1')
    @patch('zmqmsgbus.threading.Thread')
    def test_connect_service_socket_no_addr(self, thd, uuid):
        uuid.return_value = 123456
        bus = Mock()
        node = zmqmsgbus.Node(bus, serv_addr=None)
        self.assertEqual('ipc://ipc/123456', node.serv_addr)

    @patch('zmqmsgbus.threading.Thread')
    def test_connect_service_socket_tcp_random_port(self, thd):
        bus = Mock()
        bus.ctx.socket.return_value.bind_to_random_port.return_value = 1234
        node = zmqmsgbus.Node(bus, serv_addr='tcp://localhost')
        self.assertEqual('tcp://localhost:1234', node.serv_addr)

    @patch('zmqmsgbus.threading.Thread')
    def test_connect_service_socket_given_addr(self, thd):
        bus = Mock()
        node = zmqmsgbus.Node(bus, serv_addr='tcp://localhost:123')
        self.assertEqual('tcp://localhost:123', node.serv_addr)
