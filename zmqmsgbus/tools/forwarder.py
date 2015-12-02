import argparse
import zmqmsgbus


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Forward ZeroMQ messages')
    parser.add_argument('--from', dest='from_addr', nargs='*',
                        default=['ipc://ipc/sink'])
    parser.add_argument('--to', dest='to_addr', nargs='*',
                        default=['ipc://ipc/source'])
    args = parser.parse_args()

    print('forwarding from {}'.format(args.from_addr))
    print('to {}'.format(args.to_addr))
    zmqmsgbus.forward(args.from_addr, args.to_addr)
