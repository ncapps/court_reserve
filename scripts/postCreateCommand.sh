#!/usr/bin/env bash

cat << 'EOF' >> /home/vscode/.zshrc
source /workspaces/court_scheduler/scripts/venv.sh
autoload bashcompinit && bashcompinit
autoload -Uz compinit && compinit
compinit
complete -C '/usr/local/bin/aws_completer' aws
EOF
