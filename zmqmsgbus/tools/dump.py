import sys
import zmq
import zmqmsgbus.msg


if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    # socket.connect("tcp://localhost:13371")
    socket.connect("ipc://ipc/source")

    for topic in sys.argv[1:]:
        socket.setsockopt(zmq.SUBSCRIBE, zmqmsgbus.msg.createZmqFilter(topic))
    if len(sys.argv) == 1:
        socket.setsockopt(zmq.SUBSCRIBE, b'')

    while True:
        print(*zmqmsgbus.msg.decode(socket.recv()))
