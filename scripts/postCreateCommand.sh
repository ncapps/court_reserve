#!/usr/bin/env bash

WORKSPACE = /workspaces/court_reserve

python -m venv $WORKSPACE/venv
source $WORKSPACE/venv/bin/activate
python -m pip install --upgrade pip
pip install -r $WORKSPACE/requirements-dev.txt \
    -r $WORKSPACE/court_reserve/requirements.txt

cat << 'EOF' >> /home/vscode/.zshrc
source $(WORKSPACE)/venv/bin/activate

autoload bashcompinit && bashcompinit
autoload -Uz compinit && compinit
compinit
complete -C '/usr/local/bin/aws_completer' aws
EOF
