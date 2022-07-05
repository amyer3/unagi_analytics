#!/bin/bash

cd ~/pyorm/
source ./venv/bin/activate
pip install -r src/requirements.txt
gunicorn --bind 0.0.0.0:5000 wsgi:app


