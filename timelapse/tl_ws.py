#!/usr/bin/python

"""
Timelapse Web Server
Adrian Rosoga
Version 1.0, 14 Jan 2014, refactored 29 Sep 2018
"""

import re
import time
import sys
import os
import traceback
import subprocess
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler


"""
TODO
- Report how long ago the file was taken
- Report reasons for missing picture: no dir, empty dir, etc

FIXME
192.168.1.106 - - [06/Oct/2019 14:25:23] "GET /2019/tl_1006142513.jpg HTTP/1.1" 200 -
Caught exception!
<class 'socket.error'>
Traceback (most recent call last):
  File "/home/pi/code_pi/timelapse/tl_ws.py", line 159, in do_GET
    return SimpleHTTPRequestHandler.do_GET(self)
  File "/usr/lib/python2.7/SimpleHTTPServer.py", line 48, in do_GET
    self.copyfile(f, self.wfile)
  File "/usr/lib/python2.7/SimpleHTTPServer.py", line 192, in copyfile
    shutil.copyfileobj(source, outputfile)
  File "/usr/lib/python2.7/shutil.py", line 66, in copyfileobj
    fdst.write(buf)
  File "/usr/lib/python2.7/socket.py", line 328, in write
    self.flush()
  File "/usr/lib/python2.7/socket.py", line 307, in flush
    self._sock.sendall(view[write_offset:write_offset+buffer_size])
error: [Errno 113] No route to host
----------------------------------------
Exception happened during processing of request from ('192.168.1.106', 38184)
Traceback (most recent call last):
  File "/usr/lib/python2.7/SocketServer.py", line 293, in _handle_request_noblock
    self.process_request(request, client_address)
  File "/usr/lib/python2.7/SocketServer.py", line 321, in process_request
    self.finish_request(request, client_address)
  File "/usr/lib/python2.7/SocketServer.py", line 334, in finish_request
    self.RequestHandlerClass(request, client_address, self)
  File "/usr/lib/python2.7/SocketServer.py", line 657, in __init__
    self.finish()
  File "/usr/lib/python2.7/SocketServer.py", line 716, in finish
    self.wfile.close()
  File "/usr/lib/python2.7/socket.py", line 283, in close
    self.flush()
  File "/usr/lib/python2.7/socket.py", line 307, in flush
    self._sock.sendall(view[write_offset:write_offset+buffer_size])
error: [Errno 32] Broken pipe
----------------------------------------

After CTRL-C it logged below and resumed working:

^C----------------------------------------
Exception happened during processing of request from ('192.168.1.106', 38188)
Traceback (most recent call last):
  File "/usr/lib/python2.7/SocketServer.py", line 293, in _handle_request_noblock
    self.process_request(request, client_address)
  File "/usr/lib/python2.7/SocketServer.py", line 321, in process_request
    self.finish_request(request, client_address)
  File "/usr/lib/python2.7/SocketServer.py", line 334, in finish_request
    self.RequestHandlerClass(request, client_address, self)
  File "/usr/lib/python2.7/SocketServer.py", line 655, in __init__
    self.handle()
  File "/usr/lib/python2.7/BaseHTTPServer.py", line 340, in handle
    self.handle_one_request()
  File "/usr/lib/python2.7/BaseHTTPServer.py", line 310, in handle_one_request
    self.raw_requestline = self.rfile.readline(65537)
  File "/usr/lib/python2.7/socket.py", line 480, in readline
    data = self._sock.recv(self._rbufsize)
KeyboardInterrupt
----------------------------------------
192.168.1.106 - - [06/Oct/2019 16:16:10] "GET /tl HTTP/1.1" 200 -
192.168.1.106 - - [06/Oct/2019 16:16:11] "GET /tl HTTP/1.1" 200 -
192.168.1.106 - - [06/Oct/2019 16:16:12] "GET /tl HTTP/1.1" 200 -
192.168.1.106 - - [06/Oct/2019 16:16:13] "GET /tl HTTP/1.1" 200 -
192.168.1.106 - - [06/Oct/2019 16:16:13] "GET /tl HTTP/1.1" 200 -
192.168.1.101 - - [06/Oct/2019 16:17:39] "GET /tl HTTP/1.1" 200 -
192.168.1.101 - - [06/Oct/2019 16:17:39] "GET /2019/tl_1006161733.jpg HTTP/1.1" 200 -
192.168.1.101 - - [06/Oct/2019 16:17:45] "GET /tl HTTP/1.1" 200 -
192.168.1.101 - - [06/Oct/2019 16:17:46] "GET /2019/tl_1006161743.jpg HTTP/1.1" 200 -


Another CTRL-C got it killed as expected:

192.168.1.101 - - [06/Oct/2019 16:19:15] "GET /2019/tl_1006161913.jpg HTTP/1.1" 200 -
192.168.1.101 - - [06/Oct/2019 16:19:25] "GET /tl HTTP/1.1" 200 -
192.168.1.101 - - [06/Oct/2019 16:19:26] "GET /2019/tl_1006161923.jpg HTTP/1.1" 200 -
^C^C received, shutting down server

"""


#
# Configuration
#
PORT = 8007
DS18B20_OUTPUT_FILE = '/sys/bus/w1/devices/28-0000045bf342/w1_slave'


def run_cmd(cmd):
    """ Utility that gets the first line from a cmd launched on a shell """
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = pipe.communicate()[0]
    return output


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
    #return 'N/A'
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
        last_dir_name = max(filter(lambda dir: dir.find('2019') != -1, os.listdir('.')))
        if last_dir_name == None:
            print('WARNING: last_dir_name == None')
            return None
        if len(last_dir_name) == 0:
            print('WARNING: len(last_dir_name) == 0')
            return None
    except:
        print('WARNING: exception thrown - no dir starting with 201')
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
        #image = os.path.join('.', 'out_of_hours_picture.jpg')
        image = 'out_of_hours_picture.jpg'

    # print 'Image path:', image
    if image is not None:
        last_modified_date = time.ctime(os.path.getmtime(image))
        body = body.replace('XXX_IMAGE_XXX', image);

        body = body.replace('XXX_INFO_XXX', image + ' --- ' + str(get_temperature()) +
                            '--- ' + last_modified_date)
        #body = body.replace('XXX_INFO_XXX', 'St. George Wharf *** ' + last_modified_date)

    return body


class MyHandler(SimpleHTTPRequestHandler, object):

    def do_GET(self):

        try:
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write('Testing. Site under construction.')
                self.wfile.close()
                return

            if self.path != "/tl":
                return SimpleHTTPRequestHandler.do_GET(self)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            self.wfile.write(make_body())

            self.wfile.close()

        except:
            print('Caught exception!')
            print(sys.exc_info()[0])
            traceback.print_exc()


try:
    TIMELAPSE_CODE_PATH = '/home/pi/code_pi/timelapse'
    os.chdir(TIMELAPSE_CODE_PATH)

    timelapse_dir = subprocess.check_output(['readlink', 'timelapse_dir']).rstrip()
    print('Serving from ' + timelapse_dir)

    os.chdir(timelapse_dir)

    server = HTTPServer(('', PORT), MyHandler)
    print('Started HTTP server on port ' + str(PORT))
    server.serve_forever()

except KeyboardInterrupt:
    print("^C received, shutting down server")
    server.socket.close()
