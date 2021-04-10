sudo cp /home/pi/code_pi/timelapse/tl_ws.service /etc/systemd/system

sudo systemctl daemon-reload

sudo systemctl start tl_ws.service

# Check status
sudo systemctl status tl_ws.service

echo "IF ALL OK ENABLE THE SERVICE WITH: sudo systemctl enable tl_ws.service"
