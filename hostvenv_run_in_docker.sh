#!/usr/bin/env bash
docker build . -t blackout-hostenv -f hostvenv.Dockerfile
docker run --rm -v $(pwd)/:/root/projects/blackout blackout-hostenv ./entrypoint.sh "$1" "$2" "$3" "$4"
