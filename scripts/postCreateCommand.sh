#!/bin/bash

echo "pipenv shell" >> /home/vscode/.zshrc
echo "pipenv install --dev" >> /home/vscode/.zshrc
echo "autoload bashcompinit && bashcompinit" >> /home/vscode/.zshrc
echo "autoload -Uz compinit && compinit" >> /home/vscode/.zshrc
echo "compinit" >> /home/vscode/.zshrc
echo "complete -C '/usr/local/bin/aws_completer' aws" >> /home/vscode/.zshrc
