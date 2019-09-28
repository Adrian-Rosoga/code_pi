#!/usr/bin/python

"""
Timelapse Destination
Adrian Rosoga, 19 May 2014, refactored 29 Sep 2018
"""

import subprocess as sp
import sys
import os

TIMELAPSE_CODE_PATH='/home/pi/code_pi/timelapse'
os.chdir(TIMELAPSE_CODE_PATH)

menu = ((1, '/mnt/timelapse/tl',       '/mnt/timelapse/tl'),
        (2, '/mnt/timelapse/other',    '/mnt/timelapse/other'),
        (3, '/mnt/timelapse/rafi',     '/mnt/timelapse/rafi'),
        (4, '/mnt/timelapse/zero',     '/mnt/timelapse/zero'),
        (5, '/tmp/timelapse',          '/tmp/timelapse'),
        (6, 'USB Stick 0',             '/media/usb0/timelapse'),
        (7, 'USB Stick 1',             '/media/usb1/timelapse'),
        (8, 'WD Blue',                 '/media/WD_Blue/timelapse')
        )

if os.path.islink('timelapse_dir'):
    print '\nCurrent Destination: ', sp.check_output(['readlink', 'timelapse_dir'])
else:
    print '\nCurrent Destination: None'

print '\nNew Destination:\n'

for menu_elem in menu:
    print str(menu_elem[0]) + ') ' + menu_elem[1] + ' - ' + menu_elem[2]

print 'x) Exit'

while True:
    option = raw_input('\nSelect destination: ')
    if option == 'x':
        sys.exit(0)
    if option in ('1', '2', '3', '4', '5', '6', '7'):
        break
    print 'Wrong option. Try again.'

option = int(option) - 1

sp.check_call(['rm', '-f', 'timelapse_dir'])

timelapse_name = menu[option][1]
timelapse_dir = menu[option][2]

sp.check_call(['ln', '-s', timelapse_dir, 'timelapse_dir'])

print '\nDestination set to ' + timelapse_name + ': ' + timelapse_dir
