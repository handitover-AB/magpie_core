"""Implement a parser for model files"""
from __future__ import annotations

import re
import os

from pathlib import Path
from typing import List, Set, Tuple

from app.fsm.model import Model, ModelError
from app.fsm.transition import Arrow, Transition


##################
# UTIL FUNCTIONS
#
def friendly_number(num: int) -> str:
    word = [
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
    ]
    if num < 20:
        return word[num]
    return str(num)


def plural(num: int) -> str:
    return "s" if num >= 1 else ""


def remove_quotation_marks(string: str) -> str:
    return string.lstrip('"').rstrip('"').lstrip("'").rstrip("'")


#####################
# CUSTOM EXCEPTIONS
#
class ParsingError(Exception):
    """Raise when parsing goes wrong"""


################
# HELP CLASSES
#
class ModelRowParts:
    """Data structure for model row parts"""

    def __init__(
        self,
        start_state_name: str = "",
        condition_name: str = "",
        action_name: str = "",
        arrow_string: str = "",
        end_state_name: str = "",
    ) -> None:
        self.start_state_name = start_state_name
        self.condition_name = condition_name
        self.action_name = action_name
        self.arrow_string = arrow_string
        self.end_state_name = end_state_name

    def __iter__(self):
        yield self.start_state_name
        yield self.condition_name
        yield self.action_name
        yield self.arrow_string
        yield self.end_state_name

    def __str__(self):
        return "  ".join(list(self))


###########
# PARSERS
#
class FileParser:
    """Implement the actual file parser"""

    @staticmethod
    def parts_from_row(  # pylint: disable=too-many-locals
        model_row: str,
    ) -> Tuple[ModelRowParts, List[str]]:
        """Break a model row into parts, separated by at least two spaces"""

        def _is_comment(string: str) -> bool:
            return string.lstrip().startswith("#")

        def _is_conditional(string: str) -> bool:
            return (
                string.startswith("[")
                and string.endswith("]")
                and "'" not in string.lstrip("'").rstrip("'")
                and '"' not in string.lstrip('"').rstrip('"')
            )

        def _is_stringlike(string: str) -> bool:
            """States and actions are similar"""
            filtered_string = string.lstrip('"').rstrip('"')
            return not _is_arrow(string) and '"' not in filtered_string and string != ""

        def _is_arrow(string: str) -> bool:
            arrows = [item.value for item in Arrow]
            return string in arrows

        line_errors: List[str] = []
        output_parts = ModelRowParts()

        # Split the model row into segments separated
        # by two spaces or more:
        parts: List[str] = re.sub(r"\s\s+", "  ", model_row.strip("\n")).split("  ")
        if _is_comment(model_row) or parts == [""]:
            # Empty line
            return output_parts, []

        #################################
        # ROW PARSER
        #
        # Check validity of row parts:
        number_of_parts = len(parts)
        model_row: ModelRowParts = ModelRowParts()

        valid_patterns = [
            (_is_stringlike, _is_arrow, _is_stringlike),
            (_is_stringlike, _is_stringlike, _is_arrow, _is_stringlike),
            (
                _is_stringlike,
                _is_conditional,
                _is_stringlike,
                _is_arrow,
                _is_stringlike,
            ),
        ]

        # Check patterns:
        is_ok = False
        if 3 <= number_of_parts <= 5:
            valid_pattern = valid_patterns[number_of_parts - 3]
            is_ok = all((fn(parts[idx]) for idx, fn in enumerate(valid_pattern)))

            if is_ok:
                if number_of_parts == 3:
                    model_row: ModelRowParts = ModelRowParts(
                        start_state_name=remove_quotation_marks(parts[0]),
                        arrow_string=parts[1],
                        end_state_name=remove_quotation_marks(parts[2]),
                    )
                elif number_of_parts == 4:
                    model_row: ModelRowParts = ModelRowParts(
                        start_state_name=remove_quotation_marks(parts[0]),
                        action_name=remove_quotation_marks(parts[1]),
                        arrow_string=parts[2],
                        end_state_name=remove_quotation_marks(parts[3]),
                    )
                elif number_of_parts == 5:
                    model_row: ModelRowParts = ModelRowParts(
                        start_state_name=remove_quotation_marks(parts[0]),
                        condition_name=remove_quotation_marks(parts[1].lstrip("[").rstrip("]")),
                        action_name=remove_quotation_marks(parts[2]),
                        arrow_string=parts[3],
                        end_state_name=remove_quotation_marks(parts[4]),
                    )
            else:
                # There has to be exactly one arrow:
                allowed_arrows = (" or ").join([item.value for item in Arrow])
                arrows_count = list(map(_is_arrow, parts)).count(True)
                if arrows_count == 0:
                    line_errors.append(
                        f"There has to be an arrow on each line. "
                        f"Please add one of these: {allowed_arrows}"
                    )
                elif arrows_count > 1:
                    line_errors.append(
                        "There has to be exactly one arrow on each line. "
                        f"Please remove {arrows_count - 1} arrow{plural(arrows_count - 1)}."
                    )

                # Conditionals are optional but there can't be more than one conditional:
                conditionals = list(map(_is_conditional, parts))
                conditionals_count = conditionals.count(True)
                if conditionals_count > 1:
                    line_errors.append(
                        "There can't be more than one conditional on each line. "
                        f"This line has {friendly_number(conditionals_count)} conditionals."
                    )
        else:
            # Inform about the correct number of items
            if number_of_parts < 3:
                line_errors.append("Too few items, review your syntax and add the missing parts.")
            elif number_of_parts > 5:
                line_errors.append(
                    "Too many items, review your syntax and delete the superfluous parts."
                )

        return model_row, line_errors

    def parse(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        self, file_path: str
    ) -> Model:
        """Construct a model object from a model file"""
        model = Model()
        model_errors: List[Tuple[int, str]] = []
        all_action_names: Set[str] = set()
        all_condition_names: Set[str] = set()
        all_state_names: Set[str] = set()
        model_parts: List[ModelRowParts] = []
        initial_state_name: str = ""
        template: str = ""

        if not os.path.exists(file_path):
            raise ParsingError(f"File not found: {file_path}")
        template = Path(file_path).read_text()

        # Iterate over all lines in the template string
        # and create string representations of objects that
        # eventually should be created:
        for line_no, row in enumerate(template.split("\n"), start=1):
            # Replace tabs with spaces:
            processed_row = row.replace("\t", "    ")
            # Remove leading spaces:
            processed_row = processed_row.lstrip(" ")
            # Remove newline character:
            processed_row = processed_row.rstrip("\n")
            # Remove trailing spaces:
            processed_row = processed_row.rstrip(" ")
            row, line_errors = self.parts_from_row(processed_row)

            # Check if there were errors:
            if line_errors:
                for line_error in line_errors:
                    model_errors.append((line_no, line_error))
                continue  # Go to next line

            # No errors, go on...
            # If nothing was returned from the parser,
            # go to the next line:
            if "".join(row) == "":
                continue

            # Add action name to action names set.
            # Actions are optional, so we need to
            # only add the name if it is truthy:
            if row.action_name:
                all_action_names.add(row.action_name)

            # Add condition name to condition names set.
            # Conditions are optional, so we need to
            # only add the name if it is truthy:
            if row.condition_name:
                all_condition_names.add(row.condition_name)

            # Add state names to state names set:
            all_state_names.add(row.start_state_name)
            all_state_names.add(row.end_state_name)
            # Set start state if not set:
            if not initial_state_name:
                initial_state_name = row.start_state_name

            model_parts.append(row)

        # Iteration finished, create objects from string representations

        # Create objects:
        for action_name in all_action_names:
            model.add_action(action_name)

        for condition_name in all_condition_names:
            model.add_condition(condition_name)

        for state_name in all_state_names:
            model.add_state(state_name)

        # Create transitions, map states and actions to them and add them to the model:
        for line_no, row in enumerate(model_parts, start=1):
            transition = Transition()
            transition.source_code_file = file_path
            transition.source_code_line = line_no
            if row.start_state_name:
                transition.start_state = model.states[row.start_state_name]
            if row.condition_name:
                transition.condition = model.conditions[row.condition_name]
            if row.action_name:
                transition.action = model.actions[row.action_name]
            # TODO: Add support for probabilities here
            if row.arrow_string == Arrow.HappyPath.value:
                transition.happy_path = True
            if row.end_state_name:
                transition.end_state = model.states[row.end_state_name]
            try:
                model.add_transition(transition)
            except ModelError:
                start_state_name = transition.start_state.name if transition.start_state else ""
                end_state_name = transition.end_state.name if transition.end_state else ""
                # TODO: Below - add action and condition to the information:
                line_error = (
                    f"Duplicate transition, "
                    f"only one transition between `{start_state_name}` and "
                    f"`{end_state_name}` is allowed. Remove the superfluous one(s)."
                )
                model_errors.append((line_no, line_error))

        # set start state of model:
        if initial_state_name:
            model.initial_state = model.states[initial_state_name]

        # Add links to inbound/outbound actions for states in the model:
        transitions = model.transitions.values()
        for name, state in model.states.items():
            state.inbounds = [
                trns for trns in transitions if trns.end_state and trns.end_state.name == name
            ]
            state.outbounds = [
                trns for trns in transitions if trns.start_state and trns.start_state.name == name
            ]

        # Check transitions for errors:
        for transition in model.transitions.values():
            file_path = transition.source_code_file
            line_no = transition.source_code_line
            if model.state_is_unreachable(transition.start_state):
                err_msg = (
                    f"Unreachable state: `{transition.start_state.name}`! "
                    "Please check your spelling. If correct, you need to "
                    "add a transition pointing to this state."
                )
                model_errors.append((line_no, err_msg))

        # Raise a ModelError if there are errors:
        if model_errors:
            err_msg = ""
            for line_no, line_error in sorted(model_errors):
                err_msg += f'"{file_path}", line {line_no}: {line_error}\n'
            raise ModelError(err_msg)

        # Return the model:
        return model
