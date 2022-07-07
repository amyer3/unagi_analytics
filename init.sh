#!/bin/zsh
rm -rf venv/
python3 -m venv ./venv
source . ./venv/bin/activate && pip install -r src/requirements.txt
pip install flask psycopg2-binary snowflake-connector-python uwsgi