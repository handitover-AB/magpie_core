"""Implement a Finite State Machine (FSM)

A model does not run by itself. The FSM is the actual
execution engine that keeps track of the current state,
picks the next one and calls all state functions, action
functions and condition functions until all run conditions
are met.

The FSM keeps track of the results from execution and is
responsible for the creation of audit log files and test
summaries/reports.
"""
from __future__ import annotations

import inspect
import os
import random
import time
import traceback

from datetime import datetime
from typing import List, Dict
from pathlib import Path

import app.pause_manager

from app import LOGGER, OUTPUTDIR, THREAD_LOCK, Page, Strategy
from app.fsm.model_based_actor import ModelBasedActor
from app.fsm.action import Action
from app.fsm.model import Model, NavigationStrategy, PathGenerator
from app.fsm.history import AuditTrail
from app.fsm.results import Result, SessionSummary
from app.fsm.state import State
from app.fsm.transition import Transition
from app.logger import CsvFileLogger
from app.properties import running_in_docker
from app.util import safe_file_name


##################
# HELPER CLASSES
#
class RunOptions:  # pylint: disable=too-few-public-methods
    """Keep settings for run configuration"""

    def __init__(
        self,
        max_run_time_s: int = -1,
        max_transitions: int = -1,
        stop_on_fail: bool = False,
        stop_at_state: str | None = None,
        strategy: Strategy = Strategy.SmartRandom,
    ) -> None:
        self.max_run_time_s = max_run_time_s
        self.max_transitions = max_transitions
        self.stop_on_fail = stop_on_fail
        self.stop_at_state = stop_at_state
        self.strategy = strategy

    def as_dict(self) -> Dict:
        return self.__dict__


###############
# THE MACHINE
#
class Machine:  # pylint: disable=too-many-instance-attributes
    """Implement a Finite State Machine"""

    def __init__(
        self,
        actor: ModelBasedActor,
        max_run_time_s: int = -1,
        max_transitions: int = -1,
        stop_on_fail: bool = False,
        stop_at_state: str | None = None,
        strategy: Strategy = Strategy.FullCoverage,
    ) -> None:
        # Init - from args:
        self.run_options = RunOptions(
            max_run_time_s, max_transitions, stop_on_fail, stop_at_state, strategy
        )
        self.audit_trail = AuditTrail()
        self.browser_page: Page | None = None
        self.error_msg: str = ""
        self.actor: ModelBasedActor = actor
        self.model: Model = actor.model
        self.start_time: int | None = None
        self.summary: SessionSummary = SessionSummary(self.model)
        filename = safe_file_name(str(Path(OUTPUTDIR) / f"{self.actor.name}.log.csv"))
        field_names = ("Timestamp", "Type", "Name", "Result")
        self.log_file = CsvFileLogger(filename, field_names)

        # Init other variables:
        self._current_state: State | None = None
        self._predetermined_path: PathGenerator | None = None
        if strategy == Strategy.ShortestPath:
            self._predetermined_path = self.model.shortest_path(
                self.model.initial_state.name, stop_at_state
            )

    @property
    def has_browser(self) -> bool:
        """Return True if the machine requires a browser"""
        return self.browser_page is not None

    @property
    def current_state(self) -> State:
        """Return the current state of the Finite State Machine"""
        return self._current_state

    @current_state.setter
    def current_state(self, new_state: State) -> None:
        # TODO: Validate state
        self._current_state = new_state

    def _should_continue(self) -> bool:
        if self.run_options.max_run_time_s > 0:
            duration = time.time() - self.start_time
            if duration > self.run_options.max_run_time_s:
                LOGGER.info("ℹ️  Max run time exceeded! Stopping...")
                return False
        if self.run_options.max_transitions > 0:
            if self.summary.transitions_count >= self.run_options.max_transitions:
                LOGGER.info("ℹ️  Max transitions exceeded! Stopping...")
                return False
        if self.current_state.name == self.run_options.stop_at_state:
            LOGGER.info("ℹ️  End state reached! Stopping...")
            return False

        # TODO: Check configured strategy, break when we
        #       have reached 100% coverage, if FullCoverage
        return True

    def _handle_exception(self, exc: Exception, what_failed: State | Action):
        # Get traceback info:
        tb = exc.__traceback__.tb_next  # pylint: disable=invalid-name
        if not tb:
            tb = exc.__traceback__  # pylint: disable=invalid-name
        if isinstance(what_failed, State):
            file_name_prefix = what_failed.name.replace(" ", "_")
            log_message_prefix = "State"
        elif isinstance(what_failed, Action):
            file_name_prefix = what_failed.fn_name.replace(" ", "_")
            log_message_prefix = f"Action {file_name_prefix}()"

        if tb:
            line_no = tb.tb_lineno
            file_name = os.path.relpath(tb.tb_frame.f_code.co_filename)
            # Log error:
            LOGGER.error(
                '"%s": ❌ ERROR: %s failed in file "%s", line %s:',
                self.current_state.name,
                log_message_prefix,
                file_name,
                line_no,
            )
        else:
            LOGGER.error('"%s": ❌ ERROR: %s failed', self.current_state.name, log_message_prefix)
        LOGGER.error(
            '"%s":    \'-- [%s] Message: %s\n%s',
            self.current_state.name,
            exc.__class__.__name__,
            exc,
            traceback.format_exc(),
        )
        # Save screenshot:
        if self.has_browser:
            file_path = self.save_screenshot(file_name_prefix)
            # Make path of screenshot relevant outside the Docker container, if running in one:
            if running_in_docker():
                file_path = file_path.replace("/opt/magpie", ".")
            LOGGER.info(
                "\"%s\":    '-- Saving screenshot '%s'",
                self.current_state.name,
                file_path,
            )

    @staticmethod
    def _is_end_state(state: State) -> bool:
        return len(state.outbounds) == 0

    def _get_allowed_outbounds(self, state: State) -> List[Transition]:
        # Get outbound transitions and filter them according to
        # each associated condition function (if any):
        condition_args = [self.browser_page]
        outbounds = []
        for outbound in state.outbounds:
            if outbound.condition and callable(outbound.condition.fn):
                # Run the condition function, allow the outbound if the
                # condition function returns True:
                condition_result = outbound.condition.fn(*condition_args)
                if condition_result is True:
                    outbounds.append(outbound)
            else:
                # If the outbound does not have a condition, it is
                # considered allowed:
                outbounds.append(outbound)
        return outbounds

    def _get_outbound(self, outbounds: List[Transition]) -> Transition | None:
        # Apply selected strategy when selecting what to do next:
        outbound = None

        if self.run_options.strategy == Strategy.ShortestPath:
            try:
                next_state_name = next(self._predetermined_path)
            except StopIteration:
                # We're done!
                return None
            path_strategy = self._predetermined_path.strategy
            # fmt: off
            # Build outbounds list from transitions that lead to
            # next state.
            candidates = [ob for ob in outbounds if ob.end_state.name == next_state_name]
            if path_strategy == NavigationStrategy.PESSIMISTIC:
                # Remove outbounds with conditions:
                candidates = [cand for cand in candidates if not cand.condition]
            transitions = self.summary.unvisited_transitions
            candidates = [cand for cand in candidates if cand in transitions]
            if not candidates:
                transitions = self.summary.unvisited_transitions
                candidates = [cand for cand in candidates if cand in transitions]
            outbound = random.choice(candidates)
            # fmt: on

        if self.run_options.strategy == Strategy.PureRandom:
            # Pick any outbound transition:
            outbound: Transition = random.choice(outbounds)

        if self.run_options.strategy in (Strategy.SmartRandom, Strategy.Random):
            # Pick an unvisited transition, if any. If not,
            # pick randomly between all outbounds:
            candidates: List[Transition] = []
            for transition in self.summary.unvisited_transitions:
                if transition.start_state == self.current_state and transition in outbounds:
                    candidates.append(transition)
            if len(candidates) == 0:
                candidates = outbounds
            if candidates:
                outbound: Transition = random.choice(candidates)

        elif self.run_options.strategy == Strategy.FullCoverage:
            # Strive for full coverage, pick a transition that will
            # yield the highest coverage at this point:
            raise NotImplementedError(
                "FullCoverage is not implemented yet, "
                "please select PureRandom or SmartRandom "
                "until fixed."
            )

        return outbound

    def _execute_state(self, state: State) -> Result:
        # Init:
        state_result: Result = Result.NOT_APPLICABLE

        # Update state pointer:
        self.current_state = state

        # Run the associated state function, if it exists:
        if self.current_state.fn:
            # Do not run the state fn while pause is requested:
            while app.pause_manager.is_paused():
                time.sleep(0.5)

            # OK, continue:
            try:
                state_args = []
                for parameter in inspect.signature(state.fn).parameters.values():
                    if str(parameter) == "page: app.page.Page":
                        state_args += [self.browser_page]
                    elif str(parameter) == "actor: app.actor.Actor":
                        state_args += [self.actor]
                    elif str(parameter) in ("_", "__", "*_", "*__"):
                        state_args += [None]
                    else:
                        err_msg = (
                            f"Unsupported parameter {str(parameter)} in the signature "
                            f"for state function {state.fn}"
                        )
                        raise AttributeError(err_msg)
                self.current_state.fn(*state_args)
                LOGGER.info('"%s": ✅ State OK', self.current_state.name)
                state_result = Result.PASSED
            except KeyboardInterrupt:
                LOGGER.info("User initiated break (likely pressed CTRL+C)")
            except Exception as exc:  # pylint: disable=broad-except
                # Catch any error potentially thrown by the state function
                self._handle_exception(exc, self.current_state)
                state_result = Result.FAILED
        else:
            LOGGER.info('"%s": No function to run', self.current_state.name)

        # Record result:
        self.summary.record_visit(self.current_state, state_result)
        self.log_file.info('"state","%s","%s"', self.current_state.name, state_result)

        # Return:
        return state_result

    def _execute_action(self, action: Action) -> Result:
        """Execute the action, if defined."""
        # Sanity checks:
        if action.fn is None:
            raise AttributeError(f"Action {action.fn_name}() is missing!")

        # Assemble arguments list to the action function:
        action_args = []
        for parameter in inspect.signature(action.fn).parameters.values():
            if str(parameter) == "page: app.page.Page":
                if self.has_browser:
                    action_args += [self.browser_page]
                else:
                    err_msg = (
                        f"{self} does not have a browser, but the action"
                        f"{action.fn_name} expects a browser page as argument!"
                    )
                    raise AttributeError(err_msg)
            elif str(parameter) == "actor: app.actor.Actor":
                action_args += [self.actor]
            elif str(parameter) in ("_", "__", "*_", "*__"):
                action_args += [None]
            else:
                err_msg = (
                    f"Unsupported parameter {parameter} in the signature "
                    f"for state function {action.fn_name}"
                )
                raise AttributeError(err_msg)

        # Run the action function:
        action_result = Result.NOT_APPLICABLE

        # Do not run the action fn while pause is requested:
        while app.pause_manager.is_paused():
            time.sleep(0.5)

        # OK, continue:
        try:
            action.fn(*action_args)
            action_result = Result.PASSED
        except KeyboardInterrupt:
            LOGGER.info("User initiated break (likely pressed CTRL+C)")
        except Exception as exc:  # pylint: disable=broad-except
            # Catch any error potentially thrown by the action function
            LOGGER.info("FN SIGNATURE: %s", inspect.signature(action.fn))
            LOGGER.info("ARGS: %s", str(action_args))
            self._handle_exception(exc, action)
            action_result = Result.FAILED

        self.summary.record_visit(action, action_result)
        self.log_file.info('"action","%s","%s"', action.name, action_result)

        return action_result

    def save_screenshot(self, file_name_prefix: str = "") -> str:
        """Saves a screenshot. Returns the file name of the image."""
        # Save a screenshot:
        file_name = file_name_prefix
        file_name += f"_screenshot_{datetime.now().strftime('%H%M%S_%f')[:-4]}.png"
        file_path = os.path.join(OUTPUTDIR, "screenshot", file_name)
        self.browser_page.screenshot(path=file_path, full_page=True)
        return file_path

    def start(self):
        """Run the state machine"""
        # Init:
        self.start_time = time.time()

        # Set start state:
        self._execute_state(self.model.initial_state)

        # Main loop:
        while self._should_continue():
            if self._is_end_state(self.current_state):
                # Break if no outbound transitions
                # TODO: If configured, reset browser session and return to initial_state!
                LOGGER.info(
                    '"%s": Can\'t find any outbound transitions, '
                    "seems like this is an end state.",
                    self.current_state.name,
                )
                break

            # Aquire lock:
            THREAD_LOCK.acquire()  # pylint: disable=consider-using-with
            try:
                # Get all outbounds that fulfil their conditions:
                outbounds = self._get_allowed_outbounds(self.current_state)
                # Pick an outbound depending on current strategy:
                outbound = self._get_outbound(outbounds)

                # If we didn't get any outbound transition,
                # skip to next loop of the main loop:
                if not outbound:
                    time.sleep(0.10)  # 100 ms sleep
                    continue

                # Running the action function, if it exists:
                action_result = None
                if outbound.action:
                    cond = outbound.condition
                    condition_info = f" - [{cond.name}] was True" if cond else ""
                    LOGGER.info(
                        '"%s": %s()%s',
                        self.current_state.name,
                        outbound.action.fn_name,
                        condition_info,
                    )
                    action_result = self._execute_action(outbound.action)
                else:
                    LOGGER.info(
                        '"%s": No action for transition to "%s". Changing state.',
                        outbound.start_state.name,
                        outbound.end_state.name,
                    )
            finally:
                # Release lock:
                THREAD_LOCK.release()

            # Record transition visit:
            outbound_result = action_result if action_result else Result.NOT_APPLICABLE
            self.summary.record_visit(outbound, outbound_result)
            self.log_file.info('"outbound","%s","%s"', outbound.name, outbound_result)

            # Fail fast, if required by user:
            if self.run_options.stop_on_fail and action_result == Result.FAILED:
                break

            # Change state:
            if action_result is None or (action_result and action_result == Result.PASSED):
                LOGGER.info(
                    '"%s": %s "%s"',
                    self.current_state.name,
                    outbound.arrow,
                    outbound.end_state.name,
                )
                # *** This is the actual state change ***:
                self.current_state = outbound.end_state
                # Save to audit trail:
                self.audit_trail.append(outbound)

            # Let other threads run, if needed:
            if self.has_browser:
                self.browser_page.wait_for_timeout(100)

            # Run state function, if it exists:
            state_result = self._execute_state(self.current_state)
            # Fail fast, if required by user:
            if self.run_options.stop_on_fail and state_result == Result.FAILED:
                break

            # Let other threads run, if needed:
            if self.has_browser:
                self.browser_page.wait_for_timeout(100)

        # Wrap-up:
        self.summary.duration = time.time() - self.start_time
