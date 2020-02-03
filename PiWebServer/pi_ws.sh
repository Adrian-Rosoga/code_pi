#!/bin/bash

/home/pi/.local/bin/gunicorn -b :8007 -w 2 pi_ws:app
