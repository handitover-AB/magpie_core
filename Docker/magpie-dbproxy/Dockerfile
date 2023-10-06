# This Dockerfile creates a simple web service for
# executing queries on an SQL database by invoking the
# `sqlcmd` tool. The intended use is to simplify database
# access from automated tests.
#
# How to build (from project root, bash or compatible): 
#   docker build --platform=linux/amd64 -t magpie-dbproxy:localbuild Docker/magpie-dbproxy
#
# How to run (from project root, bash or compatible):
#   docker run \
#     -it \
#     -e MAGPIE_DBPROXY_SQL_SERVER_HOST="<DB_HOST:PORT HERE, e.g. localhost:1433>" \
#     -e MAGPIE_DBPROXY_SQL_SERVER_USER="<USER HERE, e.g sa>" \
#     -e MAGPIE_DBPROXY_SQL_SERVER_PASSWORD="<PASSWORD HERE, e.g. MyS3cretP4ssw0rd>" \
#     -e MAGPIE_DBPROXY_SQL_SERVER_DBNAME="<DBNAME HERE, e.g. MyDatabase>" \
#     -e OUTPUTDIR=/opt/dbproxy/log \
#     -v OUTPUTDIR:/opt/dbproxy/log \
#     magpie-dbproxy:localbuild
#
FROM --platform=linux/amd64 ubuntu:22.04
USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y curl


##################
# INSTALL PYTHON
#
RUN apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3


#######################
# INSTALL MSSQL-TOOLS
#
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | tee /etc/apt/sources.list.d/msprod.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools unixodbc-dev


##################
# COPY RESOURCES
#
COPY server.py     /opt/dbproxy/server.py
COPY entrypoint.sh /opt/dbproxy/entrypoint.sh


#####################
# INVOKE ENTRYPOINT
#
ENTRYPOINT [ "/opt/dbproxy/entrypoint.sh" ]
