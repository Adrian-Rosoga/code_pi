#!/usr/bin/env python3

"""
Timelapse Web Server
Adrian Rosoga
Version 1.0, 14 Jan 2014, refactored 29 Sep 2018
"""

import re
import time
import sys
import os
import socket
import traceback
import subprocess
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler


"""
TODO
- Report how long ago the file was taken
- Report reasons for missing picture: no dir, empty dir, etc
"""


#
# Configuration
#
PORT = 8007
FAVICON = '/home/pi/code_pi/timelapse/favicon.ico'
DS18B20_OUTPUT_FILE = '/sys/bus/w1/devices/28-0000045bf342/w1_slave'


def run_cmd(cmd):
    """ Utility that gets the first line from a cmd launched on a shell """
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = pipe.communicate()[0]
    return str(output)


regex = re.compile(r't=(\d+)')


def get_temperature_DS18B20():

    # Uncomment if no temperature sensor attached
    return 'N/A'

    file = open(DS18B20_OUTPUT_FILE, 'r')
    file.readline()
    line = file.readline()
    file.close()
    data = regex.search(line)
    temperature = float(data.group(1)[0:4]) / 100.0
    return temperature


def get_temperature():

    # Uncomment if no temperature sensor attached
    # return 'N/A'
    return run_cmd('sudo /home/pi/code_pi/HTU21/HTU21D.py')


body_template = """<HTML>
<HEAD>
<TITLE>Team GBLM</TITLE>
<META HTTP-EQUIV=PRAGMA CONTENT=NO-CACHE>
<META HTTP-EQUIV=EXPIRES CONTENT=-1>
<META HTTP-EQUIV=REFRESH CONTENT=10>
</HEAD>
<BODY BGCOLOR="BLACK" BACKGROUND_X="grill.jpg">
<H2 ALIGN="CENTER">
<B><FONT COLOR="YELLOW">XXX_INFO_XXX</FONT></B>
</H2>
<P ALIGN="CENTER">
<IMG SRC="XXX_IMAGE_XXX" STYLE="HEIGHT: 100%" ALT="NO IMAGE!" WIDTH_X="420" HEIGHT_X="420">
</P>
</BODY>
</HTML>"""


def get_picture_filename():
    # Filter for directory names starting with '201'
    try:
        last_dir_name = max([dir for dir in os.listdir('.') if dir.find('2019') != -1])
        if last_dir_name is None:
            print('WARNING: last_dir_name == None')
            return None
        if len(last_dir_name) == 0:
            print('WARNING: len(last_dir_name) == 0')
            return None
    except Exception:
        print('WARNING: exception thrown - no dir starting with 201', sys.exc_info()[0])
        return None

    last_dir_path = os.path.join('.', last_dir_name)
    if not os.path.isdir(last_dir_path):
        print('WARNING: not os.path.isdir(last_dir_path)')
        print('last_dir_path = ' + last_dir_path)
        return None

    files = os.listdir(last_dir_path)

    files.sort(key=lambda x: x)

    if len(files) == 0:
        print('WARNING: len(files) == 0')
        return None

    # Last picture is the one we are looking for
    last_picture = files[-1]

    # If it ends in '~' it's a temporary image file, try the previous one if it exists
    if last_picture.find('~') == -1:
        return os.path.join(last_dir_path, last_picture)
    else:
        if len(files) < 2:
            print('WARNING: len(files) < 2')
            return None
        last_picture = files[-2]
        return os.path.join(last_dir_path, last_picture)


def make_body():
    body = body_template

    image = get_picture_filename()
    if image is None:
        # image = os.path.join('.', 'out_of_hours_picture.jpg')
        image = 'out_of_hours_picture.jpg'

    # print 'Image path:', image
    if image is not None:
        last_modified_date = time.ctime(os.path.getmtime(image))
        body = body.replace('XXX_IMAGE_XXX', image)

        body = body.replace('XXX_INFO_XXX', image + ' --- ' + str(get_temperature()) +
                            '--- ' + last_modified_date)
        # body = body.replace('XXX_INFO_XXX', 'St. George Wharf *** ' + last_modified_date)

    return body


class MyHandler(SimpleHTTPRequestHandler, object):

    def do_GET(self):

        try:
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write(b'Testing. Site under construction.')
                return

            elif self.path == "/favicon.ico":
                with open(FAVICON, 'rb') as f:
                    favicon = f.read()

                self.send_response(200)
                self.end_headers()

                self.wfile.write(favicon)
                return

            elif self.path != "/tl":
                return SimpleHTTPRequestHandler.do_GET(self)

            else:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write(str.encode(make_body()))

        except socket.error as e:
            print('do_GET(): Caught socket.error exception:', e)
            traceback.print_exc()

        # Usually is <class 'socket.error'>, error: [Errno 113] No route to host
        except Exception:
            print('do_GET(): Caught exception:', sys.exc_info()[0])
            traceback.print_exc()


try:
    timelapse_dir = subprocess.check_output(['readlink', 'timelapse_dir']).rstrip()
    print('Image directory:', timelapse_dir.decode())

    os.chdir(timelapse_dir)

    server = HTTPServer(('', PORT), MyHandler)
    print('Started the webcam HTTP server on port', PORT)
    server.serve_forever()

    print('CRASHED OUT OF THE SERVER LOOP')

except KeyboardInterrupt:
    print("\n^C received, shutting down server")
    server.socket.close()
