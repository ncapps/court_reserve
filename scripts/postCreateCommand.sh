#!/usr/bin/env bash

pipenv install --dev

cat << 'EOF' >> /home/vscode/.zshrc
pipenv shell
autoload bashcompinit && bashcompinit
autoload -Uz compinit && compinit
compinit
complete -C '/usr/local/bin/aws_completer' aws
EOF
