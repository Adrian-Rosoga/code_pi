#!/usr/bin/env python3


import sys
import time
import Adafruit_DHT

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
SLEEP_TIME_SECS = 10


def get():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    return temperature, humidity


def main():
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

        if humidity is not None and temperature is not None:
            print("Temperature={0:0.1f}*C Humidity={1:0.1f}%".format(temperature, humidity))
        else:
            print(f"Error: Failed to retrieve data from the {DHT_SENSOR} sensor")
            sys.exit(1)

        print(f'Sleeping for {SLEEP_TIME_SECS} seconds...')
        time.sleep(10)


if __name__ == '__main__':
    main()