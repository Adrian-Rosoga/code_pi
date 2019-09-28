#!/usr/bin/python

#
# One-trick-pony web server serving page with temperature reading
# from DS18B20 sensor attached to a Raspberry Pi
#

#
# Configuration
#
PORT = 8000
DS18B20_OUTPUT_FILE = '/sys/bus/w1/devices/28-0000045bf342/w1_slave'
MAX_TEMPERATURE_ALERT = 22.0
MIN_TEMPERATURE_ALERT = 18.0

import re, time
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

regex = re.compile(r't=(\d+)')

def get_temperature():
    file = open(DS18B20_OUTPUT_FILE, 'r')
    file.readline()
    line = file.readline()
    file.close()
    data = regex.search(line)
    temperature = float(data.group(1)[0:4])/100.0
    return temperature

body_template = '<HTML>\
<HEAD>\
<TITLE>Temperature</TITLE>\
<META HTTP-EQUIV=PRAGMA CONTENT=NO-CACHE>\
<META HTTP-EQUIV=EXPIRES CONTENT=-1>\
<META HTTP-EQUIV=REFRESH CONTENT=30>\
</HEAD>\
<BODY>\
<B><BR>\
<P ALIGN=CENTER>\
<FONT SIZE=12>Web Thermometer</FONT>\
<BR>\
<FONT SIZE=5>(Raspberry Pi, DS18B20)</FONT>\
<BR><BR><BR>\
<FONT SIZE=14 COLOR=%s>%s &deg;C</FONT>\
<BR><BR><BR>\
<FONT SIZE=6>%s</FONT>\
<BR><BR>\
<FONT SIZE=5 COLOR=RED>%s</FONT>\
<BR><HR>\
<FONT SIZE=3>Page autorefreshes every 30 seconds.</FONT>\
</P>\
</B>\
</BODY>\
</HTML>'

class TemperatureHandler(SimpleHTTPRequestHandler, object):
    def do_GET(self):
        # Only the request for favicon is honored, for all else tell the temperature
        if self.path == '/favicon.ico':
            return SimpleHTTPRequestHandler.do_GET(self)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        temperature = get_temperature()
        print 'Temperature = ' + str(temperature)
        alert = ''
        color = 'GREEN'
        if (temperature > MAX_TEMPERATURE_ALERT):
            alert = 'ALERT - Temperature above ' + str(MAX_TEMPERATURE_ALERT) + ' &deg;C!'
            color = 'RED'
        elif (temperature < MIN_TEMPERATURE_ALERT):
            alert = 'ALERT - Temperature below ' + str(MIN_TEMPERATURE_ALERT) + ' &deg;C!'
            color = 'RED'

        self.wfile.write( body_template % (color, temperature, time.ctime(), alert
) )
        self.wfile.close()
        
try:
    server = HTTPServer(('', PORT), TemperatureHandler)
    print 'Started HTTP server on port ' + str(PORT) + '...'
    server.serve_forever()
except KeyboardInterrupt:
    print('^C received, shutting down...')
    server.socket.close()
    
    


