#!/usr/bin/env bash

# Set up Magpie for local test development.
#
# - Install a virtual Python environment with all third-party dependencies.
# - Install Playwright browsers
# - Check if Graphviz is installed, prompt the user to install it if not.

SCRIPT_RELATIVE_DIR=$(dirname "${0}")
MAGPIE_CORE_ABSOLUTE_DIR=$(cd "${SCRIPT_RELATIVE_DIR}/.." && pwd)

UNAME_OUT="$(uname -s)"

case "${UNAME_OUT}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${UNAME_OUT}"
esac


if [ "${MACHINE}" == "Mac" ] && [ "${MACHINE}" != "Linux" ]; then
    PIP_ACTIVATION_COMMAND="source ./.pyenv/bin/activate"
elif [ "${MACHINE}" == "MinGw" ]; then
    PIP_ACTIVATION_COMMAND="source ./.pyenv/Scripts/activate"
else
    echo " .---------------------------------------------------------."
    echo " | This setup script is not supported on your environment. |"
    echo " | For now, you're on your own... Sorry :(                 |"
    echo " '---------------------------------------------------------'"
    exit 1
fi

################################
#  INSTALL PYTHON REQUIREMENTS
#
python3 -m venv .pyenv && ${PIP_ACTIVATION_COMMAND} && pip install --upgrade pip
pip install wheel
pip install -r ${MAGPIE_CORE_ABSOLUTE_DIR}/requirements.txt


####################################
#  INSTALL PLAYWRIGHT DEPENDENCIES
#
playwright install


#####################
#  INSTALL GRAPHVIZ
#
if [ "$(which dot)" == "" ]; then
    echo "Installing graphviz..."
    if [ "${MACHINE}" != "Mac" ]; then
        brew install graphviz
    fi

    if [ "${MACHINE}" != "Linux" ]; then
        sudo apt install graphviz
    fi

    if [ "${MACHINE}" != "MinGw" ]; then
        echo ".-----------------------------------------------------."
        echo "| ⚠️ Automated installation of graphviz is not         |"
        echo "|   possible in your environment. You need to do a    |"
        echo "|   manual installation.                              |"
        echo "|                                                     |"
        echo "|   Please follow the installation instructions here: |" 
        echo "|   https://www.graphviz.org/download/                |"
        echo "'-----------------------------------------------------'"
    fi
fi