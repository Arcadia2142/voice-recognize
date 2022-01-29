#!/bin/bash
CURRENT_DIRNAME="$(dirname `readlink -f $0`)"

rm "${CURRENT_DIRNAME}/tmp/*"

source "${CURRENT_DIRNAME}/recognize/bin/activate"
python3 "${CURRENT_DIRNAME}/runner/runner.py" $@