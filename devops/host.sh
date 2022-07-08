#!/bin/bash

echo "stoping Nginx"
systemctl stop nginx

echo "stoping pyorm service"
systemctl stop pyorm

git stash && git pull origin

echo "stopping venv, just in case"
deactivate
#sudo apt-get install -y libtiff5-dev libjpeg8-dev zlib1g-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk

cd /pyorm/ || exit
pwd
echo "Removing venv, replacing with fresh copy"
rm -rf venv/
python3 -m venv ./venv
echo "setting VENV permissions"
chmod a+rwx -R ./venv/
echo "setting LOG permissions"
chmod a+rwx -R /var/log/wsgi/
chown -R root:www-data /pyorm/*
usermod -aG www-data root
echo "Activating VENV"
source venv/bin/activate && pip install -r src/requirements.txt
pip install flask psycopg2-binary snowflake-connector-python uwsgi
echo "Restarting Services"
systemctl start pyorm
systemctl start nginx
systemctl status pyorm
