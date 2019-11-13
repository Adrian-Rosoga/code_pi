#!/usr/bin/env python3

import os
import time
import logging
import traceback
import argparse
import platform
from Adafruit_IO import RequestError, Client, Feed


ADAFRUIT_IO_KEY = os.environ['ADAFRUIT_IO_KEY']
ADAFRUIT_IO_USERNAME = os.environ['ADAFRUIT_IO_USERNAME']

REPORTING_INTERVAL_DEFAULT_SECS = 10

""" Hack alert - bad idea to use these globals! """
last_idle = last_total = 0.0
idle_delta = total_delta = 0.0


def cpu_utilisation():
    """ Get CPU utilisation """
    global last_idle, last_total, idle_delta, total_delta

    with open('/proc/stat') as f:
        fields = [float(column) for column in f.readline().strip().split()[1:]]
    idle, total = fields[3], sum(fields)
    idle_delta, total_delta = idle - last_idle, total - last_total
    last_idle, last_total = idle, total
    utilisation = 100.0 * (1.0 - idle_delta / total_delta)
    return utilisation


def report_cpu(aio, feed_name, reporting_interval):
    """ Report CPU on feed """

    feed = aio.feeds(feed_name)  # Feed should exist

    while True:
        try:
            utilisation = cpu_utilisation()
            logging.info('Feed=' + feed_name + ' CPU={utilisation:.1f}%'.format(utilisation=utilisation))
            aio.send(feed.key, utilisation)

        except Exception as e:
            logging.info('Caught exception: %s', e.__class__.__name__)
            traceback.print_exc()

        time.sleep(reporting_interval)


def main():

    logging.basicConfig(format="%(asctime)-15s %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='CPU Utilisation')
    parser.add_argument('--interval', help='reporting interval in seconds')
    args = parser.parse_args()

    reporting_interval = int(args.interval) if args.interval else REPORTING_INTERVAL_DEFAULT_SECS

    aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

    hostname = platform.node().lower()
    feed_name = "cpu-" + hostname
    
    report_cpu(aio, feed_name, reporting_interval)


if __name__ == "__main__":

    main()