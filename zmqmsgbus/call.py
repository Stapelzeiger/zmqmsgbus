import msgpack


class CallFailed(Exception):
    """ This exception is raised when a call fails """
    pass


def encode_req(service, req):
    return msgpack.packb([service, req])


def decode_req(buf):
    return msgpack.unpackb(buf, encoding='utf8')


def encode_res(res):
    return msgpack.packb(['ok', res])


def encode_res_error(err):
    return msgpack.packb(['err', err])


def decode_res(buf):
    stat, res = msgpack.unpackb(buf, encoding='utf8')
    if stat == 'ok':
        return res
    else:
        raise CallFailed(res)
