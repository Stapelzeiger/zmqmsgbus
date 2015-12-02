import zmq
import zmqmsgbus.msg as msg


def map_string_or_list_of_strings(fn, s):
    if isinstance(s, str):
        fn(s)
    else:
        for s in s:
            fn(s)


def rename_message(msg_buf, topic, new_topic):
    msg_topic, msg_body = msg.decode(msg_buf)
    renamed_buf = msg.encode(msg_topic.replace(topic, new_topic, 1), msg_body)
    return renamed_buf


def forward(sub_addr, pub_addr, topic='', rename_topic=None, bind=False):
    context = zmq.Context()

    in_sock = context.socket(zmq.SUB)
    out_sock = context.socket(zmq.PUB)

    if bind is True:
        map_string_or_list_of_strings(in_sock.bind, sub_addr)
        map_string_or_list_of_strings(out_sock.bind, pub_addr)
    else:
        map_string_or_list_of_strings(in_sock.connect, sub_addr)
        map_string_or_list_of_strings(out_sock.connect, pub_addr)

    in_sock.setsockopt(zmq.SUBSCRIBE, msg.createZmqFilter(topic))
    if rename_topic is None:
        zmq.device(zmq.FORWARDER, in_sock, out_sock)
    else:
        while (1):
            out_sock.send(rename_message(in_sock.recv(), topic, rename_topic))
