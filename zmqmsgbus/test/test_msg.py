import unittest
import msgpack
import zmqmsgbus.msg as msg


class TestZmqMsg(unittest.TestCase):
    def test_encode(self):
        self.assertEqual(b'hello\0'+msgpack.packb(123),
                         msg.encode('hello', 123))

    def test_decode(self):
        self.assertEqual(('hello', [1, 2, 3]),
                         msg.decode(msg.encode('hello', [1, 2, 3])))

    def test_createZmqFilterForNamespace(self):
        self.assertEqual(b'hello/',
                         msg.createZmqFilter('hello/'))

    def test_createZmqFilterForTopic(self):
        self.assertEqual(b'hello/world\x00',
                         msg.createZmqFilter('hello/world'))

    def test_createZmqFilterAny(self):
        self.assertEqual(b'', msg.createZmqFilter(''))
