#!/usr/bin/env bash

create_venv() {
  python3 -m venv venv-d
  source ./venv-d/bin/activate
  pip install -r requirements.txt -U
}

run_flask() {
  python3 run_flask.py --port "$1" &
}


if [ "$1" == "venv" ]; then
    create_venv
fi

if [ "$2" == "flask" ]; then
    run_flask "$3"
fi
./replicate.sh
alembic upgrade head
exec litestream replicate -exec "python3 run_bot.py --token '$4'"


