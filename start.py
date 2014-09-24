"""
Crawler: 
The crawler takes a list of URLs, and starts a job to gather all the links contained in the page and the potential subpages
"""

import argparse
import rest
import task

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Webserver to crawl some urls.')
    parser.add_argument('--role', dest='role', default="rest")
    parser.add_argument('--messaging', dest='messaging', default="amqp://guest:guest@localhost:5672/%2F")
    parser.add_argument('--db', dest='db', default="mongodb://guest:guest@127.0.0.1:27017/tasks")
    args = parser.parse_args()

    mod = __import__(args.role)
    mod.start(args.db, args.messaging)