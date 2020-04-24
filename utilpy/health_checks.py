#!/usr/bin/env python3


import os
import sys
import datetime
import requests
import argparse
import smtplib
import ssl
import threading


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


#URLs = ['http://tides-env.m5xmmhjzmw.eu-west-2.elasticbeanstalk.comX']


class URLsStatus:

    def __init__(self):
        self.status = dict()
        self._lock = threading.Lock()

    def update(self, url, code, data_length):

        with self._lock:
            self.status[url] = [code, data_length]

    def values(self):

        for url, status in self.status.items():
            yield url, status[0], status[1]


def check_web_site(url: str, urls_status):

    print(f'Checking {url}...')

    try:
        page = requests.get(url)
        code = page.status_code
    except requests.exceptions.RequestException as exception:
        code = 777
    
    data_length = len(page.text) if code == requests.codes.ok else 0

    urls_status.update(url, code, data_length)

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

    threads = list()
    for url in URLs:

        thread = threading.Thread(target=check_web_site, args=(url, url_status))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    status_codes = []
    messages = []
    for url, status_code, data_length in url_status.values():

        if status_code != requests.codes.ok:
            status_codes.append(False)
            print(f'{url} is DOWN! Status code {status_code}!')
            messages.append(f'{url} is DOWN! Status code {status_code}!')
        else:
            status_codes.append(True)
            messages.append(f'{url} is UP! Status code {status_code}. Data length = {data_length}')

    if all(status_codes):
        subject = f'WebChecks OK: All {len(status_codes)} sites are UP!'
    else:
        subject = f'WebChecks FAIL for at least one site!'

    print(f'Sending email...')
    send_email(subject, "\n".join(messages))


if __name__ == '__main__':

    main()
