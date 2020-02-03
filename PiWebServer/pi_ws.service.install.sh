#!/bin/bash

set -e

sudo cp /home/pi/code_pi/PiWebServer/pi_ws.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl start pi_ws.service

# Check status
sudo systemctl status pi_ws.service

echo "All seems ok, enabling the service now..."

sudo systemctl enable tl_ws.service

echo "Done!"