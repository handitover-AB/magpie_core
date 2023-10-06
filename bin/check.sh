#!/usr/bin/env bash
INCLUDE_PATHS=(
    main.py
    app/
    unittests/
    demo/
)


if [ "${TMPDIR}" == "" ]; then
    export TMPDIR=${PWD}
fi


# Check formatting:
echo
echo "Checking code formatting..."
echo

EXIT_CODE=0
for INCLUDE_PATH in "${INCLUDE_PATHS[@]}"; do
    echo 
    echo "Checking ${INCLUDE_PATH}"
    PYTHONPATH=. python \
        -X pycache_prefix=${TMPDIR}/__pycache__ \
        -m black -l 100 \
        --check ${INCLUDE_PATH}
    EXIT_CODE=$(expr ${EXIT_CODE} + $?)
done


if [ "${EXIT_CODE}" != "0" ]; then
    echo
    echo ".--------------------------------------------------------."
    echo "| ❌ Ouch! It seems you need to format your Python code! |"
    echo "|    Run this command to update your files:              |"
    echo "|    $ black -l 100 main.py app/ unittests/ demo/        |"
    echo "'--------------------------------------------------------'"
    echo
    exit 1
else
    echo
    echo ".------------------------."
    echo "| ✅ Yay! Formatting OK! |"
    echo "'------------------------'"
    echo
fi



# Run pylint with correct options:
echo
echo "Checking your Python code for errors..."
echo

EXIT_CODE=0
for INCLUDE_PATH in "${INCLUDE_PATHS[@]}"; do
    echo 
    echo "Checking ${INCLUDE_PATH}"
    PYTHONPATH=. python \
        -X pycache_prefix=${TMPDIR}/__pycache__ \
        -m pylint \
        --rcfile .pylintrc ${INCLUDE_PATH}
    EXIT_CODE=$(( ${EXIT_CODE} | $? ))  # Bitwise OR
done

if [[ ${EXIT_CODE} -ne 0 && ${EXIT_CODE} -ne 4 ]]; then
    echo
    echo ".------------------------------------------------------------------."
    echo "| ❌ Ouch! It seems you need to check your Python code for errors! |"
    echo "|    Run this command to update your files:                        |"
    echo "|    $ PYTHONPATH=. pylint --rcfile .pylintrc app unittests demo   |"
    echo "'------------------------------------------------------------------'"
    echo
    exit 1
else
    echo
    echo ".------------------------."
    echo "| ✅ Yay! Code check OK! |"
    echo "'------------------------'"
    echo
fi

# Run unit tests with coverage measurements:
echo
echo "Running unittests with coverage measurements:"
echo
PYTHONPATH=. coverage run --source app --branch --data-file=./output/.coverage -m pytest -v unittests/*.py

# Print the coverage report:
echo
echo
echo "===== COVERAGE INFORMATION ====="
coverage report -m --data-file=./output/.coverage
