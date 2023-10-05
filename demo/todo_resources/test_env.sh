#!/usr/bin/env bash
SCRIPT_ABSOLUTE_DIR=$(cd $(dirname "${0}") && pwd)

function docker_compose_cmd () {
    if docker --help | grep "compose\*" > /dev/null; then
        echo "docker compose"
    elif which docker-compose > /dev/null; then
        echo "docker-compose"
    else
        echo "❌ Error: Neither docker compose nor docker-compose are"
        echo "available. One of them must be installed for this to work."
        exit 1
    fi
}

ARG=$1
if [[ "${ARG}" == "start" ]]; then
    CMD="up -d"
elif [[ "${ARG}" == "stop" ]]; then
    CMD="down"
else
    CMD="--help"
fi

(cd ${SCRIPT_ABSOLUTE_DIR}/.. && pwd && $(docker_compose_cmd) -f todo_resources/docker-compose.yaml ${CMD})