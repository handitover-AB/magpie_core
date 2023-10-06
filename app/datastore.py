"""Thread-safe data store"""
from __future__ import annotations

import copy

from threading import Lock
from typing import Callable, List, Any, SupportsIndex, Generator


class DataList(list):
    """Implement a list where users are not allowed to delete items."""

    @staticmethod
    def pop(*_, **__) -> None:
        """Block users from deleting items in the data list"""
        raise TypeError("DataList object doesn't support item deletion")

    def __delitem__(self, __i: SupportsIndex | slice) -> None:
        """Block users from deleting items in the data list"""
        raise TypeError("DataList object doesn't support item deletion")


class TSDataStore:
    """Implement a thread-safe data store"""

    def __init__(self) -> None:
        self._data = DataList()
        self.lock = Lock()

    def append(self, data: Any) -> None:
        """Add items on top of list"""
        with self.lock:
            self._data.append(data)

    @staticmethod
    def pop(*_, **__) -> None:
        """Block users from deleting items in the data list"""
        raise TypeError("TSDataStore object doesn't support item deletion")

    @property
    def data(self) -> List[Any]:
        """Return a copy of the data"""
        with self.lock:
            out = copy.deepcopy(self._data)
        return out

    def _filter(self, filter_fn: Callable[[Any], bool]) -> Generator[Any]:
        """Return a filtered data set filtered using the filter function

        Returns a generator yielding items that match the items for which
        filter_fn(item) is True.
        """
        with self.lock:
            out = (item for item in filter(filter_fn, self._data))
        return out

    def __getitem__(self, item) -> Any:
        with self.lock:
            item = self._data[item]
        return item

    def __iter__(self):
        # Use the thread-safe copied array data:
        return (item for item in self.data)

    def __len__(self) -> int:
        with self.lock:
            length = len(self._data)
        return length
