#!/usr/bin/env bash

WORKSPACE="/workspaces/court_scheduler"

if [[ ! -d $WORKSPACE/venv ]]; then
    python -m venv $WORKSPACE/venv
    source $WORKSPACE/venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r $WORKSPACE/requirements.txt \
        -r $WORKSPACE/requirements_dev.txt \
        -r $WORKSPACE/court_scheduler/court_reserve_lambda/requirements.txt
else
    source $WORKSPACE/venv/bin/activate
fi
