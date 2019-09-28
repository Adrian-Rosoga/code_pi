#!/usr/bin/env python

#
# DEPRECATED - Please use the Python 3 version!
#

#
# Energenie WebServer (was Phone Charger Web Server)
#
# Adrian Rosoga
# Version 1.0, 4 Feb 2018
# Version 2.0, 15 Aug 2019 - renamed Energenie WebServer
#
# Used to charge the Acer S13 laptop
#

'''
TODO
Change code in /usr/lib/python2.7/dist-packages/gpiozero/boards.py to avoid off when turning on
Real file is /usr/share/pyshared/gpiozero/boards.py
'''

import sys
import traceback
import subprocess
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from gpiozero import Energenie


#
# Configuration
#
ENERGENIE_DEVICE = 2
PORT = 8000


def run_cmd(cmd):
    ''' Utility that gets the first line from a cmd launched on a shell '''

    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = pipe.communicate()[0]
    return output


class MyHandler(SimpleHTTPRequestHandler, object):

    def do_GET(self):

        try:
            if self.path != '/off' and self.path != '/on':
                return SimpleHTTPRequestHandler.do_GET(self)

            # The second Energenie parameter is carefully selected here to avoid
            # toggling the state unnecessarily
            if self.path == '/on':
                device = Energenie(ENERGENIE_DEVICE, True)
                # device.on()
            else:
                device = Energenie(ENERGENIE_DEVICE, False)
                # device.off()

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()

            self.wfile.write('OK')

            self.wfile.close()

        except Exception:
            print 'Caught exception!'
            print sys.exc_info()[0]
            traceback.print_exc()


try:
    server = HTTPServer(('', PORT), MyHandler)
    print "Started Energenie webserver on port", PORT, "for Energenie device number", ENERGENIE_DEVICE
    server.serve_forever()
except KeyboardInterrupt:
    print("\n^C received, shutting down server")
    server.socket.close()
