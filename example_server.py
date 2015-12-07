import time
import zmqmsgbus

bus = zmqmsgbus.Bus(sub_addr='ipc://ipc/source',
                    pub_addr='ipc://ipc/sink')

node = zmqmsgbus.Node(bus)
node.register_service('/example/square', lambda x: x*x)

while 1:
    time.sleep(1)
