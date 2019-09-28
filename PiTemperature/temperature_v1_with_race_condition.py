#!/usr/bin/python

# Get the temperature from a DS18B20 1-wire digital temperature sensor attached to a Raspberry Pi

#
# Adrian Rosoga, 11 Apr 2013
#

# Format of the file
# 71 01 4b 46 7f ff 0f 10 56 : crc=56 YES
# 71 01 4b 46 7f ff 0f 10 56 t=23062

import re
import time
import thread
import SimpleHTTPServer
import SocketServer
import os

#
# Configuration
#
MAX_TEMPERATURE_ALERT = 22.0
MIN_TEMPERATURE_ALERT = 16.0
TIME_BETWEEN_READINGS = 1
OUT_FILE = "temperature_dumb.htm"
OUT_FILE_TMP = "temperature_dumb_tmp.htm"
PORT = 8000
#DS18B20_OUTPUT_FILE = "w1_slave"
DS18B20_OUTPUT_FILE = "/sys/bus/w1/devices/28-0000045bf342/w1_slave"


regex = re.compile(r"t=(\d+)")

def get_temperature():
    ''' Get the temperature '''
    file = open(DS18B20_OUTPUT_FILE, 'r')
    file.readline()
    line = file.readline()
    file.close()
    #print line
    m = regex.search(line)
    if m:
    	blob = m.group(0)
    	temperature = blob[2:4] + "." + blob[4:5]
    else:
        temperature = str(0.0)
#    print temperature
    return temperature


body_template = str("<HTML>\n\
<HEAD>\n\
<TITLE>Temperature</TITLE>\n\
<META HTTP-EQUIV=\"PRAGMA\" CONTENT=\"NO-CACHE\">\n\
<META HTTP-EQUIV=\"EXPIRES\" CONTENT=\"-1\">\n\
<META HTTP-EQUIV=\"REFRESH\" CONTENT=\"30\">\n\
</HEAD>\n\
<BODY>\n\
<B>\n\
<BR>\n\
\
<P align=\"center\">\
<FONT SIZE=\"10\" FACE=\"COURIER NEW\" COLOR=\"BLACK\">\n\
Temperature Monitor</FONT>\n\
<BR>\
<FONT SIZE=\"5\" FACE=\"COURIER NEW\" COLOR=\"BLACK\">\n\
(Raspberry Pi, DS18B20, node.js, Highcharts, SQLite, Python)</FONT>\n\
\
<BR><BR><BR>\n\
\
<FONT SIZE=\"12\" FACE=\"COURIER NEW\" COLOR=\"BLACK\">\n\
XXX_DATE_XXX</FONT>\n\
\
<BR><BR>\n\
\
<FONT SIZE=\"12\" FACE=\"COURIER NEW\" COLOR=\"XXX_COLOR_XXX\">\n\
XXX_TEMPERATURE_XXX Celsius</FONT>\n\
\
<BR><BR><BR>\n\
\
<FONT SIZE=\"5\" FACE=\"COURIER NEW\" COLOR=\"RED\">\n\
XXX_ALERT_XXX</FONT>\n\
\
<BR><HR>\n\
\
<FONT SIZE=\"3\" FACE=\"COURIER NEW\" COLOR=\"BLACK\">\n\
Page autorefreshes every 30 seconds.</FONT>\n\
\
</P>\
\
</B>\n\
</BODY>\n\
</HTML>")


# Write to a temporary file and then rename it
def write_to_file(time, temperature, alert, color):
    ''' Write temperature  '''

    out_file = open(OUT_FILE_TMP, 'w')

    # Build body
    body = body_template
    body = body.replace("XXX_DATE_XXX", time)
    body = body.replace("XXX_TEMPERATURE_XXX", temperature)
    body = body.replace("XXX_ALERT_XXX", alert)
    body = body.replace("XXX_COLOR_XXX", color)

    out_file.write(body)
    out_file.close()

    os.rename(OUT_FILE_TMP, OUT_FILE)

    # Testing
    #print body

def go():
    ''' Main loop  '''
    print "Started..."
    while 1:
        temperature = get_temperature()
        #print time.ctime() + "," + temperature
        color = "BLACK"
        alert = ""
        if (float(temperature) >= MAX_TEMPERATURE_ALERT):
            #print "ALERT: " + temperature + " is above " + str(MAX_TEMPERATURE_ALERT)
            alert = "ALERT - Temperature is above the maximum of " + str(MAX_TEMPERATURE_ALERT) + " Celsius"
            color = "RED"
        elif (float(temperature) <= MIN_TEMPERATURE_ALERT):
            #print "ALERT: " + temperature + " is below " + str(MIN_TEMPERATURE_ALERT)
            alert = "ALERT - Temperature is below the minimum of " + str(MAX_TEMPERATURE_ALERT) + " Celsius"
            color = "RED"
        else:
            color = "GREEN"
        write_to_file(time.ctime(), temperature, alert, color)
        time.sleep(TIME_BETWEEN_READINGS)

def run_web_server():
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", PORT), Handler)
    print "Serving at port", PORT
    httpd.serve_forever()

#
# Start web server in a thread
#
thread.start_new_thread(run_web_server, ())

go()

