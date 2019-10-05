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
import unittest
import io
from PIL import Image, ImageDraw, ExifTags, ImageColor, ImageFont
from PIL.ExifTags import TAGS


MINS_TO_SLEEP = 5
ON = True
OFF = False
PHOTO_DIR = '/tmp/timelapse'
IMAGE_DESTINATION_DIR = '/mnt/lenolin_speed/face_recognition/'


def get_exif(pil_image):
    exif_info = {}
    info = pil_image._getexif()
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        exif_info[decoded] = value
    return exif_info


'''
None of the 3 viewers listed /usr/lib/python2.7/dist-packages/PIL/c
was available on the distribution.
A few options are available:
# Hack the above ImageShow.py and add an existing viewer - e.g. gpicview
# Install display, xv, eog. ImageMagick might make xv available - TBC.
'''
def show_faces(response, stream, image_file, tag):

    image = Image.open(stream)

    imgWidth, imgHeight = image.size
    draw = ImageDraw.Draw(image)

    #  Find out available fonts with fc-list
    font = ImageFont.truetype("FreeSansBold.ttf", 32)
    #font = ImageFont.truetype('arial', 32)

    exif_info = get_exif(image)
    # '2019:10:03 11:24:52'
    date_taken = str(exif_info['DateTime'])

    annotation = ''
    index = 1

    text_width, text_height = font.getsize(date_taken)
    draw.rectangle((0, 0, text_width, 40), fill='black')
    draw.text((0, 0), date_taken, fill='yellow', font=font)

    # Display bounding boxes for each detected face
    for faceDetail in response['FaceDetails']:

        print('The detected face is between ' + str(faceDetail['AgeRange']['Low'])
              + ' and ' + str(faceDetail['AgeRange']['High']) + ' years old')

        box = faceDetail['BoundingBox']
        left = imgWidth * box['Left']
        top = imgHeight * box['Top']
        width = imgWidth * box['Width']
        height = imgHeight * box['Height']

        print('Left: ' + '{0:.0f}'.format(left))
        print('Top: ' + '{0:.0f}'.format(top))
        print('Face Width: ' + "{0:.0f}".format(width))
        print('Face Height: ' + "{0:.0f}".format(height))

        points = (
            (left, top),
            (left + width, top),
            (left + width, top + height),
            (left, top + height),
            (left, top)
        )
        draw.line(points, fill='yellow', width=2)

        annotation = 'Face #' + str(index) + ': EyesOpen=' + str(faceDetail['EyesOpen']['Value']) + \
               ' - EyesOpenConfidence=' + '{:.1f}'.format(faceDetail['EyesOpen']['Confidence']) + '% - ' +\
               'Confidence=' + '{:.1f}'.format(faceDetail['Confidence']) + '%'

        text_width, text_height = font.getsize(annotation)
        draw.rectangle((0, 40 * index, text_width, 40 * (index + 1)), fill='black')
        draw.text((0, 40 * index), annotation, fill='yellow', font=font)

        draw.text((left, top), str(index), fill='yellow', font=font)

        index = index + 1

    if index == 1:
        text_width, text_height = font.getsize(annotation)
        draw.rectangle((0, 40 * index, text_width,  40 * (index + 1)), fill='black')
        annotation = 'No face details'
        draw.text((0, 40 * index), annotation, fill='yellow', font=font)

    # Usable for debugging only
    # image.show()

    name, extension = os.path.basename(image_file).split('.')

    #annotated_file = name + '_' + tag + '.' + extension

    # From '2019:10:03 11:24:52' to Dropbox-like format '2019-10-03 11.24.52'
    date_taken = date_taken.replace(':', '-', 2)
    date_taken = date_taken.replace(':', '.')

    annotated_file = date_taken + ' ' + tag + '.' + extension

    image.save(os.path.join(IMAGE_DESTINATION_DIR, annotated_file))


def get_image_filename():
    # Filter for directory names starting with '201'
    try:
        last_dir_name = max(filter(lambda dir: dir.find('2019') != -1, os.listdir('.')))
        if last_dir_name is None:
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

    # Last image is the one we are looking for
    last_image = files[-1]

    # If it ends in '~' it's a temporary image file, try the previous one if it exists
    if last_image.find('~') == -1:
        return os.path.join(last_dir_path, last_image)
    else:
        if len(files) < 2:
            print('WARNING: len(files) < 2')
            return None
        last_image = files[-2]
        return os.path.join(last_dir_path, last_image)


def copy_file(image_file, tag):
    try:
        name, extension = os.path.basename(image_file).split('.')
        cmd = 'cp ' + image_file + ' ' + IMAGE_DESTINATION_DIR + name + '_' + tag + '.' + extension
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


def check(image_file, client, show=False):

    eyes_open = None
    tag = ''
    response = None

    with open(image_file, 'rb') as image:
        response = client.detect_faces(Image={'Bytes': image.read()}, Attributes=['ALL'])

        if response['FaceDetails'] is not None and len(response['FaceDetails']) == 1:

            for label in response['FaceDetails']:

                if label['EyesOpen']['Value']:
                    if label['EyesOpen']['Confidence'] >= 90.0:
                        eyes_open, tag = True, 'eyes_open'
                    else:
                        eyes_open, tag = False, 'eyes_probably_closed'
                else:
                    eyes_open, tag = False, 'eyes_closed'

                tag = tag + '_' + '{:.1f}'.format(label['EyesOpen']['Confidence']) + '_' + \
                      '{:.1f}'.format(label['Confidence'])

        elif response['FaceDetails'] is not None and len(response['FaceDetails']) > 0:

            eyes_open, tag = False, 'more_than_one_faces'

        else:

            eyes_open, tag = None, 'no_face_details'

        response['ImageOriginal'] = image_file

        if show:
            show_faces(response, image, image_file, tag)

    return response, eyes_open, tag


class AwakeTest(unittest.TestCase):

    def test(self):
        client = boto3.client('rekognition')

        response, eyes_open, tag = check('test_eyes_closed_52.7_99.9.jpg', client)
        self.assertFalse(eyes_open)
        self.assertEqual(tag, 'eyes_closed_52.7_99.9')

        response, eyes_open, tag = check('test_eyes_open_97.2_100.0.jpg', client)
        self.assertTrue(eyes_open)
        self.assertEqual(tag, 'eyes_open_97.2_100.0')

        response, eyes_open, tag = check('test_eyes_probably_closed_64.6_100.0.jpg', client)
        self.assertFalse(eyes_open)
        self.assertEqual(tag, 'eyes_probably_closed_64.6_100.0')

        response, eyes_open, tag = check('test_no_face_details.jpg', client)
        self.assertIsNone(eyes_open)
        self.assertEqual(tag, 'no_face_details')

        response, eyes_open, tag = check('test_jack_jack_and_elon.jpg', client)
        self.assertTrue(eyes_open, True)
        self.assertEqual(tag, 'eyes_open_96.9_96.6')


class AwakeTest_quick(unittest.TestCase):

    def test(self):
        client = boto3.client('rekognition')

        response, eyes_open, tag = check('test_no_face_details.jpg', client)
        self.assertIsNone(eyes_open)
        self.assertEqual(tag, 'no_face_details')


if __name__ == "__main__":

    continuous = False

    if len(sys.argv) >= 2 and sys.argv[1] == 'test':
            del sys.argv[1]
            sys.exit(unittest.main())

    if len(sys.argv) == 2:

        if sys.argv[1] == 'test':
            del sys.argv[1:]
            unittest.main()
            sys.exit(0)
        if sys.argv[1] == 'c':
            continuous = True
        else:
            image_file = sys.argv[1]
            client = boto3.client('rekognition')
            response, eyes_open, tag = check(image_file, client, show=True)
            pprint.pprint(response)
            print('\n')
            print('Eyes open:', eyes_open)
            print('tag:', tag)
            sys.exit(0)

    client = boto3.client('rekognition')
    os.chdir(PHOTO_DIR)

    while True:

        timestamp = time.localtime()

        if continuous or (timestamp.tm_hour >= 5 and timestamp.tm_hour <= 6):

            last_image = get_image_filename()
            last_image = os.path.join(PHOTO_DIR, last_image)

            print('Processing photo', last_image)

            response, eyes_open, tag = check(last_image, client, show=True)

            if eyes_open is True:
                action(ON)
            else:
                action(OFF)

            #copy_file(last_image, tag)

            localtime = time.localtime()
            timestamp = time.strftime("%I:%M:%S %p", localtime)

            print(timestamp + ': ' + last_image + ': ' + tag)

            name, extension = os.path.basename(last_image).split('.')
            response['ImageAnnotated'] = name + '_' + tag + '.' + extension

            #pprint.pprint(response)
            #print('\n')

        else:

            print('Outside checking hours, now hour is', timestamp.tm_hour)

        print('Sleeping now', MINS_TO_SLEEP, 'minutes...')
        time.sleep(MINS_TO_SLEEP * 60)
