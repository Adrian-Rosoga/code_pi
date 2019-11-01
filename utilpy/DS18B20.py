#!/usr/bin/env python3

DS18B20_OUTPUT_FILE = '/sys/bus/w1/devices/28-0000045bf342/w1_slave'

regex = re.compile(r't=(\d+)')


def get_temperature():

    with open(DS18B20_OUTPUT_FILE, 'r') as f:
        f.readline()
        line = f.readline()
        data = regex.search(line)
        temperature = float(data.group(1)[0:4]) / 100.0
        return temperature


if __name__ == "__main_":
    print(get_temperature())