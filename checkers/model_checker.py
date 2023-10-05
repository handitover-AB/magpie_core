"""Implement a checker for Magpie models.

Checks that a Magpie model has a valid syntax.
Reports errors in a human-friendly way.
"""
from __future__ import annotations

import sys

from app.fsm.model import ModelError
from app.parser import FileParser

from typing import List


def check(args: str | List[str]) -> int:
    """Check a file
    
    Log output to STDOUT. Return exit code 0 on success, 
    exit code > 0 on fail.
    """
    file_parser = FileParser()
    if isinstance(args, str):
        args = [args]
    exit_code = 0
    for file_to_check in args:
        try:
            file_parser.parse(file_to_check)
        except ModelError as err:
            print(err)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    exit_code = check(sys.argv[1:])
    sys.exit(exit_code)