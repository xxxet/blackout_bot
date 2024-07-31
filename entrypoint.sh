#!/usr/bin/env bash
alembic upgrade head
python3 run_flask.py --port "$1" &
python3 run_bot.py --token "$2"
