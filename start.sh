#! /bin/bash

service mongod start
service rabbitmq-server start
echo Running with the following credentials: $ROLE $MESSAGING $DB
python crawler/$ROLE.py --messaging $MESSAGING --db $DB