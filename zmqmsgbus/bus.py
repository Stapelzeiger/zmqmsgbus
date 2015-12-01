import zmq
import zmqmsgbus
from queue import Queue


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


class Node:
    MAX_MESSAGE_BUF_SZ = 32

    def __init__(self, bus):
        self.bus = bus
        self.subscriptions = set()
        self.message_handlers = {}
        self.message_buffers = {}

    def publish(self, topic, message):
        self.bus.publish(topic, message)

    def _register_message_buffer_handler(self, topic):
        if topic not in self.message_buffers:
            self.message_buffers[topic] = Queue(self.MAX_MESSAGE_BUF_SZ)
            handler = lambda _t, msg: self.message_buffers[topic].put_nowait(msg)
            self.register_message_handler(topic, handler)

    def _get_message_from_buffer(self, topic):
        return self.message_buffers[topic].get()

    def _subscribe_to_topic(self, topic):
        if topic not in self.subscriptions:
            self.bus.subscribe(topic)
            self.subscriptions.add(topic)

    def recv(self, topic):
        self._subscribe_to_topic(topic)
        self._register_message_buffer_handler(topic)
        return self._get_message_from_buffer(topic)

    def call(self, service, request):
        pass # returns response

    def register_service(self, service, handler):
        pass

    def register_message_handler(self, topic, handler):
        self._subscribe_to_topic(topic)
        if topic in self.message_handlers:
            self.message_handlers[topic].append(handler)
        else:
            self.message_handlers[topic] = [handler]

    def _handle_message(self, topic, message):
        if topic in self.message_handlers: #todo call also partial matches
            for handler in self.message_handlers[topic]:
                handler(topic, message)
