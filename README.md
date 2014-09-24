crawler
=======

Demo of a crawler service implemented in python. This service is made up the following components:
- rest.py : Rest server, in charge of receiving petitions to crawl and returning responses
- tasks.py : Taks server, in charge of performing the crawling and data analysis, designed to scale horizontally


## Instructions:

The following instructions assume the user is running in OSX, and it has boot2docker configured

- Start a rabbitmq container: 
```
> docker run -d -p 5672:5672 -p 15672:15672 -v /tmp/log:/data/log -v /tmp/data/mnesia:/data/mnesia dockerfile/rabbitmq
```
- Start a mongodb container: 
```
> docker run -d -p 27017:27017 -v /tmp/data/db:/data/db --name mongodb dockerfile/mongodb
```
- Get the IP of the docker vm: 
```
> boot2docker ip (assuming is 192.168.59.103 for the examples)
```
- Create a mongo user for the app to use: 
```
mongo 192.168.59.103:27017 --eval 'db.getSiblingDB("tasks").addUser({user:"tasks", pwd:"tasks", roles:["readWrite"]})'
```
- Start a rest container: 
```
> docker run -d -p 5000:5000 -e ROLE=rest -e MESSAGING="amqp://guest:guest@192.168.59.103:5672" -e DB="mongodb://tasks:tasks@192.168.59.103:27017/tasks" ramiro/crawler
```
- Start a task container: 
```
> docker run -d  -e ROLE=task -e MESSAGING="amqp://guest:guest@192.168.59.103:5672" -e DB="mongodb://tasks:tasks@192.168.59.103:27017/tasks" ramiro/crawler
```

## Usage:

- Create a new job: 
```
> curl http://192.168.59.103:5000 -X POST -d '{"urls":["http://www.mongodb.org"]}' -H Content-Type:application/json
{
  "id": "97a2ad0b-0bd6-412f-a5f3-cef49fc12aa9"
}
```
- Check the status of the job: 
```
curl http://192.168.59.103:5000/status/97a2ad0b-0bd6-412f-a5f3-cef49fc12aa9
{
  "completed": 0, 
  "files": [], 
  "id": "97a2ad0b-0bd6-412f-a5f3-cef49fc12aa9", 
  "total": 1, 
  "updated": "Wed, 24 Sep 2014 08:18:25 GMT"
}
```