pip3 install --user -r requirements.txt 
...
  The script gunicorn is installed in '/home/pi/.local/bin' which is not on PATH.
  Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
Successfully installed gunicorn-20.0.4

gunicorn -b :8007 -w 2 pi_ws:app

/home/pi/.local/bin/gunicorn -b :8007 -w 2 pi_ws:app

Use --preload to get more info in case of worker failure to boot.
