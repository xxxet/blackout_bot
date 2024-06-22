#!/usr/bin/env bash
python3 -m venv venv-d
source ./venv/bin/activate
pip install -r requirements.txt -U
python3 run_bot.py --group "$1" --token "$2"
