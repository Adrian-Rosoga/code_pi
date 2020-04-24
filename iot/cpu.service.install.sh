#!/bin/bash

set -e

sudo cp /home/pi/code_pi/iot/cpu.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl start cpu.service

# Check status
sudo systemctl status cpu.service

echo "All seems ok, enabling the service now..."

sudo systemctl enable cpu.service

echo "Done!"