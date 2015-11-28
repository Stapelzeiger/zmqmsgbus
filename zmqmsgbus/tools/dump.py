#!/usr/bin/env python

import sys
import zmq
import zmqmsgbus

context = zmq.Context()
socket = context.socket(zmq.SUB)

# socket.connect("tcp://localhost:13371")
socket.connect("ipc://ipc/source")

for topic in sys.argv[1:]:
    socket.setsockopt(zmq.SUBSCRIBE, zmqmsgbus.createZmqFilter(topic))
if len(sys.argv) == 1:
    socket.setsockopt(zmq.SUBSCRIBE, b'')

while True:
    print(zmqmsgbus.decode(socket.recv()))
