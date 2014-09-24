crawler
=======

Demo of a crawler service implemented in python

Steps on OSX (assumes boot2docker is used):
1. Start a rabbitmq container: > docker run -d -p 5672:5672 -p 15672:15672 -v /tmp/log:/data/log -v /tmp/data/mnesia:/data/mnesia dockerfile/rabbitmq
2. Start a mongodb container: > docker run -d -p 27017:27017 -v /tmp/data/db:/data/db --name mongodb dockerfile/mongodb
3. Get the IP of the docker vm: > boot2docker ip (assuming is 192.168.59.103 for the examples)
4. Create a mongo user for the app to use: mongo 192.168.59.103:27017 --eval 'db.getSiblingDB("tasks").addUser({user:"tasks", pwd:"tasks", roles:["readWrite"]})'
5. Start a rest container: > docker run -d -p 5000:5000 -e ROLE:rest -e MESSAGING:"amqp://guest:guest@192.168.59.103:5672" -DB:"mongodb://tasks:tasks@192.168.59.103:24107/tasks"