#!/usr/bin/env python

#
# Adrian Rosoga, 18 Sep 2019
#

from __future__ import print_function
import boto3
import sys
import time
import os
import pprint
import shutil


MINS_TO_SLEEP = 5
ON = True
OFF = False
PHOTO_DIR = '/tmp/timelapse'
PHOTO_SAVE_DIR = '/mnt/lenolin_speed/face_recognition/'


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


def copy_file(image_file, tag):
    try:
        # shutil.copy(image_file, PHOTO_SAVE_DIR)
        # shutil.copy2(image_file, PHOTO_SAVE_DIR)

        name, extension = os.path.basename(image_file).split('.')
        cmd = 'cp ' + image_file + ' ' + PHOTO_SAVE_DIR + name + '_' + tag + '.' + extension
        os.system(cmd)
    except IOError as e:
        print("Unable to copy file. %s" % e)
    except:
        print("Unexpected error:", sys.exc_info())


def action(on_off):

    if on_off == ON:
        os.system('/home/pi/code_pi/PiRekognition/hs100_lamp_on.sh')
    else:
        os.system('/home/pi/code_pi/PiRekognition/hs100_lamp_off.sh')


def check(image_file, client):
    localtime = time.localtime()
    timestamp = time.strftime("%I:%M:%S %p", localtime)

    with open(image_file, 'rb') as image:
        response = client.detect_faces(Image={'Bytes': image.read()}, Attributes=['ALL'])

    pprint.pprint(response)
    print('\n')

    tag = ''
    if response['FaceDetails'] is not None and len(response['FaceDetails']) > 0:

        for label in response['FaceDetails']:

            print(timestamp + ': ' + image_file + ': ' + str(label['EyesOpen']) + ' : ' + str(label['Confidence']))

            if label['EyesOpen']['Value']:
                if label['EyesOpen']['Confidence'] >= 90.0:
                    tag = 'eyes_open'
                    action(ON)
                else:
                    tag = 'eyes_open_but_maybe_not'
                    action(OFF)

            else:
                tag = 'eyes_closed'
                action(OFF)

            tag = tag + '_' + '{:.1f}'.format(label['EyesOpen']['Confidence']) + '_' + \
                  '{:.1f}'.format(label['Confidence'])

    else:
        print(timestamp + ': ' + image_file + ": No 'FaceDetails' element")
        tag = 'no_face_details'

        action(OFF)

    copy_file(image_file, tag)

    name, extension = os.path.basename(image_file).split('.')
    response['Photo'] = name + '_' + tag + '.' + extension


if __name__ == "__main__":

    os.chdir(PHOTO_DIR)

    client = boto3.client('rekognition')

    while True:

        timestamp = time.localtime()

        if timestamp.tm_hour >= 5 and timestamp.tm_hour <= 6:
        # if True:

            last_picture = get_picture_filename()
            last_picture = os.path.join(PHOTO_DIR, last_picture)

            print('Processing photo', last_picture)

            check(last_picture, client)

        else:

            print('Outside checking hours, now hour is', timestamp.tm_hour)

        print('Sleeping now', MINS_TO_SLEEP, 'minutes...')
        time.sleep(MINS_TO_SLEEP * 60)
