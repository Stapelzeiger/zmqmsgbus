import msgpack


def encode(topic, msg):
    return topic.encode('utf8') + b'\0' + msgpack.packb(msg, use_bin_type=True)


def decode(buf):
    topic, msg = buf.split(b'\0', 1)
    return (topic.decode('utf8'), msgpack.unpackb(msg, encoding='utf8'))


def createZmqFilter(topic):
    """
    Creates a ZeroMQ subscribe filter
    if topic ends with a '/', the filter matches any topic in the namespace
    """
    if topic == '':
        return b''  # this will match any message
    elif topic.endswith('/'):
        return topic.encode('utf8')
    else:
        return topic.encode('utf8') + b'\0'
