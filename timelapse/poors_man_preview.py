#!/usr/bin/python

#
# Poors man raspistill preview
# Adrian Rosoga, 27 Dec 2013
#

import os, time

while True:
    os.system('sudo raspistill -n -t 1000 -o /var/log/preview.jpg')
    print 'Captured'
    print 'Entering sleep after capture'
    #time.sleep(10)
    print 'Exiting sleep after capture'
    os.system('gpicview /var/log/preview.jpg &')
    time.sleep(5)
    os.system('wmctrl -r preview.jpg -e 0,0,0,640,480')
    print 'Preview started'
    time.sleep(10)
    os.system('pkill gpicview')
    print 'Viewer killed'
