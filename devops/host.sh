#!/bin/bash

systemctl stop nginx
systemctl stop pyorm
cd /pyorm/ || exit
rm -rf ./venv/
python3 -m venv ./venv
chmod a+rwx -R ./venv/
chmod a+rwx -R /var/log/wsgi/
chown -R root:www-data /pyorm/*
usermod -aG www-data root
source ./venv/bin/activate
pip install -r src/requirements.txt
cd src/ || exit
systemctl start pyorm
systemctl start nginx

