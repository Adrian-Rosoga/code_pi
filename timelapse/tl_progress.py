#!/usr/bin/env python3

"""
tlp - Timelapse Progress
Adrian Rosoga, 13 Jan 2014, refactored 29 Sep 2018
"""

import os
import sys
import subprocess as sp
from time import sleep
sys.path.append('/home/pi/code_pi/utilpy')
from getch import getch_non_blocking  # noqa


TIMELAPSE_CODE_PATH = '/home/pi/code_pi/timelapse'


def output_cmd(cmd):
    """Return the output of a command"""
    return sp.check_output(cmd, shell=True).rstrip().decode()


def check():
    """Check timelapse progress"""

    os.chdir(TIMELAPSE_CODE_PATH)

    timelapse_dir = output_cmd('readlink timelapse_dir')

    old_count_photos = -1

    print('\nPhotos dir: ' + timelapse_dir)

    while True:
        print('\n---------------------------------')

        if timelapse_dir != '/tmp/timelapse':
            last_dir = output_cmd(f'ls -1rt {timelapse_dir} | tail -1')
        else:
            last_dir = ""

        photos_dir = os.path.join(timelapse_dir, last_dir)

        count_photos = output_cmd(f'ls {photos_dir} | wc -l')

        print(f'{count_photos} photos in photos directory {photos_dir}')
        os.system('date')
        os.system('ps -eaf | grep raspistill | grep -v grep | grep -v sudo')

        if count_photos == old_count_photos and timelapse_dir != '/tmp/timelapse':
            print('!!!!!!! ALERT !!!!!!!')
        old_count_photos = count_photos

        os.system(f'df -h {photos_dir}')

        #sleep(30)
        ch = getch_non_blocking(30)

        if ch == 'x':
            return


if __name__ == "__main__":
    check()
