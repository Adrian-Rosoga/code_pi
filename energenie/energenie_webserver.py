#!/usr/bin/env python3

#
# Energenie WebServer (was Phone Charger Web Server)
#
# Adrian Rosoga
# Version 1.0, 4 Feb 2018
# Version 2.0, 15 Aug 2019 - Renamed Energenie WebServer
# Version 3.0, 4 Sep 2019 - Moved to Python3 using 2to3 and pep8-ed it
#
# Used to charge the Acer S13 laptop
#

'''

'''

import sys
import traceback
import subprocess
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
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

            self.wfile.write(b'OK')

            # Do not close in Python3, it is done automatically
            # self.wfile.close()

        except Exception:
            print(('do_GET(): Caught exception:', sys.exc_info()[0]))
            traceback.print_exc()


try:
    server = HTTPServer(('', PORT), MyHandler)
    print("Started Energenie webserver on port", PORT, "for Energenie device number", ENERGENIE_DEVICE)
    server.serve_forever()
except KeyboardInterrupt:
    print("\n^C received, shutting down server")
    server.socket.close()
