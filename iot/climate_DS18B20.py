#!/usr/bin/env python3

import os
import sys
import re
import time
import logging
import traceback
import argparse
from datetime import datetime
from Adafruit_IO import Client, Feed, errors
sys.path.append('/home/pi/code_pi/utilpy')
import DS18B20  # noqa


REPORTING_INTERVAL_SECS_DEFAULT = 60  # In-between sensor readings, in seconds.
ADAFRUIT_IO_KEY = os.environ['ADAFRUIT_IO_KEY']
ADAFRUIT_IO_USERNAME = os.environ['ADAFRUIT_IO_USERNAME']


class Registry():
    reporting_interval = REPORTING_INTERVAL_SECS_DEFAULT


def send_readings(aio, temperature, *feeds):

    temperature_feed, = feeds

    if temperature is not None:
        temperature = '%.2f' % temperature
        aio.send(temperature_feed.key, temperature)
    else:
        logging.info('Failed to get readings, trying again in {} seconds'.format(Registry.reporting_interval))


def main():

    logging.basicConfig(format="%(asctime)-15s %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Climate')
    parser.add_argument('-i', '--interval', help='reporting interval in seconds')
    parser.add_argument('-d', '--display_only', help='only display, no reporting', action="store_true")
    args = parser.parse_args()

    if args.interval:
        Registry.reporting_interval = int(args.interval)
    display_only = args.display_only

    # REST client.
    aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

    # Adafruit IO Feeds.
    temperature_feed = aio.feeds('room-temperature')

    while True:

        try:
            temperature = DS18B20.get_temperature()

            if temperature is not None:
                logging.info('Temp={0:0.1f}*C Send readings={1}'.format(temperature, not display_only))
            else:
                logging.info('Failed to get readings, trying again in {} seconds'.format(Registry.reporting_interval))

            if not display_only:
                send_readings(aio, temperature, temperature_feed)

        #except Adafruit_IO.errors.ThrottlingError as ex:
        #    logging.info('Throttling occured - Caught exception: %s', ex.__class__.__name__)
        except Exception as ex:
            logging.info('Caught exception: %s', ex.__class__.__name__)
            traceback.print_exc()

        # Avoid flooding Adafruit IO
        time.sleep(Registry.reporting_interval)


if __name__ == '__main__':

    main()
