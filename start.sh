#! /bin/bash

service mongod start
service rabbitmq-server start
python crawler/rest.py