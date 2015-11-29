import zmq
import argparse


def forward(from_list, to_list):
    context = zmq.Context()

    in_sock = context.socket(zmq.SUB)
    in_sock.bind("tcp://*:13370")
    in_sock.bind("ipc://ipc/sink")
    in_sock.setsockopt(zmq.SUBSCRIBE, b'')

    out_sock = context.socket(zmq.PUB)
    out_sock.bind("tcp://*:13371")
    out_sock.bind("ipc://ipc/source")

    zmq.device(zmq.FORWARDER, in_sock, out_sock)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Forward ZeroMQ messages')
    parser.add_argument('--from', dest='from_addr', nargs='*',
                        default=['ipc://ipc/sink'])
    parser.add_argument('--to', dest='to_addr', nargs='*',
                        default=['ipc://ipc/source'])
    args = parser.parse_args()

    print('forwarding from {}'.format(args.from_addr))
    print('to {}'.format(args.to_addr))
    forward(args.from_addr, args.to_addr)
