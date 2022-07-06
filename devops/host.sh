#!/bin/bash

systemctl stop nginx
systemctl stop pyorm
cd ~/pyorm/
python3 -m venv ./venv
chmod a+rwx -R ./venv/
source ./venv/bin/activate
pip install -r src/requirements.txt
cd src/
systemctl start pyorm
systemctl start nginx

