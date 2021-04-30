# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
ARG VARIANT=3
FROM mcr.microsoft.com/vscode/devcontainers/python:${VARIANT}

# [Option] Install Node.js
ARG INSTALL_NODE="true"
ARG NODE_VERSION="lts/*"
RUN if [ "${INSTALL_NODE}" = "true" ]; then su vscode -c "source /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Setup docker from docker
COPY .devcontainer/library-scripts/docker-in-docker-debian.sh /tmp/library-scripts/
RUN apt-get update && bash /tmp/library-scripts/docker-in-docker-debian.sh \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* /tmp/library-scripts

# Install aws cli
COPY .devcontainer/library-scripts/aws-cli.sh /tmp/library-scripts/
RUN bash /tmp/library-scripts/aws-cli.sh "${USERNAME}" && rm -rf /tmp/library-scripts

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# [Optional] install global node packages.
RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g aws-cdk" 2>&1

VOLUME [ "/var/lib/docker" ]
# Setting the ENTRYPOINT to docker-init.sh will configure non-root access to 
# the Docker socket if "overrideCommand": false is set in devcontainer.json. 
# The script will also execute CMD if you need to alter startup behaviors.
ENTRYPOINT ["/usr/local/share/docker-init.sh"]
CMD ["sleep", "infinity"]
