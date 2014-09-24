#! /bin/bash

service mongod start
service rabbitmq-server start
python crawler/$ROLE.py --messaging $MESSAGING --db $DB