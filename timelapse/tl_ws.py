#!/usr/bin/env python3

"""
Timelapse Web Server
Adrian Rosoga
Version 1.0, 14 Jan 2014, refactored 29 Sep 2018
"""

import time
import sys
import os
import socket
import traceback
import subprocess
import logging
import argparse
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
sys.path.append('/home/pi/code_pi/utilpy')
import HTU21D


"""
TODO
- Report how long ago the file was taken
- Report reasons for missing picture: no dir, empty dir, etc
"""


#
# Configuration
#
FAVICON_PATH = '/home/pi/code_pi/timelapse/favicon.ico'
OUT_OF_HOURS_IMAGE_PATH = '/home/pi/code_pi/timelapse/out_of_hours.jpg'


class Registry(object):
    title = "TITLE"
    refresh = 10
    port = 8007


BODY_TEMPLATE = """<HTML>
<HEAD>
<TITLE>{title}</TITLE>
<META HTTP-EQUIV=PRAGMA CONTENT=NO-CACHE>
<META HTTP-EQUIV=EXPIRES CONTENT=-1>
<META HTTP-EQUIV=REFRESH CONTENT={refresh}>
</HEAD>
<BODY BGCOLOR="BLACK" BACKGROUND_XDISABLE="grill.jpg">
<H2 ALIGN="CENTER">
<B><FONT COLOR="YELLOW">{info}</FONT></B>
</H2>
<P ALIGN="CENTER">
<IMG SRC="{image}" STYLE="HEIGHT: 100%" ALT="NO IMAGE!" WIDTH_X="420" HEIGHT_X="420">
</P>
</BODY>
</HTML>"""


def get_climate():
    temperature, humidity = HTU21D.get_temperature_humidity()
    if temperature is None or humidity is None:
        return "N/A"
    else:
        return "{0:0.1f}&deg;C - {1:0.1f}%H".format(temperature, humidity)


def get_picture_filename():
    # Filter for directory names starting with '201'
    try:
        last_dir_name = max([directory for directory in os.listdir('.') if directory.find('2019') != -1])
        if last_dir_name is None:
            logging.info('WARNING: last_dir_name == None')
            return None
        if len(last_dir_name) == 0:
            logging.info('WARNING: len(last_dir_name) == 0')
            return None
    except Exception:
        logging.info('WARNING: exception thrown - no dir starting with 201', sys.exc_info()[0])
        return None

    last_dir_path = os.path.join('.', last_dir_name)
    if not os.path.isdir(last_dir_path):
        logging.info('WARNING: not os.path.isdir(last_dir_path)')
        logging.info('last_dir_path = ' + last_dir_path)
        return None

    files = os.listdir(last_dir_path)

    files.sort(key=lambda x: x)

    if len(files) == 0:
        logging.info('WARNING: len(files) == 0')
        return None

    # Last picture is the one we are looking for
    last_picture = files[-1]

    # If it ends in '~' it's a temporary image file, try the previous one if it exists
    if last_picture.find('~') == -1:
        return os.path.join(last_dir_path, last_picture)
    else:
        if len(files) < 2:
            logging.info('WARNING: len(files) < 2')
            return None
        last_picture = files[-2]
        return os.path.join(last_dir_path, last_picture)


def make_body():
    image = get_picture_filename()
    if image is None:
        image = 'OUT_OF_HOURS_IMAGE_PATH.jpg'
        info = str(get_climate())
    else:
        last_modified_date = time.ctime(os.path.getmtime(image))
        info = last_modified_date + ' --- ' + str(get_climate())

    return BODY_TEMPLATE.format(image=image, info=info, title=Registry.title, refresh=Registry.refresh)


class WebcamHandler(SimpleHTTPRequestHandler, object):

    def do_GET(self):

        try:
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b'Site under construction.')
                return

            elif self.path == "/favicon.ico":
                with open(FAVICON_PATH, 'rb') as f:
                    content = f.read()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(content)
                    return

            elif self.path == "/out_of_hours.jpg":
                with open(OUT_OF_HOURS_IMAGE_PATH, 'rb') as f:
                    content = f.read()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(content)
                    return

            elif self.path != "/tl":
                return SimpleHTTPRequestHandler.do_GET(self)

            else:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(str.encode(make_body()))

        # Most of the time "<class 'socket.error'>, error: [Errno 113] No route to host" gets thrown
        except socket.error as e:
            logging.info('do_GET(): Caught socket.error exception:', e)
            traceback.print_exc()

        except Exception:
            logging.info('do_GET(): Caught exception:', sys.exc_info()[0])
            traceback.print_exc()


try:
    logging.basicConfig(format="%(asctime)-15s %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='WebServer')
    parser.add_argument('--title', help='set title')
    parser.add_argument('--refresh', help='automatic refresh in seconds')
    parser.add_argument('--port', help='port')
    args = parser.parse_args()

    if args.title:
        Registry.title = args.title
    if args.refresh:
        Registry.refresh = args.refresh
    if args.port:
        Registry.port = args.port

    timelapse_dir = subprocess.check_output(['readlink', 'timelapse_dir']).rstrip()
    logging.info('Image directory: %s', timelapse_dir.decode())

    os.chdir(timelapse_dir)

    server = HTTPServer(('', Registry.port), WebcamHandler)
    logging.info('Started the HTTP server on port %s', Registry.port)
    server.serve_forever()

except KeyboardInterrupt:
    logging.info("\n^C received, shutting down the HTTP server")

finally:
    server.socket.close()
