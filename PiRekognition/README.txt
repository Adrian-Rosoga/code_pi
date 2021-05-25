To install boto3:
sudo apt install python3-boto3

Install via pip (pip3 install boto3) won't do, it errors: "AttributeError: module 'sys' has no attribute 'ba{e_prefix'"

Create and populate ~/.aws directory with config and credentials files from Dino D:\Root\Code\AWS

Ready to go:
python3 detect_awake.py

