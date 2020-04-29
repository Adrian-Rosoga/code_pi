#!/usr/bin/env python3


import os
import sys
import time
import datetime
import requests
import argparse
import smtplib
import ssl
import threading
from collections import namedtuple


#
# Adrian Rosoga, 18 Apr 2020
#


URLs = ['http://tides-env.m5xmmhjzmw.eu-west-2.elasticbeanstalk.com',
        'https://arosoga.netlify.app',
        'https://arosoga.netlify.com',
        'https://adrian-rosoga.github.io',
        'https://cb91b3bd.eu.ngrok.io/tl',
        'https://d2eafeb7.eu.ngrok.io/tl'
        ]

TIMEOUT_SECS = 10

#URLs = ['http://tides-env.m5xmmhjzmw.eu-west-2.elasticbeanstalk.comX']


URLData = namedtuple('URLData', 'code exception_name data_length time_ms')


class URLsStatus:

    def __init__(self):
        self.status = dict()
        self._lock = threading.Lock()

    def update(self, url, code, exception_name, data_length, time_ms):

        with self._lock:
            self.status[url] = URLData(code, exception_name, data_length, time_ms)

    def values(self):

        for url, data in self.status.items():
            yield url, data


def check_web_site(url: str, urls_status):

    exception_name = None

    ts = time.time()

    try:
        page = requests.get(url, timeout=TIMEOUT_SECS)
        code = page.status_code
    except requests.exceptions.RequestException as ex:
        code = None
        exception_name = ex.__class__.__name__

    te = time.time()

    time_ms = (te - ts) * 1000
    
    data_length = len(page.text) if code == requests.codes.ok else 0

    urls_status.update(url, code, exception_name, data_length, time_ms)

    return code, data_length


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


def main():

    url_status = URLsStatus()

    ts = time.time()

    threads = list()
    for url in URLs:

        print(f'Checking {url}...')
        thread = threading.Thread(target=check_web_site, args=(url, url_status))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    te = time.time()

    time_ms = (te - ts) * 1000

    status_codes = []
    messages = []
    for url, url_data in url_status.values():

        status_code, exception_name, data_length, time_ms = url_data

        if status_code != requests.codes.ok:
            status_codes.append(False)
            msg = f'{url} DOWN! Code {status_code}. Exception {exception_name}. Took {time_ms:.2f} ms'
        else:
            status_codes.append(True)
            msg = f'{url} UP! Code {status_code}. Data length = {data_length}. Took {time_ms:.2f} ms'

        print(msg)
        messages.append(msg)

    messages.append("")
    msg = f"All checks took {time_ms:.2f} ms"
    print(msg)
    messages.append(msg)

    if all(status_codes):
        subject = f'WebChecks OK: All {len(status_codes)} sites are UP!'
    else:
        subject = f'WebChecks FAIL for at least one site!'

    print(f'Sending email...')
    send_email(subject, "\n".join(messages))


if __name__ == '__main__':

    main()
