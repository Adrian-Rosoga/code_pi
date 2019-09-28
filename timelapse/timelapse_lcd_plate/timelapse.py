#!/usr/bin/python

#
# Timelapse Controller
# Adrian Rosoga, 18 Dec 2013
#

from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from subprocess import * 
from time import sleep, strftime
from datetime import datetime
import sys, os, threading, signal
import RPi.GPIO as GPIO

lcd = Adafruit_CharLCDPlate()
lcd.begin(16,1)

#TIMELAPSE_ROOT_DIR = '/media/WD_Blue/timelapse_out'
TIMELAPSE_ROOT_DIR = '/media/usb/timelapse_out'

TIMELAPSE_RUN_HOURS = 168
TIMELAPSE_SECS_BETWEEN_PICTURES = 10
#TIMELAPSE_DIMENSIONS=' -w 1440 -h 1080 '
TIMELAPSE_DIMENSIONS=''
PROGRESS_THREAD_REPORT_INTERVAL = 30

info_cmd = "ip addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1"

def handler(signum = None, frame = None):
    stop_progress_thread()
    action_stop_timelapse()
    lcd.clear()
    lcd.backlight(lcd.OFF)
    lcd.message(str(signum) + ' received\nExiting')
    sys.exit(0)

def stop_progress_thread():
    global thread_stop
    thread_stop = True

def run_cmd(cmd):
        p = Popen(cmd, shell=True, stdout=PIPE)
        output = p.communicate()[0]
        return output

def get_dir():
    ''' Directories are 00, 01, 02, etc '''
    dir = run_cmd('ls -r1 ' + TIMELAPSE_ROOT_DIR + ' | head -1')

    if dir == '':
        dir = 0
    else:
        dir = int(dir) + 1

    if dir < 10:
        dir = '0' + str(dir)
    else:
        dir = str(dir)
    dir =  TIMELAPSE_ROOT_DIR + '/' + dir   

    rc = os.system('mkdir ' + dir)
    if rc != 0:
        print 'Error: Cannot create directory ' + dir
        stop_progress_thread()
        lcd.clear()
        lcd.backlight(lcd.RED)
        lcd.message('ERROR: mkdir')

    os.system('chmod ago+rw ' + dir)
    return dir

class ProgressThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global dir, thread_show_progress, thread_stop

        number_frames = 0
        rotating = r'-\|/'
        rotating_count = 0
        while True:
            if thread_stop == True:
                print 'ProgressThread finished.'
                return

            raspistill_instances = \
                run_cmd('ps -eaf | grep raspistill | grep -v grep | wc -l')[:-1]
            msg_part = os.path.basename(dir) + ": " + str(number_frames) + ' : '

            if raspistill_instances == '0' and number_frames != 0:
                lcd.message('                ')
                lcd.home()
                lcd.message(msg_part + 'Done')
            elif thread_show_progress == True:
                number_frames = run_cmd('ls -1 ' + dir + ' | wc -l')[:-1]
                lcd.message('                ')
                lcd.home()
                lcd.message(msg_part + rotating[rotating_count])
                rotating_count = (rotating_count + 1) % 4
            sleep(PROGRESS_THREAD_REPORT_INTERVAL)

def action_halt():
    thread_show_progress = False
    stop_progress_thread()
    lcd.clear()
    lcd.backlight(lcd.RED)
    lcd.message('Halting')
    os.system('sudo shutdown -h now')

def action_reboot():
    thread_show_progress = False
    stop_progress_thread()
    lcd.clear()
    lcd.backlight(lcd.RED)
    lcd.message('Rebooting')
    os.system('sudo reboot')

def action_start_timelapse():
    global dir, thread_show_progress, thread_stop
    dir = get_dir()
    print 'Capture directory: ' + dir
    action_stop_timelapse()
    thread_show_progress = True 
    lcd.clear()
    # E.g.: 
    cmd = 'raspistill -n -q 100 -o ' + dir + '/z%05d.jpg -t ' + \
          str(TIMELAPSE_RUN_HOURS * 3600 * 1000) + \
          TIMELAPSE_DIMENSIONS + \
          ' -tl ' + str(TIMELAPSE_SECS_BETWEEN_PICTURES * 1000) + ' &'
    #print cmd
    rc = os.system(cmd)
    if rc != 0:
        lcd.backlight(lcd.RED)
        lcd.message('Error starting')
    else:
        lcd.backlight(lcd.GREEN)
        lcd.message('Capture started!')

def action_stop_timelapse():
    global dir, thread_show_progress, thread_stop
    thread_show_progress = False
    os.system('pkill raspistill')
    lcd.clear()
    lcd.backlight(lcd.GREEN)
    lcd.message('Capture stopped')

def action_info():
    lcd.clear()
    ipaddr = run_cmd(info_cmd)
    #lcd.message(datetime.now().strftime('%b %d  %H:%M:%S\n'))
    lcd.message('IP %s' % ( ipaddr ) )

menu_item = 0
menu = (('==> Info', action_info),
        ('==> Halt', action_halt),
        ('==> Reboot', action_reboot),
        ('==> Stop', action_stop_timelapse),
        ('==> Start', action_start_timelapse))

def button2cmd(button):
    global menu_item, menu
    #print 'Button = ' + str(button)
    if button == lcd.UP:
        menu_item = (menu_item + 1) % len(menu)
        #print menu_item
        lcd.message('\n                              ')
        lcd.message('\n' + menu[menu_item][0])
    if button == lcd.DOWN:
        menu_item -= 1
        if menu_item == -1: menu_item = len(menu) - 1
        lcd.message('\n                              ')
        lcd.message('\n' + menu[menu_item][0])
    if button == lcd.SELECT:
        menu[menu_item][1]()
    if button == lcd.RIGHT:
        lcd.backlight(lcd.GREEN)
    if button == lcd.LEFT:
        lcd.backlight(lcd.OFF)
        GPIO.output(CAMLED, False)

### Main ##############################################################

# Use GPIO numbering
GPIO.setmode(GPIO.BCM)
 
# Set GPIO for camera LED
CAMLED = 5
 
# Set GPIO to output
GPIO.setup(CAMLED, GPIO.OUT, initial=False)

for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]:
    signal.signal(sig, handler)

lcd.clear()
lcd.backlight(lcd.GREEN)
lcd.message("Timelapse\nRaspberry Pi")
sleep(5)
lcd.backlight(lcd.OFF)

# Start with the Info menu
menu[menu_item][1]()

dir = ''
thread_stop = False
thread_show_progress = False
progressThread = ProgressThread()
progressThread.start()

try:
    previous_button = -1
    while True:
        sleep(0.5)
        for button in (lcd.LEFT, lcd.UP, lcd.DOWN, lcd.RIGHT, lcd.SELECT):
            if lcd.buttonPressed(button):
                if button is not previous_button:
                    button2cmd(button)
                    #previous_button = button
                break
except KeyboardInterrupt:
    print 'Interrupt...'
    action_stop_timelapse()
    stop_progress_thread()
    #progressThread.join()
    print 'Exiting...'

