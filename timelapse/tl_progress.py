#!/usr/bin/python

"""
tlp - Time-lapse Progress
Adrian Rosoga, 13 Jan 2014, refactored 29 Sep 2018
"""

import subprocess as sp
from time import sleep
import sys
import os

TIMELAPSE_CODE_PATH='/home/pi/code_pi/timelapse'
os.chdir(TIMELAPSE_CODE_PATH)


def run_cmd(cmd):
        p = sp.Popen(cmd, shell=True, stdout=sp.PIPE)
        output = p.communicate()[0]
        return output


timelapse_dir = sp.check_output(['readlink', 'timelapse_dir']).rstrip()

old_count = -1

print '\nDestination: ' + timelapse_dir

while True:
    print '\n---------------------------------'
    last_dir = run_cmd('ls -1rt ' + timelapse_dir + ' | tail -1')[:-1]
    print 'Directory: ' + last_dir
    new_count = run_cmd('ls ' + timelapse_dir + '/' + last_dir + ' | wc -l')[:-1]
    print str(new_count) + ' photos'
    os.system('date')
    os.system('ps -eaf | grep raspistill | grep -v grep')

    if new_count == old_count:
        print '!!!!!!! ALERT !!!!!!!'
    old_count = new_count

    os.system('df -h ' + timelapse_dir + '/' + last_dir)

    sleep(30) 
