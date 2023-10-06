"""Implement logic for actors

Actors provide files with code for:
 - Model (defines states and transitions)
 - Action functions
 - State functions
 - Condition functions
"""
from __future__ import annotations

import os

from types import ModuleType
from typing import Any

from app.fsm.model import Model
from app.parser import FileParser
from app.actor import Actor


class ModelBasedActor(Actor):  # pylint: disable=too-many-instance-attributes
    def __init__(self, *, actor_module: ModuleType, name: str = "", config: Any = None) -> None:
        super().__init__(actor_module=actor_module, config=config)
        self.model: Model = Model(name)
        self._model_file_path: str = ""
        self._actions_module: ModuleType | None = None
        self._conditions_module: ModuleType | None = None
        self._states_module: ModuleType | None = None
        # Add setup, if it exists:
        self.setup = None
        if hasattr(self.actor_module, "setup"):
            self.setup = self.actor_module.setup
        # Add teardown, if it exists:
        self.teardown = None
        if hasattr(self.actor_module, "teardown"):
            self.teardown = self.actor_module.teardown
        # Construct the model:
        if not actor_module:
            raise AttributeError("No actor was defined!")
        self._build()

    def _build(self) -> None:
        """Construct the model from supplied modules"""
        # Get model, action functions and state functions from the actor module:
        file_parser = FileParser()

        actor_module_dir = os.path.dirname(os.path.relpath(self.actor_module.__file__, os.getcwd()))
        model_file_path = f"{actor_module_dir}/model"
        if not os.path.exists(model_file_path):
            err_msg = f"{self.actor_module.__name__} " "has no model. Please add a 'model' file."
            raise FileNotFoundError(err_msg)
        if hasattr(self.actor_module, "conditions"):
            self._conditions_module = getattr(self.actor_module, "conditions")
        if hasattr(self.actor_module, "actions"):
            self._actions_module = getattr(self.actor_module, "actions")
        if hasattr(self.actor_module, "states"):
            self._states_module = getattr(self.actor_module, "states")

        # Parse the model file, will raise a ParseError
        # if there are syntax errors:
        model_path = f"{os.path.dirname(os.path.abspath(self.actor_module.__file__))}/model"
        self.model = file_parser.parse(model_path)
        self.model.name = self.actor_module.__name__.replace("tests.actors.", "")

        # Add condition hooks:
        for name, condition in self.model.conditions.items():
            condition_fn_name = self._fn_name_from_name(name)
            if hasattr(self._conditions_module, condition_fn_name):
                condition.fn = getattr(self._conditions_module, condition_fn_name)
            # TODO: Error / warning if fn is missing?

        # Add action hooks:
        for name, action in self.model.actions.items():
            action_fn_name = self._fn_name_from_name(name)
            if hasattr(self._actions_module, action_fn_name):
                action.fn = getattr(self._actions_module, action_fn_name)
            # TODO: Error / warning if fn is missing?

        # Add state hooks:
        for name, state in self.model.states.items():
            state_fn_name = self._fn_name_from_name(name)
            if hasattr(self._states_module, state_fn_name):
                state.fn = getattr(self._states_module, state_fn_name)
            # TODO: Error / warning if fn is missing?

    @staticmethod
    def _fn_name_from_name(name: str) -> str:
        """Convert a name with mixed case and spaces into a snake case name"""
        return name.lstrip("'").rstrip("'").lower().replace(" ", "_")
