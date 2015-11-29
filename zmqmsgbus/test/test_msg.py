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

    def test_createZmqFilterForNamespace(self):
        self.assertEqual(b'hello/',
                         zmqmsgbus.createZmqFilter('hello/'))

    def test_createZmqFilterForTopic(self):
        self.assertEqual(b'hello/world\x00',
                         zmqmsgbus.createZmqFilter('hello/world'))

    def test_createZmqFilterAny(self):
        self.assertEqual(b'', zmqmsgbus.createZmqFilter(''))
