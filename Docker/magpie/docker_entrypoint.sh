#!/bin/bash
# This is the entrypoint script for the magpie Docker image
DATETIME=$(date +"%Y%m%d_%H%M%S")
OUTPUTDIR_DOCKER=/opt/magpie/${DATETIME}
OUTPUTDIR_HOST=/data/output
PERFLOG_FILE=${OUTPUTDIR_DOCKER}/performance_log.csv

export PYTHONPATH=/opt/magpie
export TMPDIR=/opt/magpie/tmp
export OUTPUTDIR=${OUTPUTDIR_DOCKER}

function logging () {
    # Logs the CPU usage of the Magpie container.
    # The intent is to give information about the conditions surrounding
    # fault situations that might occure during test execution:
    echo "Timestamp,CpuLoadAvg1m,CpuLoadAvg5m,CpuLoadAvg15m,Cores" > $PERFLOG_FILE
    cores=$(nproc --all)
    while true; do
        loads=$(uptime | sed "s/.*average:\ //" | sed "s/\ //g")
        echo "$(date -Iseconds),${loads},${cores}"
        sleep 1
    done
}

# Output dir on host should be volume mounted
# onto /data/output. Artifacts will be copied here.

mkdir -p ${TMPDIR}
mkdir -p ${OUTPUTDIR_DOCKER}

echo "Output files will be owned by $USERID, belonging to group $GROUPID"

# Activate the virtual Python environment
echo "Activating the virtual Python environment..."
source /opt/.pyenv/bin/activate

logging >> $PERFLOG_FILE &
LOGGING_PID=$!
echo "Resource logging started."

# Using the X Virtual FrameBuffer tool (to be able to run browsers),
# run the tests with the arguments supplied from the command line.
# Put all pycache files in a temp directory in the Docker container;
# we don't want to pollute the host's file system with those files:
xvfb-run \
    python \
    -X pycache_prefix=${TMPDIR}/__pycache__ \
    /opt/magpie/main.py run "$@"

# Store the exit code for later use:
TEST_EXECUTION_RESULT=$?

# Try to create the output directory:
# Using '-p' will guarantee that the command does not
# fail even if the directory exists:
mkdir -p ${OUTPUTDIR_HOST}

# Copy the output files to the output directory,
# if it exists:
echo "Make artifacts accessible outside the Docker container:"
# Bash replace: ${main_string/search_term/replace_term}
echo "Copying artifacts to ${OUTPUTDIR_HOST/\/data/}"
cp -r ${OUTPUTDIR_DOCKER} ${OUTPUTDIR_HOST}
if [ "${USERID}" != "" ] && [ "${GROUPID}" != "" ]; then
    echo "Changing ownership of output files to user id ${USERID} and group id ${GROUPID}"
    chown -R ${USERID}:${GROUPID} ${OUTPUTDIR_HOST}
fi

# Stop logging
kill $LOGGING_PID

# Exit with the exit code from the test execution:
exit ${TEST_EXECUTION_RESULT}
