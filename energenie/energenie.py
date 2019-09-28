#!/usr/bin/env python3

#
# Utility to turn on/off Enerhenies
#
# Adrian Rosoga
# Version 1.0 - 4 Sep 2019
#
# Use

import sys
from gpiozero import Energenie


def usage():

    print("Usage:", sys.argv[0], "on|off <device_number>")
    print("Example:", sys.argv[0], "on 1")


def main():

    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    command = sys.argv[1]

    if command not in ("on", "off"):
        usage()
        sys.exit(1)

    device_number = sys.argv[2]

    if device_number not in ("1", "2", "3", "4"):
        usage()
        sys.exit(1)

    device_number = int(device_number)

    if command == "on":
        device = Energenie(device_number, True)
        # lamp.on() # Above just does the job
    else:
        device = Energenie(device_number, False)
        # lamp.on() # Above just does the job


if __name__ == "__main__":

    main()
