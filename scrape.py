#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from sys import exit, stderr
from kafka import KafkaProducer
import requests
from lxml import etree
from pathlib import Path
from ratelimiter import RateLimiter
from datetime import datetime
from icmplib import ping
from urllib.parse import urlparse

parser = ArgumentParser()

# Global options
parser.add_argument(
    '-b', '--kafka-bootstrap',
    help="specify the kafka server to produce to",
    default="localhost:9092",
)

parser.add_argument(
    '-k', '--kafka-topic',
    help="specify the kafka topic to produce to",
    default="sample",
)

parser.add_argument(
    '-u', '--url',
    help="specify the HTTP URL to scrape",
    required=True,
)

parser.add_argument(
    '-s', '--simulate', 
    help="specify the HTTP URL to scrape",
    action='store_true',
)

parser.add_argument(
    '--wait', 
    help="wait for up to --kafka-timeout seconds to write to kafka",
    action='store_true',
)

parser.add_argument(
    '--icmp', 
    help="wait for ICMP (ping) availability before HTTP request",
    action='store_true',
)

parser.add_argument(
    '--icmp-timeout',
    help="specify the kafka timeout (seconds)",
    type=float,
    default=0.5,
)

parser.add_argument(
    '-t', '--timout',
    help="specify the HTTP timeout (seconds)",
    type=float,
    default=10.0,
)

parser.add_argument(
    '-d', '--delay',
    help="specify the delay in the loop (seconds)",
    type=float,
    default=60.0,
)

parser.add_argument(
    '--kafka-timeout',
    help="specify the kafka timeout (seconds)",
    type=float,
    default=10.0,
)

subparsers = parser.add_subparsers(dest="xml")

parser_xml = subparsers.add_parser(
    'xml',
    help="parse the data as XML",
)

parser_xml.add_argument(
    '-x', '--xpath',
    action='append',
    help="XPath to produce, values emitted in order",
    required=True,
)

args = parser.parse_args()

if not args.xml:
    parser.parse_args(["--help"])
    exit(-1)


def wait(host):
    while True:
        res = ping(host, count=1, timeout=args.icmp_timeout)
        if res.is_alive:
            break

producer = KafkaProducer(bootstrap_servers=[ args.kafka_bootstrap ])
netloc = urlparse(args.url).netloc
rate_limiter = RateLimiter(max_calls=1, period=args.delay)
print(f'Scraping from url:"{args.url}"" on host:"{netloc}"')
while True:
    try:
        with rate_limiter:
            #TODO: support file path
            #txt = Path('test.xml').read_bytes()

            if args.icmp:
                wait(netloc)

            response = requests.request("GET", args.url, timeout=args.timout)
            now =  datetime.utcnow().isoformat(sep=' ', timespec='milliseconds')
            txt = response.content
            values = [ ]

            root = etree.fromstring(txt)

            for path in args.xpath:
                try:
                    l = root.xpath(path, now=now)
                    
                    v = None
                    if isinstance(l, list):
                        if len(l) > 0:
                            v = l[0]
                    else:
                        v = l

                    values.append(v)
                except etree.XPathEvalError as e:
                    print(f"Error evaluting XPath:{path}", file=stderr)
                    raise e
            row = ",".join(values)

            if args.simulate:
                print(row)
            else:
                future = producer.send(args.kafka_topic, value=row.encode())
                if args.wait:
                    result = future.get(timeout=args.kafka_timeout)
                    print(f"kafka-written: timestamp={result.timestamp}, partition={result.partition}, offset={result.offset}")

    except KeyboardInterrupt as e:
        exit(0)
        pass
    except requests.exceptions.ReadTimeout as e:
        print("read-timeout", file=stderr)
        continue        
    except requests.exceptions.ConnectTimeout as e:
        print("connect-timeout", file=stderr)
        continue
