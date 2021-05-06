#!/usr/bin/env bash

WORKSPACE="/workspaces/court_reserve"

if [[ ! -d $WORKSPACE/venv ]]; then
    python -m venv $WORKSPACE/venv
    source $WORKSPACE/venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r $WORKSPACE/requirements.txt \
        -r $WORKSPACE/court_reserve/requirements.txt
else
    source $WORKSPACE/venv/bin/activate
fi
