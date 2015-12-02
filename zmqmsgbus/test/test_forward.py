import unittest
from unittest.mock import Mock, call, patch
import zmqmsgbus
import zmqmsgbus.msg as msg


class TestMapStringOrListOfStrings(unittest.TestCase):

    def test_str(self):
        mock = Mock()
        zmqmsgbus.map_string_or_list_of_strings(mock, 'address')
        mock.assert_called_once_with('address')

    def test_list(self):
        mock = Mock()
        addrs = ['address1', 'address2']
        zmqmsgbus.map_string_or_list_of_strings(mock, addrs)
        mock.assert_has_calls([call(a) for a in addrs])


class TestForward(unittest.TestCase):

    @patch('zmqmsgbus.zmq.Context')
    @patch('zmqmsgbus.zmq.device')
    def test_forward_everything(self, dev, ctx):
        zmqmsgbus.forward('from_addr', 'to_addr')
        dev.assert_called_once_with(zmqmsgbus.zmq.FORWARDER,
                                    ctx.return_value.socket.return_value,
                                    ctx.return_value.socket.return_value)
        sock = ctx.return_value.socket.return_value
        sock.connect.assert_has_calls([call('from_addr'), call('to_addr')],
                                   any_order=True)


class TestRename(unittest.TestCase):

    def test_rename(self):
        buf = zmqmsgbus.rename_message(msg.encode('/old/topic', 123),
                                       '/old/', '/new/')
        self.assertEqual(('/new/topic', 123), msg.decode(buf))
