import unittest
import msgpack
import zmqmsgbus


class TestZmqMsg(unittest.TestCase):
    def test_encode(self):
        self.assertEqual(b'hello\0'+msgpack.packb(123),
                         zmqmsgbus.encode('hello', 123))

    def test_decode(self):
        self.assertEqual(('hello', [1, 2, 3]),
                         zmqmsgbus.decode(zmqmsgbus.encode('hello', [1, 2, 3])))

    def test_createZmqFilter(self):
        self.assertEqual(b'hello/',
                         zmqmsgbus.createZmqFilter('hello/'))
        self.assertEqual(b'hello/world\x00',
                         zmqmsgbus.createZmqFilter('hello/world'))
