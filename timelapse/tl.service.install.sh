#!/bin/bash

set -e

sudo cp /home/pi/code_pi/timelapse/tl.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl start tl.service

# Check status
sudo systemctl status tl.service

echo "All seems ok, enabling the service now..."

sudo systemctl enable tl.service

echo "Done!"