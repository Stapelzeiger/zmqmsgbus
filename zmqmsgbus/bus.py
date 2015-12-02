import zmq
import zmqmsgbus.msg as msg
import zmqmsgbus.call as call
import threading
import queue
import time


class Bus:
    def __init__(self, sub_addr, pub_addr=None):
        self.ctx = zmq.Context()
        self.in_sock = self.ctx.socket(zmq.SUB)
        self.out_sock = self.ctx.socket(zmq.PUB)
        self.in_sock.connect(sub_addr)
        if pub_addr is not None:
            self.out_sock.connect(pub_addr)

    def __del__(self):
        self.ctx.destroy()

    def publish(self, topic, message):
        self.out_sock.send(msg.encode(topic, message))

    def subscribe(self, topic):
        self.in_sock.setsockopt(zmq.SUBSCRIBE, msg.createZmqFilter(topic))

    def recv(self, zmq_recv_flags=0):
        return msg.decode(self.in_sock.recv(flags=zmq_recv_flags))


class Node:
    MAX_MESSAGE_BUF_SZ = 1000

    def __init__(self, bus):
        self.bus = bus
        self.subscriptions = set()
        self.message_handlers = {}
        self.message_buffers = {}
        self.lock = threading.RLock()
        self.recv_deamon = threading.Thread(target=self._recv_msg_loop, daemon=True)
        self.recv_deamon.start()

    def __del__(self):
        self.recv_deamon.stop()

    def publish(self, topic, message):
        with self.lock:
            self.bus.publish(topic, message)

    def _register_message_buffer_handler(self, topic):
        if topic not in self.message_buffers:
            q = queue.Queue(self.MAX_MESSAGE_BUF_SZ)
            self.message_buffers[topic] = q

            def handler(_t, msg):
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    pass
            self.register_message_handler(topic, handler)

    def _get_message_from_buffer(self, topic, timeout):
        return self.message_buffers[topic].get(timeout=timeout)

    def _subscribe_to_topic(self, topic):
        if topic not in self.subscriptions:
            self.bus.subscribe(topic)
            self.subscriptions.add(topic)

    def recv(self, topic, timeout=None):
        with self.lock:
            self._subscribe_to_topic(topic)
            self._register_message_buffer_handler(topic)
        return self._get_message_from_buffer(topic, timeout)

    def call(self, service, request):
        with self.lock:
            pass # returns response

    def call_with_address(self, service, request, address):
        with self.lock:
            socket = self.bus.ctx.socket(zmq.REQ)
            socket.connect(address)
            socket.send(call.encode_req(service, request))
            s = socket.recv()
            return call.decode_res(s)

    def register_service(self, service, handler):
        with self.lock:
            pass

    def register_message_handler(self, topic, handler):
        with self.lock:
            self._subscribe_to_topic(topic)
            if topic in self.message_handlers:
                self.message_handlers[topic].append(handler)
            else:
                self.message_handlers[topic] = [handler]

    @staticmethod
    def _topic_possible_subscriptions(topic):
        """ returns the possible variations of a topic
            (list of the topic and the contatining namespaces)
        """
        topic_path = topic.split('/')
        return set(['/'.join(topic_path[0:i])+'/' for i in range(len(topic_path))] + [topic])

    def _handle_message(self, topic, message):
        possible_subscriptions = self._topic_possible_subscriptions(topic)
        for subscription in possible_subscriptions:
            if subscription in self.message_handlers:
                for handler in self.message_handlers[subscription]:
                    handler(topic, message)

    def _recv_msg_loop(self):
        while (1):
            try:
                with self.lock:
                    topic, message = self.bus.recv(zmq.NOBLOCK)
                    self._handle_message(topic, message)
            except zmq.ZMQError as err:
                if err.errno == zmq.EAGAIN:
                    time.sleep(0.001)
                else:
                    raise err
