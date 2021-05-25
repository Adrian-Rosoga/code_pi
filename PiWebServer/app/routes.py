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


class Registry(object):
    title = "Thames"
    refresh = 1200
    port = 8007


def get_climate():
    temperature, humidity = HTU21D.get_temperature_humidity()
    return f"{temperature:0.1f}C - {humidity:0.1f}%H" if temperature and humidity else ""


def get_picture_filename():

    # # Filter for directory names starting with '201'
    # try:
    #     dirs = [directory for directory in os.listdir('.') if directory.find('202') != -1]
    #     if len(dirs) == 0:
    #         app.logger.warning('No directories starting with 202')
    #         return None
    #     last_dir_name = max(dirs)
    #     if last_dir_name is None:
    #         app.logger.warning('Last directory name is None')
    #         return None
    #     if len(last_dir_name) == 0:
    #         app.logger.warning('Last directory name is empty string')
    #         return None
    # except Exception:
    #     app.logger.warning('Exception thrown - no dir starting with 202', sys.exc_info()[0])
    #     return None

    # last_dir_path = os.path.join('.', last_dir_name)
    # if not os.path.isdir(last_dir_path):
    #     app.logger.warning('not os.path.isdir(last_dir_path)')
    #     app.logger.warning('last_dir_path = ' + last_dir_path)
    #     return None

    last_dir_path = "."

    files = os.listdir(last_dir_path)

    files.sort(key=lambda x: x)

    if len(files) == 0:
        app.logger.warning('No images')
        return None

    # Last picture is the one we are looking for
    last_picture = files[-1]

    # If it ends in '~' it's a temporary image file, try the previous one if it exists
    if last_picture.find('~') == -1:
        return os.path.join(last_dir_path, last_picture)
    else:
        if len(files) < 2:
            app.logger.warning('Less than 2 files')
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

    os.chdir("/tmp/timelapse")

    image = get_picture_filename()
    if image is None:
        image = 'out_of_hours.jpg'
        info = str(get_climate())
        image = "".join(["/static/", image])
    else:
        last_modified_date = time.ctime(os.path.getmtime(image))
        info = last_modified_date
        climate = get_climate()
        if climate != "":
            info += ' --- ' + climate
        image = "".join(["/static/timelapse/", image])

    app.logger.info(os.path.basename(image))

    return render_template('index.html', image=image, info=info, title=Registry.title, refresh=Registry.refresh)
