import zmq
import zmqmsgbus.msg as msg
import zmqmsgbus.call as call
import threading
import queue
import time
import uuid


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


class ServiceFailed(Exception):
    """ This exception should be raised by a service hanlder if it fails """
    pass


class Node:
    MAX_MESSAGE_BUF_SZ = 1000

    def __init__(self, bus, serv_addr=None):
        self.bus = bus
        self.lock = threading.RLock()

        self.subscriptions = set()
        self.message_handlers = {}
        self.message_buffers = {}
        self.service_handlers = {}
        self.service_address_table = {}
        self.register_message_handler('/service_address/',
                lambda t, m: self._service_address_subscription_handler(t, m))

        self._connect_service_socket(serv_addr)

        self.recv_deamon = threading.Thread(target=self._recv_msg_loop, daemon=True)
        self.recv_deamon.start()
        self.publish_deamon = threading.Thread(target=self._publish_service_address_loop, daemon=True)
        self.publish_deamon.start()
        self.service_deamon = threading.Thread(target=self._handle_service_loop, daemon=True)
        self.service_deamon.start()

    def _connect_service_socket(self, serv_addr):
        self.service_sock = self.bus.ctx.socket(zmq.REP)
        if serv_addr is None:
            self.serv_addr = "ipc://ipc/" + str(uuid.uuid1())
            self.service_sock.bind(self.serv_addr)
        elif (serv_addr.startswith('tcp://') and
              not serv_addr.rsplit(':', 1)[1].isdigit()):
            port = self.service_sock.bind_to_random_port(serv_addr)
            self.serv_addr = serv_addr + ':' + str(port)
        else:
            self.serv_addr = serv_addr
            self.service_sock.bind(self.serv_addr)

    def publish(self, topic, message):
        with self.lock:
            self.bus.publish(topic, message)

    def _service_address_subscription_handler(self, topic, message):
        self.service_address_table[topic[len('/service_address'):]] = message

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
            if service in self.service_address_table:
                addr = self.service_address_table[service]
                return self.call_with_address(service, request, addr)
            else:
                raise call.CallFailed('service not known')

    def call_with_address(self, service, request, address):
        with self.lock:
            socket = self.bus.ctx.socket(zmq.REQ)
            socket.connect(address)
            socket.send(call.encode_req(service, request))
            s = socket.recv()
            return call.decode_res(s)

    def register_service(self, service, handler):
        with self.lock:
            self.service_handlers[service] = handler

    def _service_handle(self, buf):
        service, arg = call.decode_req(buf)
        with self.lock:
            if service in self.service_handlers:
                hanlder = self.service_handlers[service]
            else:
                return call.encode_res_error("service doesn't exist")
        try:
            return call.encode_res(hanlder(arg))
        except ServiceFailed as e:
            return call.encode_res_error(str(e))

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

    def _publish_service_address(self):
        for service in self.service_handlers:
            self.bus.publish('/service_address' + service, self.serv_addr)

    def _publish_service_address_loop(self):
        while (1):
            with self.lock:
                self._publish_service_address()
            time.sleep(1)

    def _handle_service_loop(self):
        while (1):
            buf = self.service_sock.recv()
            res = self._service_handle(buf)
            self.service_sock.send(res)
