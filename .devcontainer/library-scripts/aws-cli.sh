#!/usr/bin/env bash
# Syntax: ./aws-cli.sh [non-root user]

USERNAME=${1:-"automatic"}

set -e

if [ "$(id -u)" -ne 0 ]; then
    echo -e 'Script must be run as root. Use sudo, su, or add "USER root" to your Dockerfile before running this script.'
    exit 1
fi

# Determine the appropriate non-root user
if [ "${USERNAME}" = "auto" ] || [ "${USERNAME}" = "automatic" ]; then
    USERNAME=""
    POSSIBLE_USERS=("vscode" "node" "codespace" "$(awk -v val=1000 -F ":" '$3==val{print $1}' /etc/passwd)")
    for CURRENT_USER in ${POSSIBLE_USERS[@]}; do
        if id -u ${CURRENT_USER} > /dev/null 2>&1; then
            USERNAME=${CURRENT_USER}
            break
        fi
    done
    if [ "${USERNAME}" = "" ]; then
        USERNAME=root
    fi
elif [ "${USERNAME}" = "none" ] || ! id -u ${USERNAME} > /dev/null 2>&1; then
    USERNAME=root
fi

# Download and install AWS CLI
mkdir -p /tmp/aws-cli
cd /tmp/aws-cli
curl -sSl -o /tmp/aws-cli/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"
unzip awscliv2.zip
./aws/install
rm -rf /tmp/aws-cli

# Download and install AWS SAM CLI
AWS_SAM_PATH=/tmp/aws-sam-cli
mkdir -p $AWS_SAM_PATH
cd $AWS_SAM_PATH
curl -sSL -o $AWS_SAM_PATH/awssamcli.zip "https://github.com/aws/aws-sam-cli/releases/download/v1.23.0/aws-sam-cli-linux-x86_64.zip"
unzip awssamcli.zip -d sam-installation
./sam-installation/install
rm -rf $AWS_SAM_PATH
