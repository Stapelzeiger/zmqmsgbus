import unittest
from unittest.mock import Mock, patch
import zmqmsgbus
import tempfile
import zmq
from logging import debug


class TestZmqMsg(unittest.TestCase):

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
        expected_msg = zmqmsgbus.encode('test', 'hello')
        self.out_sock.send.assert_called_once_with(expected_msg)

    def test_subscribe(self):
        self.bus.subscribe('test/topic')
        self.in_sock.setsockopt.assert_called_once_with(zmq.SUBSCRIBE,
                                                        b'test/topic\x00')

    def test_recv(self):
        self.in_sock.recv.return_value = zmqmsgbus.encode('test', 123)
        self.assertEqual(('test', 123), self.bus.recv())

