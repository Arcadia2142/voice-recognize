#!/bin/bash
CURRENT_DIRNAME="$(dirname `readlink -f $0`)"

source "${CURRENT_DIRNAME}/venv/bin/activate"
python3 "${CURRENT_DIRNAME}/runner/runner.py" "$@"