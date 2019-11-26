from flask import render_template
from flask import send_from_directory
from app import app

import time
import datetime
import sys
import os
sys.path.append('/home/pi/code_pi/utilpy')
import HTU21D  # noqa

#
# Configuration
#
FAVICON_PATH = '/home/pi/code_pi/timelapse/favicon.ico'
OUT_OF_HOURS_IMAGE_PATH = '/home/pi/code_pi/timelapse/out_of_hours.jpg'

request_count = 0


class Registry(object):
    title = "TITLE"
    refresh = 10
    port = 8007


def get_climate():
    temperature, humidity = HTU21D.get_temperature_humidity()
    if temperature is None or humidity is None:
        return "N/A"
    else:
        return "{0:0.1f}C - {1:0.1f}%H".format(temperature, humidity)


def get_picture_filename():
    # Filter for directory names starting with '201'
    try:
        last_dir_name = max([directory for directory in os.listdir('.') if directory.find('2019') != -1])
        if last_dir_name is None:
            app.logger.info('WARNING: last_dir_name == None')
            return None
        if len(last_dir_name) == 0:
            app.logger.info('WARNING: len(last_dir_name) == 0')
            return None
    except Exception:
        app.logger.info('WARNING: exception thrown - no dir starting with 201', sys.exc_info()[0])
        return None

    last_dir_path = os.path.join('.', last_dir_name)
    if not os.path.isdir(last_dir_path):
        app.logger.info('WARNING: not os.path.isdir(last_dir_path)')
        app.logger.info('last_dir_path = ' + last_dir_path)
        return None

    files = os.listdir(last_dir_path)

    files.sort(key=lambda x: x)

    if len(files) == 0:
        app.logger.info('WARNING: len(files) == 0')
        return None

    # Last picture is the one we are looking for
    last_picture = files[-1]

    # If it ends in '~' it's a temporary image file, try the previous one if it exists
    if last_picture.find('~') == -1:
        return os.path.join(last_dir_path, last_picture)
    else:
        if len(files) < 2:
            app.logger.info('WARNING: len(files) < 2')
            return None
        last_picture = files[-2]
        return os.path.join(last_dir_path, last_picture)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route('/')
@app.route('/tl')
@app.route('/index')
def index():

    global request_count

    os.chdir("/tmp/timelapse")

    image = get_picture_filename()
    if image is None:
        image = 'out_of_hours.jpg'
        info = str(get_climate())
        image = "".join(["/static/", image])
    else:
        last_modified_date = time.ctime(os.path.getmtime(image))
        info = last_modified_date + ' --- ' + str(get_climate())
        image = "".join(["/static/timelapse/", image])

    request_count = request_count + 1

    print(datetime.datetime.now(), "-", os.getpid(), "-", os.path.basename(image), "-",  request_count)    

    return render_template('index.html', image=image, info=info, title=Registry.title, refresh=Registry.refresh)
