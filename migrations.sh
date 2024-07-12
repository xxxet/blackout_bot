#!/usr/bin/env bash
python3 -m venv venv-d
source ./venv-d/bin/activate
pip install -r requirements.txt -U
alembic upgrade head
