#!/bin/bash

set -e

sudo cp /home/pi/code_pi/iot/climate_DS18B20.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl start climate_DS18B20.service

# Check status
sudo systemctl status climate_DS18B20.service

echo "All seems ok, enabling the service now..."

sudo systemctl enable climate_DS18B20.service

echo "Done!"
