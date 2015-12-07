import unittest
import msgpack
import zmqmsgbus.call as call


class TestZmqCall(unittest.TestCase):
    def test_encode_req(self):
        self.assertEqual(msgpack.packb(['hello', 123]),
                         call.encode_req('hello', 123))

    def test_decode_req(self):
        self.assertEqual(['hello', 123],
                         call.decode_req(call.encode_req('hello', 123)))

    def test_encode_res(self):
        self.assertEqual(msgpack.packb(['ok', 123]),
                         call.encode_res(123))

    def test_encode_err(self):
        self.assertEqual(msgpack.packb(['err', 'error message']),
                         call.encode_res_error('error message'))

    def test_decode_res(self):
        self.assertEqual(123,
                         call.decode_res(call.encode_res(123)))

    def test_decode_res_err(self):
        with self.assertRaises(call.CallFailed):
            call.decode_res(call.encode_res_error('error'))
