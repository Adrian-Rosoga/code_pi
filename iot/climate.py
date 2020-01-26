#!/usr/bin/env python3

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from Adafruit_IO import Client, Feed, errors
sys.path.append('/home/pi/code_pi/utilpy')
import HTU21D  # noqa


REPORTING_INTERVAL_SECS_DEFAULT = 60
ADAFRUIT_IO_KEY = os.environ['ADAFRUIT_IO_KEY']
ADAFRUIT_IO_USERNAME = os.environ['ADAFRUIT_IO_USERNAME']


class Registry():
    reporting_interval = REPORTING_INTERVAL_SECS_DEFAULT


def send_readings(aio, temperature, humidity, *feeds):

    temperature_feed, humidity_feed, last_updated_feed = feeds

    if humidity is not None and temperature is not None:
        temperature = f'temperature:.2f'
        humidity = f'humidity:.2f'
        aio.send(temperature_feed.key, temperature)
        aio.send(humidity_feed.key, humidity)
        aio.send(last_updated_feed.key, str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))


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
    temperature_feed = aio.feeds('rafi-temperature')
    humidity_feed = aio.feeds('rafi-humidity')
    last_updated_feed = aio.feeds('rafi-last-updated')

    while True:

        try:
            temperature, humidity = HTU21D.get_temperature_humidity()

            if humidity is not None and temperature is not None:
                logging.info(f'Temp={temperature:0.1f}*C Humidity={humidity:0.1f}% Send={not display_only}')
            else:
                logging.info(f'Failed to get readings, trying again in {Registry.reporting_interval} seconds')

            if not display_only:
                send_readings(aio, temperature, humidity, temperature_feed, humidity_feed, last_updated_feed)

        except Exception as ex:
            logging.exception('Cannot send report')

        # Avoid flooding Adafruit IO
        time.sleep(Registry.reporting_interval)


if __name__ == '__main__':

    main()
