#!/usr/bin/env python3

"""
Timelapse Destination
Adrian Rosoga, 19 May 2014, refactored 29 Sep 2018
"""

import subprocess as sp
import sys
import os

TIMELAPSE_CODE_PATH = '/home/pi/code_pi/timelapse'


MENU = ((1, '/mnt/timelapse/tl',       '/mnt/timelapse/tl'),
        (2, '/mnt/timelapse/other',    '/mnt/timelapse/other'),
        (3, '/mnt/timelapse/rafi',     '/mnt/timelapse/rafi'),
        (4, '/mnt/timelapse/zero',     '/mnt/timelapse/zero'),
        (5, '/tmp/timelapse',          '/tmp/timelapse'),
        (6, '/media/usb0/timelapse',   '/media/usb0/timelapse'),
        (7, '/media/pi/PI_STICK',      '/media/pi/PI_STICK'))


def main():

    os.chdir(TIMELAPSE_CODE_PATH)

    if os.path.islink('timelapse_dir'):
        output = sp.check_output(['readlink', 'timelapse_dir'])
        print('\nCurrent image directory:', output.strip().decode('utf-8'))
    else:
        print('\nCurrent image directory not set')

    print('\nChoose image directory:\n')

    for menu_elem in MENU:
        print(str(menu_elem[0]) + ') ' + menu_elem[1] + ' - ' + menu_elem[2])

    print('x) Exit')

    while True:
        option = input('\nSelect image directory: ')
        if option == 'x':
            sys.exit(0)
        if option in ('1', '2', '3', '4', '5', '6', '7'):
            break
        print('Wrong option. Try again.')

    option = int(option) - 1

    sp.check_call(['rm', '-f', 'timelapse_dir'])

    timelapse_name = MENU[option][1]
    timelapse_dir = MENU[option][2]

    sp.check_call(['ln', '-s', timelapse_dir, 'timelapse_dir'])

    print('\nImage directory set to ' + timelapse_name + ': ' + timelapse_dir)


if __name__ == '__main__':
    main()
