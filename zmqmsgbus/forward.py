import zmq


def forward(from_list, to_list):
    context = zmq.Context()
    in_sock = context.socket(zmq.SUB)
    for addr in from_list:
        in_sock.bind(addr)
    in_sock.setsockopt(zmq.SUBSCRIBE, b'')
    out_sock = context.socket(zmq.PUB)
    for addr in to_list:
        out_sock.bind(addr)
    zmq.device(zmq.FORWARDER, in_sock, out_sock)
