#!/bin/bash
DATETIME=$(date +"%Y%m%d_%H%M%S")

export TMPDIR=/opt/magpie/tmp
mkdir -p ${TMPDIR}

# Activate the virtual Python environment
echo "Activating the virtual Python environment..."
source /opt/.pyenv/bin/activate

echo "Running the check job..."
/data/bin/check.sh "$@"
EXIT_CODE=$?

# Wrap-Up safety measure:
# delete any pycache files if created
CACHE_FILES=$(find . -name __pycache__)
if [ ${CACHE_FILES} ]; then
    echo -n "Removing pycache files..."
    echo ${CACHE_FILES} | xargs rm -rf
    echo "OK"
fi

# Exit with the exit code from the check job:
exit ${EXIT_CODE}
