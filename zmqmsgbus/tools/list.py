import time
import zmqmsgbus


if __name__ == '__main__':
    CLEAR_CONSOLE = '\x1b[2J\x1b[H'

    bus = zmqmsgbus.Bus(sub_addr='ipc://ipc/source')
    node = zmqmsgbus.Node(bus)

    messages = {}

    def handler(topic, content):
        if topic in messages:
            messages[topic] += 1
        else:
            messages[topic] = 1

    node.register_message_handler('/', handler)
    while 1:
        time.sleep(1)
        print(CLEAR_CONSOLE)
        print('topics:')
        for topic, count in sorted(messages.items()):
            print('{}: {}Hz'.format(topic, count))
        messages = {}
