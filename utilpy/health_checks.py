#!/usr/bin/env python3

import os
import re
import sys
import time
import requests
import smtplib
import ssl
import threading
import pickle
import datetime
import yaml
from dataclasses import dataclass
from collections import namedtuple
from http import HTTPStatus
from util import cmd_output
from Adafruit_IO import Client

#
# Adrian Rosoga, 18 Apr 2020
#

ADAFRUIT_IO_KEY = os.environ['ADAFRUIT_IO_KEY']
ADAFRUIT_IO_USERNAME = os.environ['ADAFRUIT_IO_USERNAME']


@dataclass
class Config:
    URLs = None
    TIMEOUT_SECS = 30
    STATUS_STORE_FILE = "/home/adi/code_local/health_check_status.dat"
    NUMBER_BACKLOG_CHECKS = 24
    MIN_DOWNLOAD_THRESHOLD_MBPS = 30
    MIN_UPLOAD_THRESHOLD_MBPS = 30


g_config = Config()

URLData = namedtuple('URLData', 'url code ex_type ex_value data_length time_ms')

SPEEDTEST_SERVERS = {"Trunk Networks - London (id = 12920)": 12920,
                     "Vox Telecom - London (id = 7437)": 7437,
                     "fdcservers.net - London (id = 6032)": 6032,
                     "Jump Networks Ltd - London (id = 24640)": 24640,
                     "GTT.net - London (id = 24383)": 24383
                     }


def HTTP_info_from_code(code: int):
    for status in HTTPStatus:
        if status.value == code:
            return status.name, status.phrase, status.description

    return (None,) * 3


class ManagedTimerSeconds:

    def __init__(self, duration_out):
        self.time_start = None
        self.duration_out = duration_out

    def __enter__(self):
        self.time_start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_out *= 0
        self.duration_out.append((time.time() - self.time_start))


class StatusStore:

    def __init__(self):
        self.statuses = []

    def add(self, status):
        self.statuses.append(status)


def TimeFn(elem):
    return float(elem.time_ms)


class URLsStatus:

    def __init__(self):
        self.status = []
        self._lock = threading.Lock()

    def update(self, url, code, ex_type, ex_value, data_length, time_ms):
        with self._lock:
            self.status.append(URLData(url, code, ex_type, ex_value, data_length, time_ms))

    def values(self):
        for url_status in self.status:
            yield url_status

    def values_sorted_by_time(self):
        for url_status in sorted(self.status, key=TimeFn):
            yield url_status


def check_web_site(url: str, urls_status):
    ex_type = None
    ex_value = None

    elapsed_secs = []
    with ManagedTimerSeconds(elapsed_secs):
        try:
            page = requests.get(url, timeout=g_config.TIMEOUT_SECS)
            code = page.status_code
        except requests.exceptions.RequestException:
            code = None
            ex_type, ex_value, _ = sys.exc_info()

    time_ms = elapsed_secs[0] * 1000

    data_length = len(page.text) if code == requests.codes.OK else 0

    urls_status.update(url, code, ex_type, ex_value, data_length, time_ms)


def send_email(subject, message):
    port = os.environ['SMTP_PORT']
    smtp_server = os.environ['SMTP_SERVER']
    sender_email = os.environ['SMTP_SENDER_EMAIL']
    password = os.environ['SMTP_PASSWORD']

    receiver_email = "arosoga@yahoo.com"

    message = f'''Subject: {subject}

    {message}'''

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


def build_message(values, messages=None, status_codes=None):
    for status in values:

        url, status_code, ex_type, ex_value, data_length, time_ms = status

        if status_code == requests.codes.ok:
            if status_codes is not None:
                status_codes.append(True)
            msg = f'{url} UP! Code {status_code}. Data length = {data_length}. Took {time_ms:.2f} ms'
        elif status_code == requests.codes.unauthorized:
            if status_codes is not None:
                status_codes.append(True)
            msg = f'{url} UP (Unauthorized)! Code {status_code}. Data length = {data_length}. Took {time_ms:.2f} ms'
        else:
            if status_codes is not None:
                status_codes.append(False)
            HTTPName, HTTPPhrase, HTTPDescription = HTTP_info_from_code(status_code)
            msg = f'{url} DOWN! Code {status_code}. Name \'{HTTPName}\'. Phrase \'{HTTPPhrase}\'. Description \'{HTTPDescription}\'. Ex_type {ex_type}. Ex_value \'{ex_value}\'. Took {time_ms:.2f} ms'



        if messages is None:
            print(msg)
        if messages is not None:
            messages.append(msg)


def speedtest_result(server_id=None):
    cmd = "/usr/bin/speedtest --progress=no"

    if server_id is not None:
        cmd = cmd + f" --server-id={server_id}"

    # print(f"cmd={cmd}")

    return cmd_output(cmd.split())


def parse_speedtest_report(internet_check_report):
    """ Parse the Speedtest report """

    match = re.search(r'Download:\s+(\d*\.*\d*)\s+Mbps', internet_check_report)
    download_mbps = float(match.group(1)) if match else 0

    match = re.search(r'Upload:\s+(\d*\.*\d*)\s+Mbps', internet_check_report)
    upload_mbps = float(match.group(1)) if match else 0

    print(f'{download_mbps} Mbps download - {upload_mbps} Mbps upload')

    return download_mbps, upload_mbps


def send_speedtest_report(download_mbps, upload_mbps):
    """ Report internet speed to Adafruit IO """

    aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

    feed_internet_download_name = "internet-download"
    feed_internet_upload_name = "internet-upload"

    feed_internet_download = aio.feeds(feed_internet_download_name)
    feed_internet_upload = aio.feeds(feed_internet_upload_name)

    aio.send(feed_internet_download.key, f'{download_mbps:.2f}')
    aio.send(feed_internet_upload.key, f'{upload_mbps:.2f}')


def internet_speed_check():
    """ Run Internet speed check """

    print("\nRunning Speedtest(s)...")

    # Turned out that in practice the speed check is done against a chosen station and not the desired one. TBC.
    # STATIONS = [None, 24383, 12920, 7437, 6032]
    STATIONS = []
    final_internet_check_report = ''

    # for station_id in STATIONS or [None]:
    station_id = None
    try_number = 0
    MAX_TRIES = 3
    download_mbps = 0
    upload_mbps = 0

    while try_number != MAX_TRIES:

        try_number += 1

        elapsed_secs = []
        with ManagedTimerSeconds(elapsed_secs):
            internet_check_report = speedtest_result(station_id)

        time_ms = elapsed_secs[0] * 1000

        print(
            f"Running Speedtest attempt #{try_number}/{MAX_TRIES} for station {station_id} took {time_ms:.2f} ms. Results:\n{internet_check_report}")

        final_internet_check_report += internet_check_report

        # Report the download and upload speeds
        try:
            download_mbps, upload_mbps = parse_speedtest_report(internet_check_report)

            if download_mbps > 0 and upload_mbps > 0:
                send_speedtest_report(download_mbps, upload_mbps)
                break
            elif try_number == 1:
                final_internet_check_report += '\n\nDownload or upload FAILED, trying again\n\n'
                continue
            else:
                send_speedtest_report(download_mbps, upload_mbps)
                break
        except:
            pass

    if download_mbps < g_config.MIN_DOWNLOAD_THRESHOLD_MBPS or upload_mbps < g_config.MIN_UPLOAD_THRESHOLD_MBPS:
        email_subject = "Warning: Slow Internet Upload or Download"
        email_content = f'\nDownload speed is {download_mbps} mbps and threshold is {g_config.MIN_DOWNLOAD_THRESHOLD_MBPS} mbps\n'
        email_content += f'Upload speed is {upload_mbps} mbps and threshold is {g_config.MIN_UPLOAD_THRESHOLD_MBPS} mbps\n'
        send_email(email_subject, email_content)

    return final_internet_check_report


SAMPLE_REPORT = """
   Speedtest by Ookla

     Server: fdcservers.net - London (id = 6032)
        ISP: Hyperoptic Ltd
    Latency:     2.28 ms   (0.35 ms jitter)
   Download:    0.01 Mbps (data used: 58.7 MB)                               
     Upload:    65. Mbps (data used: 66.4 MB)                               
Packet Loss: Not available.
 Result URL: https://www.speedtest.net/result/c/ed9deb63-3a65-4a13-918b-2d4f9696cc2e
"""


def main():
    global g_config

    # Test parsing
    if False:
        parse_speedtest_report(SAMPLE_REPORT)
        return

    script_path = __file__.rsplit('/', 1)[0]

    with open(script_path + '/health_checks.yaml') as config_file:
        data = yaml.full_load(config_file)

    g_config.URLs = data['URLs']
    print(g_config.URLs)
    g_config.TIMEOUT_SECS = data['TIMEOUT_SECS']
    g_config.STATUS_STORE_FILE = data['STATUS_STORE_FILE']
    g_config.NUMBER_BACKLOG_CHECKS = data['NUMBER_BACKLOG_CHECKS']
    g_config.MIN_DOWNLOAD_THRESHOLD_MBPS = data['MIN_DOWNLOAD_THRESHOLD_MBPS']
    g_config.MIN_UPLOAD_THRESHOLD_MBPS = data['MIN_UPLOAD_THRESHOLD_MBPS']

    messages = ["\nHealth chech performed at " + str(datetime.datetime.now())]

    url_status = URLsStatus()

    elapsed_secs = []
    with ManagedTimerSeconds(elapsed_secs):

        threads = []
        for url in g_config.URLs:
            print(f'Checking {url}...')
            thread = threading.Thread(target=check_web_site, args=(url, url_status))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    time_ms = elapsed_secs[0] * 1000

    status_codes = []

    build_message(url_status.values(), messages=None, status_codes=status_codes)

    messages.append("\nOrdered by response time:")

    # Almost the same but sort by time
    build_message(url_status.values_sorted_by_time(), messages, status_codes=None)

    msg = f"\nRunning all connectivity checks took {time_ms:.2f} ms"
    print(msg)
    messages.append(msg)

    try:
        with open(g_config.STATUS_STORE_FILE, "rb") as fd:
            status_store = pickle.load(fd)
    except:
        status_store = StatusStore()

    current_email_body = "\n".join(messages)

    # Run Internet speed test
    internet_check_report = internet_speed_check()

    # Add the Internet speed report
    current_email_body += "\n\n" + internet_check_report

    # Send results
    if all(status_codes):

        status_store.add(current_email_body)

        # Send email right away if enough reports in the backlog, else just store the report
        if len(status_store.statuses) == g_config.NUMBER_BACKLOG_CHECKS:

            subject = f'WebChecks OK: All {len(status_codes)} sites are UP!'
            print(f'Sending email to inform of {len(status_store.statuses)} successful checks so far...')

            email_body = "\n\n======================\n".join(status_store.statuses)

            send_email(subject, email_body)

            # Clear the status store
            with open(g_config.STATUS_STORE_FILE, "wb") as fd:
                pickle.dump(StatusStore(), fd)

        else:

            with open(g_config.STATUS_STORE_FILE, "wb") as fd:
                pickle.dump(status_store, fd)

            print(f'Not sending email report, {len(status_store.statuses)} checks OK so far...')

    else:

        subject = f'WebChecks FAILED for at least one site!'

        email_body = "\n\n======================\n".join(status_store.statuses)

        email_body += "\n\n=== FAILED CHECKS ===================\n" + current_email_body

        print(f'Sending email to inform of failure...')
        send_email(subject, email_body)

        # Clear the status store
        with open(g_config.STATUS_STORE_FILE, "wb") as fd:
            pickle.dump(StatusStore(), fd)


if __name__ == '__main__':
    main()
