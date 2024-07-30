#!/usr/bin/env bash
docker build . -t blackout
docker run --rm -p 8080:8080 -v $(pwd)/:/root/projects/blackout  blackout ./entrypoint.sh "$1"
