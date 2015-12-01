import unittest
from unittest.mock import Mock, patch
import zmqmsgbus
import zmqmsgbus.msg
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

    def setUp(self):
        self.bus = Mock()
        self.node = zmqmsgbus.Node(self.bus)

    def test_publish(self):
        self.node.publish('topic', 123)
        self.bus.publish.assert_called_once_with('topic', 123)

    def test_multiple_subscribe_calls_subscribe_once(self):
        self.node._subscribe_to_topic('test')
        self.node._subscribe_to_topic('test')
        self.bus.subscribe.assert_called_once_with('test')


class TestNodeMessagHandlers(TestNode):

    def test_register_message_handler(self):
        handler = Mock()
        self.node.register_message_handler('test', handler)
        self.node._handle_message('test', 123)
        handler.assert_called_once_with('test', 123)

    def test_register_multiple_message_handlers_same_topic(self):
        handler1 = Mock()
        handler2 = Mock()
        self.node.register_message_handler('test', handler1)
        self.node.register_message_handler('test', handler2)
        self.node._handle_message('test', 123)
        handler1.assert_called_once_with('test', 123)
        handler2.assert_called_once_with('test', 123)

    def test_register_message_handler_calls_subscribe(self):
        self.node.register_message_handler('test', lambda t, m: None)
        self.bus.subscribe.assert_called_once_with('test')


class TestNodeRecv(TestNode):

    @patch('zmqmsgbus.Queue.get')
    def test_recv_calls_subscribe(self, queue_get_mock):
        self.node.recv('test')
        self.bus.subscribe.assert_called_once_with('test')

    @patch('zmqmsgbus.Queue.put_nowait')
    def test_message_buffer_register(self, queue_put_mock):
        self.node._register_message_buffer_handler('test')
        self.node._handle_message('test', 123)
        queue_put_mock.assert_called_once_with(123)

    @patch('zmqmsgbus.Queue.get')
    def test_message_buffer_get(self, queue_get_mock):
        self.node._register_message_buffer_handler('test')
        queue_get_mock.return_value = 123
        self.assertEqual(123, self.node._get_message_from_buffer('test', None))

    def test_message_buffer_queue(self):
        self.node._register_message_buffer_handler('test')
        self.node._handle_message('test', 123)
        self.assertEqual(123, self.node._get_message_from_buffer('test', None))

    @patch('zmqmsgbus.Queue.get')
    def test_recv_returns_from_queue(self, queue_get_mock):
        queue_get_mock.return_value = 123
        self.assertEqual(123, self.node.recv('test'))

    @patch('zmqmsgbus.Queue.get')
    def test_recv_timeout(self, queue_get_mock):
        self.node.recv('test', timeout=1)
        queue_get_mock.assert_called_once_with(timeout=1)
