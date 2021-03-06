#!/usr/bin/env python

from setuptools import setup

args = dict(
    name='zmqmsgbus',
    version='0.1',
    description='Very simple message bus based on zeromq and messagepack.',
    packages=['zmqmsgbus', 'zmqmsgbus.tools'],
    install_requires=['msgpack-python', 'zmq'],
    author='Patrick Spieler',
    author_email='stapelzeiger@gmail.com',
    url='https://github.com/stapelzeiger/zmqmsgbus',
    license='BSD',
    test_suite='nose.collector',
    tests_require=['nose']
)

setup(**args)
