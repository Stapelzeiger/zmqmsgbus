import argparse
import zmqmsgbus


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Forward ZeroMQ messages')
    parser.add_argument('--from', dest='from_addr', nargs='*',
                        default=['ipc://ipc/source'])
    parser.add_argument('--to', dest='to_addr', nargs='*',
                        default=['ipc://ipc/sink'])
    parser.add_argument('--topic', default='')
    parser.add_argument('--rename', default=None)
    args = parser.parse_args()

    if args.rename is None:
        print('forwarding ' + args.topic)
    else:
        print('forwarding {} ==> {}'.format(args.topic, args.rename))
    print('from {}'.format(', '.join(args.from_addr)))
    print('to   {}'.format(', '.join(args.to_addr)))
    zmqmsgbus.forward(args.from_addr, args.to_addr, args.topic, args.rename)
