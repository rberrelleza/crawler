#!/bin/python

"""
Web crawler: 
The crawler takes a list of URLs, and starts a job to gather all the links contained in the page and the potential sublevels

"""

import argparse
import datetime
import pika
import uuid
import json

from functools import wraps
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pika.adapters import BlockingConnection
from pika import BasicProperties

app = Flask(__name__)
EXCHANGE = "tasks"

def start(db, messaging):
    global connection
    connection = BlockingConnection(pika.URLParameters(messaging))
    
    global channel
    channel = connection.channel()
    channel.queue_declare(queue=EXCHANGE, durable=True, exclusive=False, auto_delete=False)
    channel.exchange_declare(exchange=EXCHANGE)
    channel.queue_bind(exchange=EXCHANGE, queue=EXCHANGE)

    global database
    client = MongoClient(db)
    database = client.get_default_database()

    app.run()


def validate_json(f):
    @wraps(f)
    def wrapper(*args, **kw):
        try:
            request.json
        except BadRequest, e:
            return jsonify({"error": "Payload doesn't include valid json"}), 400
        return f(*args, **kw)
    return wrapper


@validate_json
@app.route("/", methods=["POST"])
def post():
    data = request.get_json()
    if 'urls' not in data or len(data['urls']) < 1:
        return jsonify({"error": "Payload doesn't include valid data"}), 400
    
    job =  {
        "id": str(uuid.uuid4()), 
        "files": [], 
        "total": len(data['urls']), 
        "completed": 0,
        "updated": datetime.datetime.utcnow() }
    database.tasks.insert(job)

    for url in data['urls']:
        print url
        messagedata = json.dumps({"id": job["id"], "level":0,  "url": url})
        channel.basic_publish(exchange=EXCHANGE,
                      routing_key=EXCHANGE,
                      body=messagedata,
                      properties=BasicProperties(content_type="application/json", delivery_mode=2))
        print "Published message for url " + url

    return jsonify({"id": job["id"]})


@app.route("/status/<job_id>", methods=["GET"])
def get(job_id):
    job = database.tasks.find_one({"id":job_id})
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    else:
        del job["_id"]
        return jsonify(job)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Webserver to crawl some urls.')
    parser.add_argument('--messaging', dest='messaging', default="amqp://guest:guest@localhost:5672/%2F")
    parser.add_argument('--db', dest='db', default="mongodb://server:tasks@127.0.0.1:27017/tasks")
    args = parser.parse_args()
    start(args.db, args.messaging)
    