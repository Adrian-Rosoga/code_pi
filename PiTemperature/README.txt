PiThermServer
=============

Simple NodeJS server and SQLite3 logger for the DS18B20 digital temperature sensor on the Raspberry Pi.

Description
-----------
A NodeJS server for the DS18B20 GPIO temperature sensor on the Raspberry Pi. The sensor is accessed using the w1-gpio and w1-therm kernel modules in the Raspbian distro. The server parses data from the sensor and returns the temperature and a Unix time-stamp in JSON format, this is then written to an SQLite database on the Pi. A simple front-end is included and served using node-static, which performs ajax calls to the server/database and plots temperature in real time or from a time-series, using the highcharts JavaScript library.

Files
-----
* load_gpio.sh - bash commands to load kernel modules
* server.js - NodeJS server, returns temperature as JSON, logs to database and serves other static files
* temperature_plot.htm - example client front-end showing live temperatures
* temperature_log.htm - example client front-end showing time-series from database records
* build_database.sh - shell script to create database schema
* sample_database.db - example database with real world data from the Pi recorded in UK Jan-Feb 2013

Usage
-----
* With sensor attached load kernel modules: sudo load_gpio.sh 
* Start server: node server.js

References
----------
http://www.cl.cam.ac.uk/freshers/raspberrypi/tutorials/temperature/

Screenshots/Images
------------------
<p><a href="http://tomholderness.files.wordpress.com/2013/02/ss_temperatured_db_log.png"><img src="http://tomholderness.files.wordpress.com/2013/02/ss_temperatured_db_log.png" alt="Temperature time-series plot" width="400"></a></p>
<p><a href="http://tomholderness.files.wordpress.com/2013/01/plot1.png"><img src="http://tomholderness.files.wordpress.com/2013/01/plot1.png" alt="Temperature plot" width="400"></a></p>
Screenshot of temperature plot
<p><a href="http://tomholderness.files.wordpress.com/2013/01/pi_temp_sensor_scaled.jpg"><img src="http://tomholderness.files.wordpress.com/2013/01/pi_temp_sensor_scaled.jpg" width="400"></a></p>
Raspberry Pi & DS18B20 digital thermometer

=== Sun 20 Oct 2013

Modified with custom HTTP handler from which the temperature is read instead of creating a htm file every second.

It still blocks and the page reads:

<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>503 Service Temporarily Unavailable</title>
</head><body>
<h1>Service Temporarily Unavailable</h1>
<p>The server is temporarily unable to service your
request due to maintenance downtime or capacity
problems. Please try again later.</p>
</body></html>

This comes from Apache maybe? Yes, it does!

Capacity and resilience test:
  # 16 tabs in IE. Started at 09:21:26:
    Accessing the service directly with: http://192.168.1.6:8000/temperature_dumb.htm
  # At 09:36, after 15 mins, it failed on 9 tabs and still working on 7!
  # All 15 tabs failed, last at 11:22

Test #2 - with only one tab:
  # Started 16:46:12
  # Dies 18:03:43

=== Wed 19 Mar 2014

- Created the SQLite db and moved it on the USB stick. Created soft link:
ln -s /media/usb/data/piTemps.db piTemps.db
