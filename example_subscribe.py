import zmqmsgbus

bus = zmqmsgbus.Bus(sub_addr='ipc://ipc/source',
                    pub_addr='ipc://ipc/sink')

node = zmqmsgbus.Node(bus)

print('receiving')
while 1:
    print(node.recv('/example/counter'))
