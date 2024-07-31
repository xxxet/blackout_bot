#!/usr/bin/env bash
python3 -m venv venv1
source ./venv1/bin/activate
pip install -r requirements.txt -U
alembic upgrade head
