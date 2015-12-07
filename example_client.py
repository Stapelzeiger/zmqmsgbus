import time
import zmqmsgbus

bus = zmqmsgbus.Bus(sub_addr='ipc://ipc/source',
                    pub_addr='ipc://ipc/sink')

node = zmqmsgbus.Node(bus)

i = 0
while 1:
    try:
        print(i, node.call('/example/square', i))
        i += 1
    except zmqmsgbus.call.ServiceFailed as e:
        print(e)
    time.sleep(0.1)
