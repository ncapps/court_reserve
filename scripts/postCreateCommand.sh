#!/usr/bin/env bash

cat << 'EOF' >> /home/vscode/.zshrc
pipenv shell
pipenv install --dev
autoload bashcompinit && bashcompinit
autoload -Uz compinit && compinit
compinit
complete -C '/usr/local/bin/aws_completer' aws
EOF
