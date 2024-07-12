#!/usr/bin/env bash
docker build . -t blackout
docker run --rm -v $(pwd)/:/root/projects/blackout  blackout ./entrypoint.sh "$1"
