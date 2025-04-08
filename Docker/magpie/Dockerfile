FROM mcr.microsoft.com/playwright:v1.51.0

ARG MAGPIE_VER=UNKNOWN
ARG MAGPIE_CORE_VER=UNKNOWN

# Set timezone:
ENV TZ="Europe/Stockholm"

# Update packages:
RUN apt-get update

# Install graphviz:
RUN apt-get install -y graphviz

# Install certutil
RUN apt-get install -y libnss3-tools

# Install the tree command:
RUN apt-get install tree

# INSTALL PYTHON DEPENDENCIES
# Notice: Each RUN command is run in a separate shell.
# If we need the virtual python environment, it has
# to be activated separately, on each RUN line, before it is used:
RUN echo "Python version: $(python3 -V)"
RUN apt-get install -y python3.12-venv
RUN python3 -m venv /opt/.pyenv
RUN . /opt/.pyenv/bin/activate && pip install --upgrade pip
RUN . /opt/.pyenv/bin/activate && pip install wheel
# Install third-party libraries:
COPY requirements.txt /tmp
RUN . /opt/.pyenv/bin/activate && pip install -r /tmp/requirements.txt

# Update Playwright:
RUN . /opt/.pyenv/bin/activate && playwright install

# Create version information file:
RUN mkdir /opt/magpie
RUN echo "Magpie version: ${MAGPIE_VER}"
RUN echo ${MAGPIE_VER} > /opt/magpie/.MAGPIE_VERSION
RUN echo ${MAGPIE_CORE_VER} > /opt/magpie/.MAGPIE_CORE_VERSION

# Copy files:
COPY Docker/magpie/docker_entrypoint.sh  /opt/magpie/entrypoint.sh
COPY app/                                /opt/magpie/app/
COPY demo/                               /opt/magpie/demo/
COPY main.py                             /opt/magpie
COPY magpie_logo.txt                     /opt/magpie

RUN mkdir -p /opt/magpie/tmp && chmod ugo+rw /opt/magpie/tmp

RUN chmod +x                             /opt/magpie/entrypoint.sh
ENTRYPOINT [ "/opt/magpie/entrypoint.sh" ]
