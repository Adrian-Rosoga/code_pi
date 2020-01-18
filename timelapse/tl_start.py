#!/usr/bin/env python3

"""
Timelapse Starter - meant to be invoked from cron
Adrian Rosoga, 6 Feb 2014
Refactored 29 Sep 2018
Refactored Dec 2019
"""


import sys
import os
import time
import logging
import traceback
import argparse
from datetime import datetime
import subprocess as sp
import RPi.GPIO as GPIO

TIMELAPSE_RUN_HOURS = 24
TIMELAPSE_SECS_BETWEEN_PICTURES = 10
FILES_TO_KEEP = 10
CAMLED = 5  # GPIO for camera LED

"""
Aspect is 4:3       - 1.333
Now: 1440x1080      - 1.333
Max: 2592x1944      - 1.333

YouTube:
To fit the player perfectly, encode at these resolutions:
    2160p: 3840x2160.
    1440p: 2560x1440.
    1080p: 1920x1080.
    720p: 1280x720.
"""

#CONFIG_DIMENSIONS = '-w 1440 -h 1080'
#CONFIG_DIMENSIONS = ''                  # Max size
CONFIG_DIMENSIONS = '-w 2560 -h 1440'    # YouTube 16:9

#CONFIG_TIME_LIMIT = '-t 86400000'  # 24 hours
#CONFIG_TIME_LIMIT = '-t 0'         # No limit
CONFIG_TIME_LIMIT = '-t 100000'  # 10 photos at one photo every 10 secs

#CONFIG_DATE_IN_NAME = ''           # No
CONFIG_DATE_IN_NAME = '-dt'         # Yes

TIMELAPSE_CODE_PATH = '/home/pi/code_pi/timelapse'


def get_capture_dir():
    """Return (create if not exists) the directory where pictures go"""

    timelapse_dir = sp.check_output(['readlink', 'timelapse_dir']).rstrip().decode('utf-8')
    logging.info(f'timelapse_dir = {timelapse_dir}')

    if timelapse_dir != '/tmp/timelapse':
        # Use a different directory every time
        #capture_dir = os.path.join(timelapse_dir, datetime.now().strftime("%Y%m%d-%H%M%S"))
        # Use the same directory
        capture_dir = os.path.join(timelapse_dir, datetime.now().strftime("%Y%m%d"))
    else:
        capture_dir = os.path.join(timelapse_dir, "")

    # If already there just return it
    if os.path.isdir(capture_dir):
        return capture_dir

    return_code = sp.call(['mkdir', capture_dir])
    if return_code:
        logging.error(f'Cannot create the capture directory "{capture_dir}"')
        sys.exit(1)

    return_code = sp.call(['chmod', 'ago+rw', capture_dir])
    if return_code:
        logging.error(f'Cannot chmod for directory "{capture_dir}"')
        sys.exit(1)

    return capture_dir


def start_capture(capture_dir, run_in_background=True):

    logging.info(f'Capture directory: "{capture_dir}"')

    ampersand = '&' if run_in_background else ''

    # E.g.: raspistill -n -q 100 -o /mnt/timelapse/20160113-093350/z%05d.jpg
    # -t 86400000 -w 1440 -h 1080  -tl 10000 &
    #
    # TODO: ' -t ' + str(TIMELAPSE_RUN_HOURS * 3600 * 1000) + \
    #
    cmd = 'raspistill -n -q 100 -o ' + capture_dir + '/tl_%05d.jpg'\
          + ' ' + CONFIG_TIME_LIMIT\
          + ' ' + CONFIG_DIMENSIONS\
          + ' ' + CONFIG_DATE_IN_NAME\
          + ' ' + '-tl ' + str(TIMELAPSE_SECS_BETWEEN_PICTURES * 1000)\
          + ' ' + ampersand

    # Stop LED
    GPIO.output(CAMLED, False)

    logging.info(cmd)
    ret_code = os.system(cmd)
    if ret_code:
        #logging.info('Error starting capture! Exiting.')
        #sys.exit(1)
        pass
    else:
        logging.info('Capture started!')
        #time.sleep(2)
        #GPIO.output(CAMLED, False)


def stop_capture():

    sp.call(['pkill', 'raspistill'])
    logging.info('Capture stopped!')


def safe_remove(filepath):

    try:
        os.remove(filepath)
    except FileNotFoundError:
        logging.warn(f'File to remove not found: "{filepath}"')
    except Exception as ex:
        logging.error('Caught exception: %s', ex.__class__.__name__)
        traceback.print_exc()


def cleanup_dir(timelapse_dir):
    ''' Keep only FILES_TO_KEEP files '''

    while True:
        files = sorted(os.listdir(timelapse_dir))
        number_files = len(files)

        count = 0
        while number_files > FILES_TO_KEEP:
            #logging.info('Delete', timelapse_dir + '/' + files[count])
            safe_remove(timelapse_dir + '/' + files[count])
            count += 1
            number_files -= 1

        time.sleep(30)


def watchdog():

    while True:

        time.sleep(30)


def run_default():

    global CONFIG_TIME_LIMIT

    # Stop capture if already started
    stop_capture()

    # Create capture directory and start timelapse
    capture_dir = get_capture_dir()
    CONFIG_TIME_LIMIT = '-t 86400000'  # 24 hours
    start_capture(capture_dir)

    # If entered with an argument only keep the last files
    if len(sys.argv) > 1:
        logging.info("Running cleanup...")
        cleanup_dir(capture_dir)


def run_loop():

    global CONFIG_TIME_LIMIT

    # Stop capture if already started
    stop_capture()

    # Create capture directory
    capture_dir = get_capture_dir()

    CONFIG_TIME_LIMIT = '-t 100000'  # 10 photos at one photo every 10 secs

    while True:

        #start_capture(capture_dir, False)
        #time.sleep(TIMELAPSE_SECS_BETWEEN_PICTURES - 2)

        start_capture(capture_dir, True)
        logging.info("Sleeping...")
        time.sleep(100 + 10)
        logging.info("Killing...")
        stop_capture()


def main():

    logging.basicConfig(format="%(asctime)-15s %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Timelapse Start')
    parser.add_argument('tmp', help='Capture in /tmp/timelapse')
    args = parser.parse_args()

    os.chdir(TIMELAPSE_CODE_PATH)

    # For "RuntimeWarning: This channel is already in use, continuing anyway."
    # use GPIO.setwarnings(False) to disable warning.
    GPIO.setwarnings(False)

    # Use GPIO numbering
    GPIO.setmode(GPIO.BCM)

    # Set GPIO to output
    GPIO.setup(CAMLED, GPIO.OUT, initial=False)

    run_default()
    #run_loop()


if __name__ == "__main__":
    main()
