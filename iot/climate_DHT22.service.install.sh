#!/bin/bash

set -e

sudo cp /home/pi/code_pi/iot/climate_DHT22.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl start climate_DHT22.service

# Check status
sudo systemctl status climate_DHT22.service

echo "All seems ok, enabling the service now..."

sudo systemctl enable climate_DHT22.service

echo "Done!"