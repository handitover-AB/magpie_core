#!.pyenv/bin/python  # pylint: disable=missing-module-docstring
import argparse
import os
import sys
import time
from pathlib import Path

from importlib import import_module
from typing import List, Dict

import graphviz

from dotenv import load_dotenv
from packaging import version
from playwright._repo_version import version as playwright_version
from texttable import Texttable

from app import LOGGER
from app.fsm.action import Action
from app.fsm.state import State
from app.sessions import start_sessions, Session
from app.render import render_session
from app.fsm.model import ModelError
from app.parser import ParsingError
from app.ide.server import main as magpie_ide_main
from app.properties import running_in_docker
from app.versions import get_version_string, GitNotFoundError


load_dotenv()
MAIN_FILE_LOCATION = str(Path(__file__).parent)
PLAYWRIGHT_MIN_VERSION = "1.35.0"

SUMMARY_ASCII = r"""
 ____
/ ___| _   _ _ __ ___  _ __ ___   __ _ _ __ _   _
\___ \| | | | '_ ` _ \| '_ ` _ \ / _` | '__| | | |
 ___) | |_| | | | | | | | | | | | (_| | |  | |_| |
|____/ \__,_|_| |_| |_|_| |_| |_|\__,_|_|   \__, |
                                            |___/
"""
SESSIONS_ASCII = r"""
  ____                _
 / ___|  ___  ___ ___(_) ___  _ __  ___
 \___ \ / _ \/ __/ __| |/ _ \| '_ \/ __|
  ___) |  __/\__ \__ \ | (_) | | | \__ \
 |____/ \___||___/___/_|\___/|_| |_|___/
"""

SESSIONS: List[Session] = []
RESULTS: Dict[str, any] = dict()
WHAT_TO_RUN: str


#################
# CUSTOM ERRORS
#
class PlaywrightVersionError(Exception):
    """Raise for incompatibility problems with Playwright"""


#####################
# UTILITY FUNCTIONS
#
def check_playwright_compatibility():
    if version.parse(playwright_version) < version.parse(PLAYWRIGHT_MIN_VERSION):
        err_msg = (
            "\n\n"
            ".--------------------------------------------------------.\n"
            "| ❌ ERROR: You need to upgrade your Playwright version  |\n"
            f"|    Your current version is {playwright_version}, but you need        |\n"
            f"|    to have at least version {PLAYWRIGHT_MIN_VERSION}. Run the command    |\n"
            "|      pip install --upgrade playwright                  |\n"
            "|    followed by                                         |\n"
            "|      playwright install                                |\n"
            "'--------------------------------------------------------'\n"
        )
        raise PlaywrightVersionError(err_msg)


def run(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    what_to_run: str, headless=False
) -> int:
    """Run a test and return the exit code"""
    global SESSIONS, WHAT_TO_RUN  # pylint: disable=global-statement
    # TODO: Refactor to decrease cyclomatic complexy, increase testability etc.

    # Sanity check:
    what_path = Path(what_to_run)
    if not what_path.exists():
        LOGGER.warning("Could not find '%s', stopping...", what_to_run)
        sys.exit(1)

    WHAT_TO_RUN = what_to_run
    # Import what to run as a module:
    module = None
    if what_path.is_file():
        module = str(what_path.parent / what_path.stem).replace("/", ".").replace("\\", ".")
        sys.path.insert(0, str(what_path.parent))
    elif what_path.is_dir():
        module = str(what_path).replace("/", ".").replace("\\", ".")
        sys.path.insert(0, str(what_path))

    # Another sanity check:
    if module is None:
        raise ModuleNotFoundError(module)

    # Expect the Magpie code to be mounted on /data in Docker containers:
    if running_in_docker():
        sys.path.append("/data")
    else:
        sys.path.insert(0, MAIN_FILE_LOCATION)

    # Try to import the module:
    try:
        LOGGER.info("Importing %s", module)
        test = import_module(module, ".")  # TODO: Allow files to be stored outside Magpie root
    except (ModelError, ParsingError) as err:
        LOGGER.info("❌ Can't run '%s'", module)
        LOGGER.info("   Errors:")
        LOGGER.info("     %s", "\n     ".join(str(err).split("\n")))
        sys.exit(1)

    # Create sessions list from module:
    SESSIONS = []
    test_setup_fn = None
    test_teardown_fn = None
    for attr_name in dir(test):
        attr = getattr(test, attr_name)
        if isinstance(attr, Session):
            SESSIONS.append(attr)
        if attr_name == "test_setup" and callable(attr):
            test_setup_fn = attr
        if attr_name == "test_teardown" and callable(attr):
            test_teardown_fn = attr

    # Anything to run?
    if not test_setup_fn and not SESSIONS and not test_teardown_fn:
        LOGGER.info("Nothing to run. Bye, bye! 👋")
        sys.exit(0)

    # Test setup here:
    if test_setup_fn:
        start_time = time.time()
        LOGGER.info("----- TEST SETUP -----")
        test_setup_fn()
        setup_exec_time = round(time.time() - start_time, 3)
    else:
        setup_exec_time = 0

    # Start the sessions:
    exec_ok = True
    if SESSIONS:
        start_time = time.time()
        LOGGER.info("----- SESSIONS -----")
        start_sessions(SESSIONS, headless)
        for _session in SESSIONS:
            exec_ok = exec_ok and not _session.has_failures
        session_exec_time = round(time.time() - start_time, 3)
    else:
        session_exec_time = 0

    # Test teardown here:
    if test_teardown_fn:
        start_time = time.time()
        LOGGER.info("----- TEST TEARDOWN -----")
        test_teardown_fn()
        teardown_exec_time = round(time.time() - start_time, 3)
    else:
        teardown_exec_time = 0
    LOGGER.info("----- DONE! -----")

    total_exec_time = setup_exec_time + session_exec_time + teardown_exec_time
    LOGGER.info("Test execution finished. Total execution time: %ss", round(total_exec_time))
    RESULTS.update({"setup_exec_time": setup_exec_time})
    RESULTS.update({"session_exec_time": session_exec_time})
    RESULTS.update({"teardown_exec_time": teardown_exec_time})
    RESULTS.update({"total_exec_time": total_exec_time})
    # Return exit code:
    return 0 if exec_ok else 1


def compile_sessions_info() -> str:  # pylint: disable=too-many-locals, too-many-statements
    """Return a multiline string containing sessions data"""
    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_chars(["-", "|", "+", "-"])
    table.set_cols_width([40, 25])

    def _coverage_string(coverage: int) -> str:
        """Return a human-friendly coverage string"""
        return f"{round(coverage)}%" if coverage else "--"

    out = ""

    for _session in SESSIONS:
        _summary = _session.machine.summary
        title = f"{_session.name} ({_session.actor.actor_module.__name__})"  # pylint: disable=protected-access
        # Switch off formatting with Black:
        # fmt: off
        out += "\n\n" + "*" * 74 + "\n"
        out += f"*  {title}\n"
        out += "* " + "=" * (len(title) + 2) + "\n"
        out += "*\n"
        out += f"*   Run time..............: {round(_summary.duration, 3)}s\n"
        out += f"*   Transitions...........: {_summary.total_transitions_visits_count}\n"
        # Coverage info:
        coverage = _coverage_string(_summary.states_coverage)
        out += f"*   States coverage.......: {coverage}\n"
        coverage = _coverage_string(_summary.actions_coverage)
        out += f"*   Actions coverage......: {coverage}\n"
        coverage = _coverage_string(_summary.transitions_coverage)
        out += f"*   Transitions coverage..: {coverage}\n"
        # TODO: Separate transition coverage (Happy / all)
        out += "*\n"
        # Switch formatting with Black on again:
        # fmt: on

        if _session.machine.error_msg:
            err_table = Texttable()
            err_table.set_cols_width([64])
            err_table.add_row([_session.machine.error_msg])
            lines = err_table.draw()
            out += "*   " + "\n*   ".join(lines.split("\n")) + "\n"
            out += "*\n"

        # STATES:
        table.reset()
        table.add_rows([["STATE NAME", "RESULT COUNTS"]], header=True)
        for state_name in sorted(_session.machine.model.states.keys()):
            state_results = _summary.results.states.get(state_name, None)
            short_summary = state_results.short_summary if state_results else ""
            state_string = (f"{state_name[:40]}" + "." * 40)[:40]
            table.add_row([state_string, short_summary])
        lines = table.draw()
        out += "*" + "\n*   ".join(lines.split("\n")) + "\n"
        out += "*\n"

        # ACTIONS:
        table.reset()
        table.add_rows([["ACTION NAME", "RESULT COUNTS"]], header=True)
        for action_name in sorted(_session.machine.model.actions.keys()):
            action_results = _summary.results.actions.get(action_name, None)
            short_summary = action_results.short_summary if action_results else ""
            action_name = action_name.replace(" ", "_").lower()
            action_string = (f"{action_name[:38]}()" + "." * 40)[:40]
            table.add_row([action_string, short_summary])
        lines = table.draw()
        out += "*" + "\n*   ".join(lines.split("\n")) + "\n"

        # UNCOVERED STATES:
        out += "*\n"
        uncovered_states = _summary.unvisited_states.keys()
        if uncovered_states:
            out += f'*   UNCOVERED STATES: {", ".join(uncovered_states)}\n'

        # UNCOVERED ACTIONS:
        uncovered_actions = _summary.unvisited_actions.keys()
        if uncovered_actions:
            out += f'*   UNCOVERED ACTIONS: {", ".join(uncovered_actions)}\n'
        out += "*\n"

        # RENDER GRAPH:
        try:
            output_path = render_session(_session)
            out += f"*   Session graph: '{output_path}'\n"
        except graphviz.backend.execute.ExecutableNotFound:
            out += (
                "*   No session graph was rendered; Graphviz is not installed. "
                "See the README.md file for instructions."
            )

        # Add an empty line at the end:
        out += "\n"

    return out


def get_file_contents_if_it_exists(relative_path: str, alt_text="") -> str:
    """Returns the contents of a file, if it can be found

    Returns the alt text if the file is not found.
    """
    script_location = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_location, relative_path)
    if os.path.exists(file_path):
        with open(file_path, "r") as _file:
            return _file.read()
    else:
        return alt_text


def compile_summary() -> str:  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
    """Return a multiline string containing summary data"""
    actions_visited_count = 0
    actions_with_errors = []
    states_visited_count = 0
    states_with_errors = []
    total_actions_failed_count = 0
    total_actions_flaky_count = 0
    total_actions_count = 0
    total_states_count = 0
    total_states_failed_count = 0
    total_states_flaky_count = 0
    total_transitions_count = 0
    total_transitions_visited_count = 0
    transitions_visited_count = 0

    for _session in SESSIONS:
        _summary = _session.machine.summary
        # Actions:
        total_actions_count += _summary.actions_count
        actions_visited_count += len(_summary.visited_actions)
        total_actions_failed_count += len(_summary.failed_actions)
        total_actions_flaky_count += len(_summary.flaky_actions)
        for action_name in _summary.failed_actions:
            actions_with_errors.append(
                f"{_session.name}, FAILED ACTION: {action_name} "
                f"{_summary.results.actions[action_name].short_summary}"
            )
        for action_name in _summary.flaky_actions:
            actions_with_errors.append(
                f"{_session.name}, FLAKY ACTION: {action_name} "
                f"{_summary.results.actions[action_name].short_summary}"
            )
        # States:
        total_states_failed_count += len(_summary.failed_states)
        total_states_count += _summary.states_count
        total_states_failed_count += len(_summary.failed_states)
        total_states_flaky_count += len(_summary.flaky_states)
        states_visited_count += len(_summary.visited_states)
        for action_name in _summary.failed_states:
            states_with_errors.append(
                f"{_session.name}, FAILED STATE: {action_name} "
                f"{_summary.results.states[action_name].short_summary}"
            )
        for action_name in _summary.flaky_states:
            states_with_errors.append(
                f"{_session.name}, FLAKY STATE: {action_name} "
                f"{_summary.results.states[action_name].short_summary}"
            )
        # Transitions:
        total_transitions_count += _summary.transitions_count
        transitions_visited_count += len(_summary.visited_transitions)
        total_transitions_visited_count += _summary.total_transitions_visits_count

    action_coverage = (
        round(100 * actions_visited_count / total_actions_count) if total_actions_count else 100
    )
    duration = RESULTS.get("total_exec_time", 0)
    state_coverage = (
        round(100 * states_visited_count / total_states_count) if total_states_count else 100
    )
    sessions_count = len(SESSIONS)
    total_states_visited = (
        (total_transitions_visited_count + 1) if SESSIONS else 0
    )  # Include the initial state
    transition_coverage = (
        round(100 * transitions_visited_count / total_transitions_count)
        if total_transitions_count
        else 100
    )
    transitions_per_second = total_transitions_visited_count / duration if duration > 0 else "N/A"
    try:
        states_per_second = round(transitions_per_second, 2)
    except TypeError:
        states_per_second = "N/A"
    try:
        states_per_session_and_second = (
            round(transitions_per_second / sessions_count, 2) if sessions_count else 0
        )
    except TypeError:
        states_per_session_and_second = "N/A"

    supplemental_action_info = ""
    if total_actions_failed_count > 0:
        supplemental_action_info += f"FAILED: {total_actions_failed_count} "
    if total_actions_flaky_count > 0:
        supplemental_action_info += f"FLAKY: {total_actions_flaky_count}"
    if supplemental_action_info != "":
        supplemental_action_info = f" - {supplemental_action_info}"

    supplemental_state_info = ""
    if total_states_failed_count > 0:
        supplemental_state_info += f"FAILED: {total_states_failed_count} "
    if total_states_flaky_count > 0:
        supplemental_state_info += f"FLAKY: {total_states_flaky_count}"
    if supplemental_state_info != "":
        supplemental_state_info = f" - {supplemental_state_info}"

    # pylint: disable=line-too-long
    out = ""
    out += f"  MODULE: {WHAT_TO_RUN}\n"
    out += "\n"
    out += f"  Total execution time........: {round(duration) if duration > 0 else 'N/A'}s\n"
    out += f"  Number of sessions..........: {sessions_count}\n"
    out += f"  Unique states visited.......: {states_visited_count} of {total_states_count} ({state_coverage}%) {supplemental_state_info}\n"
    out += f"  Unique actions visited......: {actions_visited_count} of {total_actions_count} ({action_coverage}%) {supplemental_action_info}\n"
    out += f"  Unique transitions visited..: {transitions_visited_count} of {total_transitions_count} ({transition_coverage}%)\n"
    out += f"  Total number of states visited.....: {total_states_visited}\n"
    out += f"  Total number of states per second..: {states_per_second}\n"
    out += f"  States per session and second......: {states_per_session_and_second}\n"
    # pylint: enable=line-too-long

    if actions_with_errors:
        out += "\n  " + "\n  ".join(actions_with_errors) + "\n"
    if states_with_errors:
        out += "\n  " + "\n  ".join(states_with_errors) + "\n"
    return out


def parse_arguments(*args) -> argparse.Namespace:
    # Configure the argument parser:
    parser = argparse.ArgumentParser("main.py")

    subparsers = parser.add_subparsers()
    run_parser = subparsers.add_parser("run", help="Run a Magpie test")
    run_parser.add_argument("MODULE")
    run_parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run web browser(s) in the backgound",
    )

    ide_parser = subparsers.add_parser("ide", help="Open the Magpie model IDE")
    ide_parser.add_argument("ACTOR")
    ide_parser.add_argument(
        "--port",
        type=int,
        default=8888,
        help="Magpie IDE webserver port (default=8888)",
    )

    # Parse input arguments
    return parser.parse_args(*args)


def print_logo():
    """Print logo, if present"""
    logo = get_file_contents_if_it_exists("magpie_logo.txt")
    if logo:
        LOGGER.info(logo)


def print_version_info():
    # TODO: This assumes that magpie_core is a submodule to the magpie repo.
    #        Should be handled differently.

    # Print version info:
    magpie_core_dir = Path(__file__).parent
    try:
        local_magpie_version = get_version_string(magpie_core_dir.parent)
    except (GitNotFoundError, FileNotFoundError):
        local_magpie_version = "-- No version found --"
    try:
        local_magpie_core_version = get_version_string(magpie_core_dir)
    except (GitNotFoundError, FileNotFoundError):
        local_magpie_core_version = "-- No version found --"
    magpie_version_info = get_file_contents_if_it_exists(
        ".MAGPIE_VERSION", local_magpie_version
    ).replace("\n", "")
    magpie_core_version_info = get_file_contents_if_it_exists(
        ".MAGPIE_CORE_VERSION", local_magpie_core_version
    ).replace("\n", "")
    LOGGER.info("  Versions:")
    LOGGER.info("  ---------")
    LOGGER.info("  magpie..........: %s", magpie_version_info)
    LOGGER.info("  magpie_core.....: %s", magpie_core_version_info)


def action_error_messages_for_azure_devops(
    actions: Dict[str, Action], ci_test_spec_display_name: str, session: Session, result_type: str
) -> List[str]:
    """Return formatted error messages for Azure DevOps from failed/flaky actions"""
    # TODO: Add file reference at the end of each failed action log line?
    _err_msg = []
    for action_name in actions.keys():
        short_summary = session.machine.summary.results.actions[action_name].short_summary
        _err_msg.append(
            "##vso[task.logissue type=error;] "
            f"{ci_test_spec_display_name} - {session.name}, "
            f"{result_type.upper()} ACTION: {action_name} {short_summary}"
        )
    return _err_msg


def state_error_messages_for_azure_devops(
    states: Dict[str, State], ci_test_spec_display_name: str, session: Session, result_type: str
) -> List[str]:
    """Return formatted error messages for Azure DevOps from failed/flaky states"""
    # TODO: Add file reference at the end of each failed state log line?
    _err_msg = []
    for state_name in states.keys():
        short_summary = session.machine.summary.results.states[state_name].short_summary
        _err_msg.append(
            "##vso[task.logissue type=error;] "
            f"{ci_test_spec_display_name} - {session.name}, "
            f"{result_type.upper()} STATE: {state_name} {short_summary}"
        )
    return _err_msg


def print_test_summary(module: str, outputdir: str, ci_mode: str = "off"):
    # Print the test summary:
    sessions_info = compile_sessions_info()
    summary = compile_summary()
    test_summary = ""
    test_summary += SESSIONS_ASCII if SESSIONS else ""
    test_summary += sessions_info
    test_summary += SUMMARY_ASCII
    test_summary += "\n" + "-" * 79 + "\n"
    test_summary += summary
    test_summary += "-" * 79 + "\n\n"
    LOGGER.info("Summarizing test round...\n%s", test_summary)

    # Write to markdown summary file, if in CI:
    if ci_mode == "on":
        test_spec_base_name, _ = os.path.splitext(os.path.basename(module))
        summary_name = f"{test_spec_base_name}_summary.md"
        summary_path = os.path.join(outputdir, summary_name)
        with open(summary_path, "w") as summary_file:
            summary_file.write(f"```\n{summary}\n```")


def send_test_issues_info_to_azure_devops(ci_test_spec_display_name: str, ci_mode: str = "off"):
    # Log errors etc:
    if ci_mode == "on":
        err_msg = []
        for session in SESSIONS:
            err_msg += action_error_messages_for_azure_devops(
                session.machine.summary.failed_actions, ci_test_spec_display_name, session, "failed"
            )
            err_msg += action_error_messages_for_azure_devops(
                session.machine.summary.flaky_actions, ci_test_spec_display_name, session, "flaky"
            )
            err_msg += state_error_messages_for_azure_devops(
                session.machine.summary.failed_states, ci_test_spec_display_name, session, "failed"
            )
            err_msg += state_error_messages_for_azure_devops(
                session.machine.summary.flaky_states, ci_test_spec_display_name, session, "flaky"
            )
        if err_msg:
            LOGGER.info(
                "CI mode is on: let Azure DevOps know about failed states and flaky states:\n%s",
                "\n".join(err_msg),
            )


########
# MAIN
#
def main():
    parsed_args = parse_arguments(sys.argv[1:])

    if hasattr(parsed_args, "ACTOR"):
        # Start the Magpie IDE and exit:
        magpie_ide_main(parsed_args.ACTOR, parsed_args.port)
        sys.exit(0)

    print_logo()

    LOGGER.info("-" * 79)

    LOGGER.info("  Command line arguments used:")
    LOGGER.info("  ----------------------------")
    LOGGER.info("    %s", " ".join(sys.argv[1:]))
    LOGGER.info("")

    print_version_info()

    # Get information from environmental variables:
    ci_mode = os.environ.get("CIMODE", "off")
    ci_test_spec_display_name = os.environ.get("TESTSPECDISPLAYNAME", "Unknown")
    host = os.environ.get("HOST")
    magpie_timeout = int(os.environ.get("MAGPIE_TIMEOUT", 5000))
    outputdir = os.environ.get("OUTPUTDIR", os.path.join(".", "output"))
    LOGGER.info("")
    LOGGER.info("  Environment variables:")
    LOGGER.info("  ----------------------")
    LOGGER.info("  CIMODE...............: %s", ci_mode)
    LOGGER.info("  HOST.................: %s", host)
    LOGGER.info("  MAGPIE_TIMEOUT.......: %s", magpie_timeout)
    LOGGER.info("  OUTPUTDIR............: %s", outputdir)

    # Run the test file:
    LOGGER.info("-" * 79)
    sys.path.append(os.getcwd())
    try:
        exit_code = run(parsed_args.MODULE, parsed_args.headless)
    except RuntimeError:
        LOGGER.warning(
            "WARNING: All operations on the page did not finish. "
            "The forced shutdown may cause side effects!"
        )
        exit_code = 1

    send_test_issues_info_to_azure_devops(ci_test_spec_display_name, ci_mode)
    print_test_summary(parsed_args.MODULE, outputdir, ci_mode)

    # Exit with exit code
    LOGGER.info("Exiting with exit code %s", exit_code)

    sys.exit(exit_code)


if __name__ == "__main__":
    check_playwright_compatibility()
    main()
