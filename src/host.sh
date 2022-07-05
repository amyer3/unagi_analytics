#!/bin/bash

cd ~/pyorm/
source ./venv/bin/activate
pip install -r src/requirements.txt
cd src/
gunicorn --bind 0.0.0.0:5000 wsgi:app


