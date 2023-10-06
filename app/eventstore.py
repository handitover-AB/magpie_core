"""Implement event store code"""
from __future__ import annotations

import datetime
import re
import time

from typing import List, Any, Callable
from app.datastore import TSDataStore


#######################
# EVENT STORE CLASSES
#
class Event:
    """A convenience class for events"""

    def __init__(self, event_name: str, data: Any) -> None:
        self.timestamp: datetime.datetime = datetime.datetime.now()
        self.name: str = event_name
        self.data: Any = data

    @property
    def elapsed(self) -> datetime.timedelta:
        """Return the elapsed time since the event was created

        Returns a timedelta object. To get the number of seconds
        elapsed, use the `seconds` property of the timedelta object:
        `elapsed.seconds`
        """
        return datetime.datetime.now() - self.timestamp

    def __str__(self):
        try:
            return f'{self.timestamp},"{self.name}","{str(self.data)}"'
        except TypeError as err:
            return f"{self}: {err}"


class TSEventStore(TSDataStore):
    """Thread-safe event store

    The idea is to write once and be able to read from many places. Intended
    use is to let other actors know about what what has been done that may
    be of importance to others.
    """

    def append(self, event_name: str, data: Any) -> None:  # pylint: disable=arguments-differ
        """Add data to the event store.

        `event_type` should be a string uniquely defining the type of event you add.
        `data` should be a Python object contaning the data you want to share.
        """
        event = Event(event_name, data)
        return super().append(event)

    def match(
        self, event_name: str, data_filter_fn: Callable[[Any], bool] | None = None
    ) -> List[Event]:
        """Return all events matching the specified name

        `event_type` should be a regular expression pattern to match event names with.
        E.g., to match all event names beginning with "MESSAGE_", supply `"MESSAGE_.*"`
        as pattern. To match event names ending with "_CREATED", supply `".*_CREATED"`
        as pattern, etc. Read about regular expression patterns here:
        https://docs.python.org/3/howto/regex.html#simple-patterns

        `data_filter_fn` [optional] if supplied, should be a function where
        data_filter_fn(item) returns True for events that should be matched.
        """
        pattern = re.compile(event_name, re.IGNORECASE)

        def _filter_fn(item: Event) -> bool:
            """Define matching function"""
            if data_filter_fn is not None:
                return bool(pattern.match(item.name) and data_filter_fn(item))
            return bool(pattern.match(item.name))

        return list(self._filter(_filter_fn))

    def wait_for_event(self, event_name: str, timeout_s: float = 30.0) -> Event | None:
        """Block execution until specified event is emitted

        Return the first event matching the event_name that was emitted
        since wait_for_event() was called.
        """
        start = datetime.datetime.now()
        while True:
            matches = [evt for evt in self.match(event_name) if evt.timestamp > start]
            if matches:
                return matches[0]
            if (datetime.datetime.now() - start).seconds > timeout_s:
                return None
            time.sleep(0.25)  # Let other threads run
