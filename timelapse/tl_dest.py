#!/usr/bin/env python3

"""
Timelapse Destination
Adrian Rosoga, 19 May 2014, refactored 29 Sep 2018
"""

import sys
import os
import subprocess as sp
sys.path.append('/home/pi/code_pi/utilpy')
from getch import getch  # noqa


TIMELAPSE_CODE_PATH = '/home/pi/code_pi/timelapse'


MENU = ('/mnt/timelapse/tl',
        '/mnt/timelapse/other',
        '/mnt/timelapse/rafi',
        '/mnt/timelapse/zero',
        '/tmp/timelapse',
        '/mnt/pi_stick/timelapse')


def check_directory_exists(directory):
    '''Check directory exists'''

    if not os.path.exists(directory):
        msg = f'WARNING: The directory {directory} does not exist!'
        print('\n' + '=' * len(msg))
        print(msg)
        print('=' * len(msg))


def main():
    """Show and offer option to set the photos directory"""

    os.chdir(TIMELAPSE_CODE_PATH)

    if os.path.islink('timelapse_dir'):
        timelapse_dir = sp.check_output(['readlink', 'timelapse_dir'])
        timelapse_dir = timelapse_dir.strip().decode('utf-8')
        print('\nPhotos directory:', timelapse_dir)

        check_directory_exists(timelapse_dir)

    else:
        print('\nPhotos directory not set!')

    print('\nChoose photos directory or \'x\' to exit:\n')

    for index, menu_elem in enumerate(MENU):
        print(f'{index + 1}) {menu_elem}')

    print('x) Exit')

    while True:
        print('\nSelect photos directory:', end=' ', flush=True)
        option = getch()
        if option == 'x':
            sys.exit(0)
        elif option not in [str(nb + 1) for nb in range(len(MENU))]:
            print('Wrong option. Try again.')
        else:
            break

    option = int(option) - 1

    sp.check_call(['rm', '-f', 'timelapse_dir'])

    timelapse_dir = MENU[option]

    sp.check_call(['ln', '-s', timelapse_dir, 'timelapse_dir'])

    print(f'\nPhotos directory set to {timelapse_dir}')

    check_directory_exists(timelapse_dir)


if __name__ == '__main__':

    main()
