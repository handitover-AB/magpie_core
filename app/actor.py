"""Implement actor logic"""
from types import ModuleType


class Actor:
    """Actor base class"""

    def __init__(self, *, actor_module: ModuleType, name: str = "", config=None) -> None:
        self.actor_module: ModuleType = actor_module
        self.name: str = name
        self.config = config
