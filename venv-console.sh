#!/bin/bash
CURRENT_DIRNAME="$(dirname `readlink -f $0`)"

bash --init-file <(echo "source '${CURRENT_DIRNAME}/venv/bin/activate'")
