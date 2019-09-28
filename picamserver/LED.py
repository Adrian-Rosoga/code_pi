#!/usr/bin/python

'''
Pi Camera LED off
Adrian Rosoga, 3 Mar 2014
'''

import RPi.GPIO as GPIO

CAMLED = 5  # GPIO for camera LED  

def main():
    ''' main '''

    # For "RuntimeWarning: This channel is already in use, continuing anyway."
    # use GPIO.setwarnings(False) to disable warning.
    GPIO.setwarnings(False)

    # Use GPIO numbering
    GPIO.setmode(GPIO.BCM)
     
    # Set GPIO to output
    GPIO.setup(CAMLED, GPIO.OUT, initial=False)

    # LED off
    GPIO.output(CAMLED, False)

if __name__ == "__main__":
    main()
