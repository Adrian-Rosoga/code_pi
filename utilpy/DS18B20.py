"""
Returns temperature from a DS18B20 sensor or None if no sensors attached or more than one sensors found

Sample file path: /sys/bus/w1/devices/28-0000045bf342/w1_slave

Sample file (includes empty line at the end):
60 01 4b 46 7f ff 10 10 b5 : crc=b5 YES
60 01 4b 46 7f ff 10 10 b5 t=22000

"""

import time
import re
import glob
import os

_DS18B20_OUTPUT_PATHNAME = '/sys/bus/w1/devices/28-*'
_regex = re.compile(r't=(\d+)')
_RETRY_COUNT = 4


def get_temperature():

    DS18B20_files = glob.glob(_DS18B20_OUTPUT_PATHNAME)
    number_sensors = len(DS18B20_files)

    if number_sensors != 1:
        print(f'Only one sensor supported, found {number_sensors} instead')
        return None  # Either no sensor or more than one sensors

    DS18B20_file = os.path.join(DS18B20_files[0], "w1_slave")
    retry_count = _RETRY_COUNT

    while (retry_count > 0):
        with open(DS18B20_file, 'r') as f:
            lines = f.read().split('\n')
            if len(lines) != 3 or ( len(lines) == 3 and 'YES' not in lines[0]):
                time.sleep(0.2)
                retry_count = retry_count - 1
                continue
            data = _regex.search(lines[1])
            temperature = float(data.group(1)[0:4]) / 100.0
            return temperature

    print(f'Couldn\'t read the temperature after {_RETRY_COUNT} attempts')
    return None


if __name__ == "__main__":

    temperature = get_temperature()
    if temperature is not None:
        print(get_temperature())
