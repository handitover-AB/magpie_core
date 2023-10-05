"""Define a global logger"""
import datetime
import logging
from typing import Iterable

import pytz
from tzlocal import get_localzone


logging.basicConfig(format="%(asctime)s [%(threadName)s] - %(message)s")
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class ISO8601Formatter(logging.Formatter):
    converter = datetime.datetime.fromtimestamp
    timezone = str(get_localzone())

    def formatTime(self, record, datefmt=None):
        """Override method in base class"""
        return self.converter(record.created, tz=pytz.timezone(self.timezone)).isoformat()


class CsvFileLogger(logging.Logger):
    """A thread-safe csv file logger"""

    def __init__(
        self, filename: str, field_names: Iterable[str], level: int = logging.NOTSET
    ) -> None:
        with open(filename, "w") as file:
            file.write(",".join(field_names) + "\n")
        super().__init__(filename, level)
        self.formatter = ISO8601Formatter("%(asctime)s,%(message)s")
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(self.formatter)
        self.addHandler(file_handler)
