#!/bin/bash

set -e

sudo cp /home/pi/code_pi/iot/climate.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl start climate.service

# Check status
sudo systemctl status climate.service

echo "All seems ok, enabling the service now..."

sudo systemctl enable climate.service

echo "Done!"