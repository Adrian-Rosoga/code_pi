#!/usr/bin/env python3

import os
import sys
import time
import logging
from datetime import datetime
from Adafruit_IO import Client, Feed
sys.path.append('/home/pi/code_pi/utilpy')
import HTU21D

# Delay in-between sensor readings, in seconds.
READ_INTERVAL = 60
ADAFRUIT_IO_KEY = os.environ['ADAFRUIT_IO_KEY']
ADAFRUIT_IO_USERNAME = os.environ['ADAFRUIT_IO_USERNAME']

def send_readings(aio, *feeds):

    temperature_feed, humidity_feed, last_updated_feed = feeds

    temperature, humidity = HTU21D.get_temperature_humidity()
    if humidity is not None and temperature is not None:
        logging.info('Temp={0:0.1f}*C Humidity={1:0.1f}%'.format(temperature, humidity))
        # Send humidity and temperature feeds to Adafruit IO
        temperature = '%.2f' % temperature
        humidity = '%.2f' % humidity
        aio.send(temperature_feed.key, str(temperature))
        aio.send(humidity_feed.key, str(humidity))
        aio.send(last_updated_feed.key, str(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    else:
        logging.info('Failed to get readings, trying again in {interval} seconds'.format(interval=READ_INTERVAL))


def main():

    logging.basicConfig(format="%(asctime)-15s %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    # REST client.
    aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

    # Adafruit IO Feeds.
    temperature_feed = aio.feeds('rafi-temperature')
    humidity_feed = aio.feeds('rafi-humidity')
    last_updated_feed = aio.feeds('rafi-last-updated')

    while True:

        try:
            send_readings(aio, temperature_feed, humidity_feed, last_updated_feed)
        # except simplejson.errors.JSONDecodeError as ex:
        #     logging.info('simplejson.errors.JSONDecodeError caught')
        except Exception as ex:
            logging.info('Caught exception: %s', ex.__class__.__name__)
            traceback.print_exc()

        # Avoid flooding Adafruit IO
        time.sleep(READ_INTERVAL)


if __name__ == '__main__':

    main()
