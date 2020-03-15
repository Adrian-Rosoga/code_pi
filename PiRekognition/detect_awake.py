#!/usr/bin/env python

#
# Adrian Rosoga, 18 Sep 2019
#


import boto3
import sys
import time
import os
import pprint
import unittest
import io
import logging
import argparse
from PIL import Image, ImageDraw, ExifTags, ImageColor, ImageFont
from PIL.ExifTags import TAGS

MINS_TO_SLEEP = 5
CONFIDENCE_THRESHOLD = 90.0
ON = True
OFF = False
PHOTO_DIR = '/tmp/timelapse'
IMAGE_DESTINATION_DIR = '/media/pi/PI_STICK/awake_detector/'
MIN_HOUR, MAX_HOUR = 5, 6


def get_exif(pil_image):
    exif_info = {}
    info = pil_image._getexif()
    for tag, value in list(info.items()):
        decoded = TAGS.get(tag, tag)
        exif_info[decoded] = value
    return exif_info


def to_yes_no(value):
    return 'YES' if value else 'NO'


def show_faces(response, stream, image_file, tag):

    image = Image.open(stream)

    image_width, image_height = image.size
    draw = ImageDraw.Draw(image)

    #  Find out available fonts with fc-list
    font = ImageFont.truetype("FreeSansBold.ttf", 32)

    exif_info = get_exif(image)
    # '2019:10:03 11:24:52'
    date_taken = str(exif_info['DateTime'])

    annotation = ''
    index = 1

    text_width, text_height = font.getsize(date_taken)
    draw.rectangle((0, 0, text_width, 40), fill='black')
    draw.text((0, 0), '*** PiRekognition *** ' + date_taken, fill='yellow', font=font)

    # Display bounding boxes for each detected face
    for faceDetail in response['FaceDetails']:
        # print('The detected face is between ' + str(faceDetail['AgeRange']['Low'])
        #      + ' and ' + str(faceDetail['AgeRange']['High']) + ' years old')

        box = faceDetail['BoundingBox']
        left = image_width * box['Left']
        top = image_height * box['Top']
        width = image_width * box['Width']
        height = image_height * box['Height']

        points = (
            (left, top),
            (left + width, top),
            (left + width, top + height),
            (left, top + height),
            (left, top)
        )
        draw.line(points, fill='yellow', width=2)

        annotation = 'Face #' + str(index) + ': EyesOpen=' + to_yes_no(faceDetail['EyesOpen']['Value']) + \
                     ' - EyesOpenConfidence=' + '{:.1f}'.format(faceDetail['EyesOpen']['Confidence']) + '% ' + \
                     '(Threshold=' + '{:.1f}'.format(CONFIDENCE_THRESHOLD) + ') - ' +\
                     'Confidence=' + '{:.1f}'.format(faceDetail['Confidence']) + '%'

        text_width, text_height = font.getsize(annotation)
        draw.rectangle((0, 40 * index, text_width, 40 * (index + 1)), fill='black')
        draw.text((0, 40 * index), annotation, fill='yellow', font=font)

        draw.text((left, top), str(index), fill='yellow', font=font)

        index = index + 1

    if index == 1:
        text_width, text_height = font.getsize(annotation)
        draw.rectangle((0, 40 * index, text_width, 40 * (index + 1)), fill='black')
        annotation = 'No face details'
        draw.text((0, 40 * index), annotation, fill='yellow', font=font)

    '''
    Debugging only
    None of the 3 viewers listed /usr/lib/python2.7/dist-packages/PIL/c
    was available on the distribution.
    A few options are available:
    # Hack the above ImageShow.py and add an existing viewer - e.g. gpicview
    # Install display, xv, eog. ImageMagick might make xv available - TBC.
    '''
    # image.show()

    name, extension = os.path.basename(image_file).split('.')

    # From '2019:10:03 11:24:52' to Dropbox-like format '2019-10-03 11.24.52'
    date_taken = date_taken.replace(':', '-', 2)
    date_taken = date_taken.replace(':', '.')

    annotated_file = date_taken + ' ' + tag + '.' + extension

    image.save(os.path.join(IMAGE_DESTINATION_DIR, annotated_file))


def get_image_filename():

    if False:
        # Filter for directory names starting with '201'
        try:
            last_dir_name = max([dir for dir in os.listdir('.') if dir.find('2020') != -1])
            if last_dir_name is None:
                logging.info('No directory ending in 2019')
                return None
            if len(last_dir_name) == 0:
                logging.info('No directory ending in 2019')
                return None
        except:
            logging.info('exception thrown - no directory starting with 201')
            return None
    else:
        last_dir_name = '.'

    last_dir_path = os.path.join('.', last_dir_name)
    if not os.path.isdir(last_dir_path):
        logging.info('path is not a directory')
        logging.info('last_dir_path = %s', last_dir_path)
        return None

    files = os.listdir(last_dir_path)

    files.sort(key=lambda x: x)

    if len(files) == 0:
        logging.info('No files in directory')
        return None

    # Last image is the one we are looking for
    last_image = files[-1]

    # If it ends in '~' it's a temporary image file, try the previous one if it exists
    if last_image.find('~') == -1:
        return os.path.join(last_dir_path, last_image)
    else:
        if len(files) < 2:
            logging.info('Less than 2 image files')
            return None
        last_image = files[-2]
        return os.path.join(last_dir_path, last_image)


def copy_file(image_file, tag):
    try:
        name, extension = os.path.basename(image_file).split('.')
        cmd = 'cp ' + image_file + ' ' + IMAGE_DESTINATION_DIR + name + '_' + tag + '.' + extension
        os.system(cmd)
    except IOError as e:
        logging.error("Unable to copy file. %s" % e)
    except:
        logging.error("Unexpected error:", sys.exc_info())


def action(on_off):
    if on_off == ON:
        os.system('/home/pi/code_pi/PiRekognition/hs100_lamp_on.sh')
    else:
        os.system('/home/pi/code_pi/PiRekognition/hs100_lamp_off.sh')


def check(image_file, client, show=False):

    eyes_open = None
    tag = ''

    with open(image_file, 'rb') as image:
        response = client.detect_faces(Image={'Bytes': image.read()}, Attributes=['ALL'])

        if response['FaceDetails'] is not None and len(response['FaceDetails']) == 1:

            for label in response['FaceDetails']:

                if label['EyesOpen']['Value']:
                    if label['EyesOpen']['Confidence'] >= CONFIDENCE_THRESHOLD:
                        eyes_open, tag = True, 'eyes_open'
                    else:
                        eyes_open, tag = False, 'eyes_probably_closed'
                else:
                    eyes_open, tag = False, 'eyes_closed'

                tag = tag + '_' + '{:.1f}'.format(label['EyesOpen']['Confidence']) + '_' +\
                            '{:.1f}'.format(label['Confidence'])

        elif response['FaceDetails'] is not None and len(response['FaceDetails']) > 0:

            eyes_open, tag = False, 'more_than_one_face'

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


class AwakeTestQuick(unittest.TestCase):

    def test(self):
        client = boto3.client('rekognition')

        response, eyes_open, tag = check('test_no_face_details.jpg', client)
        self.assertIsNone(eyes_open)
        self.assertEqual(tag, 'no_face_details')


def check_file(image_file, verbose=False):

    client = boto3.client('rekognition')
    response, eyes_open, tag = check(image_file, client, show=True)
    if verbose:
        pprint.pprint(response)
        print('\n')
    logging.info('Eyes open: %s', eyes_open)
    logging.info('tag: %s', tag)
    return 0


def check_continuously(verbose=False):

    client = boto3.client('rekognition')
    os.chdir(PHOTO_DIR)

    while True:

        timestamp = time.localtime()

        if args.force or (MIN_HOUR <= timestamp.tm_hour <= MAX_HOUR):

            last_image = get_image_filename()
            last_image = os.path.join(PHOTO_DIR, last_image)

            # logging.info('Processing image %s', last_image)

            # ADIRX: Refactor, extract loop in another method, try over the whole loop
            try:
                response, eyes_open, tag = check(last_image, client, show=True)
            except botocore.exceptions.EndpointConnectionError as e:
                logging.error("%s" % e)
                time.sleep(MINS_TO_SLEEP * 60)
                continue
            except:
                logging.info("Unexpected error:", sys.exc_info())
                time.sleep(MINS_TO_SLEEP * 60)
                continue

            if eyes_open is True:
                action(ON)
            else:
                action(OFF)

            # copy_file(last_image, tag)

            signal = " |||||||||||||" if eyes_open else " ............."
            logging.info(os.path.basename(last_image) + ': ' + tag + signal)

            name, extension = os.path.basename(last_image).split('.')
            response['ImageAnnotated'] = name + '_' + tag + '.' + extension

            if verbose:
                pprint.pprint(response)
                print('\n')

        else:

            logging.info("Outside detection interval %s <= hour <= %s", MIN_HOUR, MAX_HOUR)

        # logging.info('Sleeping now %s minutes...', MINS_TO_SLEEP)
        time.sleep(MINS_TO_SLEEP * 60)


if __name__ == "__main__":

    logging.basicConfig(format="%(asctime)-15s %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    parser = argparse.ArgumentParser(description='Detect Awake')
    parser.add_argument('-t', '--test', help='run unittests', action="store_true")
    parser.add_argument('-f', '--file', help='analyze image file')
    parser.add_argument('-x', '--force', help='run outside the time window', action="store_true")
    parser.add_argument('-v', '--verbose', help='verbose', action="store_true")
    args = parser.parse_args()

    if args.test:
        del sys.argv[1]
        sys.exit(unittest.main())
    elif args.file is not None:
        image_file = args.file
        sys.exit(check_file(image_file, verbose=args.verbose))
    else:
        check_continuously(verbose=args.verbose)
