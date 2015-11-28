import zmq

context = zmq.Context()

in_sock = context.socket(zmq.SUB)
in_sock.bind("tcp://*:13370")
in_sock.bind("ipc://ipc/sink")
in_sock.setsockopt(zmq.SUBSCRIBE, b'')

out_sock = context.socket(zmq.PUB)
out_sock.bind("tcp://*:13371")
out_sock.bind("ipc://ipc/source")

zmq.device(zmq.FORWARDER, in_sock, out_sock)
