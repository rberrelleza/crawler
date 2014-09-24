#!/bin/python

"""
Task executer: 
The task executer takes a url, and crawls it for more urls that match a certain pattern
"""

import argparse
import BeautifulSoup
import constants
import datetime
import json
import pika
import random
import re
import requests
import os
import utils

from pika import BasicProperties
from pika.adapters import BlockingConnection
from pymongo import MongoClient

LINK_REGEX = re.compile(r'[http|https]+?://[^\s<>"]+|www\.[^\s<>"]+', re.IGNORECASE)
FILE_EXTENSIONS = [".png", ".jpg", ".gif"]
MAX_CRAWL = 1
EXCHANGE = "tasks"

def crawl(url):
    files = set()
    urls = set()
    try:
        response = requests.get(url)
        soup = BeautifulSoup.BeautifulSoup(response.text)
        found = soup.body.findAll("a") + soup.body.findAll("img") 
        for link in found:
            url = link.get("href")
            if url is None:
                url = link.get("src")
            
            extension = os.path.splitext(url.lower())[1]
            if extension in FILE_EXTENSIONS:
                files.add(url)
            elif re.match(LINK_REGEX, url):
                urls.add(url)
    except Exception as e:
        # for this example we just ignore bad urls to keep it simple
        pass
    finally:
        return list(files), list(urls)
    
def update_job(database, job_id, found_files, urls_count):
    database.tasks.update({"id":job_id}, {"$inc": { "completed": 1, "total": urls_count}})

    if len(found_files) > 0:
        database.tasks.update({"id":job_id}, {"$addToSet": { "files": { "$each": found_files}}})

def on_message(channel, method_frame, header_frame, body):
    message_dict = json.loads(body)

    url = message_dict["url"]
    job_id = message_dict["id"]
    level = message_dict["level"] if "level" in message_dict else 0

    found_files, found_urls = crawl(url)

    if level < MAX_CRAWL:
        level = level + 1
        update_job(database, job_id, found_files, len(found_urls))
        for found_url in found_urls:
            messagedata = json.dumps({"id": job_id, "level":level,  "url": found_url})
            pub_channel.basic_publish(exchange=EXCHANGE,
                routing_key=EXCHANGE,
                body=messagedata,
                properties=BasicProperties(content_type="application/json", delivery_mode=2))
    else:
        update_job(database, job_id, found_files, 0)

    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    print str(datetime.datetime.utcnow()) + "Done with message " + str(method_frame.delivery_tag)

def start(db, messaging):
    connection = BlockingConnection(pika.URLParameters(messaging))
    publish_connection = BlockingConnection(pika.URLParameters(messaging))
    client = MongoClient(db)
    
    global database
    database = client.get_default_database()

    channel = connection.channel()

    global pub_channel
    pub_channel = publish_connection.channel()

    channel = connection.channel()
    channel.queue_declare(queue=EXCHANGE, durable=True, exclusive=False, auto_delete=False)
    channel.exchange_declare(exchange=EXCHANGE)
    channel.queue_bind(exchange=EXCHANGE, queue=EXCHANGE)
    channel.basic_consume(on_message, EXCHANGE)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()
    publish_connection.close()

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Task server to crawl some urls.')
    parser.add_argument('--messaging', dest='messaging', default="amqp://guest:guest@localhost:5672/%2F")
    parser.add_argument('--db', dest='db', default="mongodb://tasks:tasks@127.0.0.1:27017/tasks")
    args = parser.parse_args()
    start(args.db, args.messaging)
    