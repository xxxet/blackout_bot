#!/usr/bin/env bash
python3 -m venv venv1
source ./venv1/bin/activate
pip install -r requirements.txt -U
alembic upgrade head
python3 run_flask.py --port "$1" &
python3 run_bot.py --token "$2"
