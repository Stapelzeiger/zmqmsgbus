import time
import zmqmsgbus

bus = zmqmsgbus.Bus(sub_addr='ipc://ipc/source',
                    pub_addr='ipc://ipc/sink')

node = zmqmsgbus.Node(bus)

i = 0
while 1:
    print('publishing', i)
    node.publish('/example/counter', i)
    i += 1
    time.sleep(0.1)
