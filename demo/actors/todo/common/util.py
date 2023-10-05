"""Util function definitions"""
import os
from pathlib import Path

from app import LOGGER


def _call_test_env_script(cmd: str):
    base_path = Path(__file__).parent.parent.parent.parent  # :)
    cmd_string = f"{base_path / 'todo_resources' / 'test_env.sh'} {cmd}"
    process = os.popen(cmd_string)
    result = process.read()
    if result:
        LOGGER.info(result.rstrip("\n"))


def start_test_env():
    LOGGER.info("Starting the test environment...")
    _call_test_env_script("start")


def stop_test_env():
    LOGGER.info("Stopping the test environment...")
    _call_test_env_script("stop")
