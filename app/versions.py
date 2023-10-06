"""Implement code for checking versions of magpie and magpie_core repos

TODO: Assumes that magpie_core is a submodule to the magpie repo.
      Should be broken out, eventually.
"""

import subprocess

from typing import List
from pathlib import Path


class GitNotFoundError(Exception):
    """Raise if git is not on the system"""


def dir_is_available(cwd: str) -> bool:
    return Path(cwd).exists()


def git_is_available() -> bool:
    try:
        subprocess.run(["git", "-h"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return True


def run_command(*, args: List[str], cwd: str = ".") -> str:
    output = ""
    try:
        output_raw = subprocess.run(args, capture_output=True, check=True, cwd=cwd)
        output = output_raw.stdout.decode("utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        if exc.__class__ != subprocess.CalledProcessError:
            print(exc)
    return output


def get_version_string(cwd: str = ".") -> str:
    """Builds a version string from the git repo in the current directory

    Raises GitNotFoundError if git is not on the computer
    Raises FileNotFoundError if cwd is not found
    """
    if not git_is_available():
        raise GitNotFoundError("Can't find git on your computer. Maybe it is not installed?")
    if not dir_is_available(cwd):
        raise FileNotFoundError(f"Directory {cwd} cound not be found.")

    branch = run_command(args=["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    if branch == "HEAD":
        branch = ""

    describe_string = run_command(
        args=["git", "describe", "--always", "--match", '"*magpie*"', "--dirty"], cwd=cwd
    )

    if branch:
        output = f"{branch}--{describe_string}"
    else:
        output = describe_string
    if not output:
        return "-- No version information was found --"
    return output.replace("\n", "")
