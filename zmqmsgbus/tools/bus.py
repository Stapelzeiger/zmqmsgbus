import argparse
import zmqmsgbus


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run ZeroMQ message Bus')
    parser.add_argument('--in', dest='in_addr', nargs='*',
                        default=['ipc://ipc/sink'])
    parser.add_argument('--out', dest='out_addr', nargs='*',
                        default=['ipc://ipc/source'])
    args = parser.parse_args()

    print('runnning ZeroMQ Message Bus')
    print('input  {}'.format(', '.join(args.in_addr)))
    print('output {}'.format(', '.join(args.out_addr)))
    zmqmsgbus.forward(args.in_addr, args.out_addr, bind=True)
