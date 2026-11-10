#!/bin/bash

cd "$(dirname "$0")"

export PYTHONPATH="$PWD/backend:$PYTHONPATH"

python3 cli.py "$@"
