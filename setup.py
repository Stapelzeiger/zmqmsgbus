#!/usr/bin/env python

from setuptools import setup

args = dict(
    name='zmqmsgbus',
    version='0.1',
    description='Very simple message bus based on zeromq and messagepack.',
    packages=['zmqmsgbus'],
    install_requires=['msgpack-python'],
    author='Patrick Spieler',
    author_email='stapelzeiger@gmail.com',
    url='https://github.com/stapelzeiger/zmqmsgbus',
    license='BSD'
)

setup(**args)
