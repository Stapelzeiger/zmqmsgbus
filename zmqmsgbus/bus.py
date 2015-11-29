import zmq
import zmqmsgbus


class Bus:
    def __init__(self, sub_addr, pub_addr):
        self.ctx = zmq.Context()
        self.in_sock = self.ctx.socket(zmq.SUB)
        self.out_sock = self.ctx.socket(zmq.PUB)
        self.in_sock.connect(sub_addr)
        self.out_sock.connect(pub_addr)

    def publish(self, topic, message):
        self.out_sock.send(zmqmsgbus.encode(topic, message))

    def subscribe(self, topic):
        self.in_sock.setsockopt(zmq.SUBSCRIBE, zmqmsgbus.createZmqFilter(topic))

    def recv(self):
        return zmqmsgbus.decode(self.in_sock.recv())
