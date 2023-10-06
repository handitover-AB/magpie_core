"""Implement logic for models

Models keep information about states,
transitions, actions and conditions and
the relations between them.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Set

import graphviz

from app.fsm.action import Action
from app.fsm.condition import Condition
from app.fsm.state import State
from app.fsm.transition import Transition
from app.fsm.results import Result, SessionSummary, VisitsAndResults


NeighborGraph = Dict[str, Dict[str, int]]
INF = float("inf")  # represent infinity


#####################
# CUSTOM EXCEPTIONS
#
class ModelError(Exception):
    """Raise when the model contains errors"""


class PathError(Exception):
    """Raise when it is impossible to find a valid path"""


################
# HELP CLASSES
#
class MyIter:
    def __init__(self, gen_fn):
        self.gen_fn = gen_fn

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.gen_fn)


class Color:
    # From https://flatcolors.net
    Green = "#97CE68"
    Grey = "#CCCCCC"
    Red = "#C82647"
    Orange = "#EB9532"
    White = "#FFFFFF"
    Dark = "#333333"
    MediumDark = "#BBBBBB"
    Light = "#E7E7E7"


#################
# MODEL CLASSES
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


class Model:
    """Holds a potentially runnable model with states, actions and transitions"""

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.actions: Dict[str, Action] = dict()
        self.conditions: Dict[str, Condition] = dict()
        self.states: Dict[str, State] = dict()
        self.transitions: Dict[str, Transition] = dict()
        self.initial_state: State | None = None

    def state_is_unreachable(self, state: State) -> None:
        """Returns True if state has no inbound transitions, False otherwise

        Exception:
        If state is start state, it is allowed to have no inbound transitions
        """
        return len(state.inbounds) == 0 and not self.initial_state == state

    def add_action(self, action_name: str) -> None:
        """Add an action to the model if it does not already exist"""
        if action_name in self.actions:
            return
        # Add action to collection of actions:
        self.actions[action_name] = Action(action_name)

    def add_condition(self, condition_name: str) -> None:
        """Add a condition to the model if it does not already exist"""
        if condition_name in self.conditions:
            return
        # Add condition to collection of conditions:
        self.conditions[condition_name] = Condition(condition_name)

    def add_state(self, state: str) -> None:
        """Add a state to the model if it does not already exist"""
        if state in self.states:
            return
        # Add state to collection of states:
        self.states[state] = State(state)

    def add_transition(self, transition: Transition) -> None:
        """Add a transition to the model if it does not already exist"""
        if transition.name in self.transitions:
            raise ModelError("Duplicate transition")

        self.transitions[transition.name] = transition

    def shortest_path(self, start_state_name: str, end_state_name: str) -> PathGenerator:
        dijkstra = Dijkstra(self)
        return dijkstra.shortest_path(start_state_name, end_state_name)

    def to_digraph(  # pylint: disable=too-many-locals
        self, result_summary: SessionSummary | None = None
    ) -> graphviz.Digraph:
        digraph: graphviz.Digraph = graphviz.Digraph()
        digraph.attr(label=rf"&#10;&#10;{self.name}")
        digraph.attr(bgcolor=Color.Light)

        # First node:
        init_node_attrs = {
            "shape": "circle",
            "style": "filled",
            "color": Color.MediumDark,
            "fillcolor": Color.Grey,
            "height": "0.2",
            "width": "0.2",
        }
        digraph.node(".", "", **init_node_attrs)

        # Other nodes:
        for state_name in sorted(self.states):
            color = Color.White  # Default color
            font_color = Color.Dark  # Default color

            tooltip = state_name

            if result_summary:
                state_result = result_summary.results.states.get(state_name)
                color = self._get_result_color(state_result) if state_result else Color.White
                font_color = Color.Light if color == Color.Red else Color.Dark
                result_text_summary = self._get_result_text_summary(state_result)
                tooltip += rf"&#10;&#10;{result_text_summary}" if result_text_summary else ""

            node_attrs = {
                "shape": "box",
                "style": "rounded,filled",
                "color": Color.MediumDark,
                "fillcolor": color,
                "fontcolor": font_color,
                "fontsize": "12",
                "fontname": "Helvetica",
                "tooltip": tooltip,
            }
            digraph.node(state_name, state_name, **node_attrs)

        # Default settings:
        color = Color.MediumDark
        style = "solid"
        penwidth = "0.75"

        # First edge:
        if result_summary:
            first_edge_visited = (
                result_summary.results.states.get(self.initial_state.name) is not None
            )
        else:
            first_edge_visited = False

        init_edge_attrs = {
            "penwidth": "2" if first_edge_visited else penwidth,
            "color": Color.Green if first_edge_visited else color,
            "style": style,
        }
        digraph.edge(".", self.initial_state.name, **init_edge_attrs)

        # Other edges:
        for transition in self.transitions.values():
            style = "solid"
            penwidth = "0.75"
            edge_attrs = {}
            tooltip = f"Start state: {transition.start_state.name}"
            tooltip += rf"&#10;End state: {transition.end_state.name}"
            if transition.action:
                tooltip += rf"&#10;Action: {transition.action.fn_name}()"
                edge_attrs.update({"label": f"{transition.action.fn_name}()"})
            if transition.condition:
                style = "dashed"
                tooltip += rf"&#10;Condition: {transition.condition.fn_name}()"
            if result_summary:
                transition_result = result_summary.results.transitions.get(transition.name)
                if transition_result:
                    penwidth = "2"
                color = self._get_result_color(transition_result)
                result_text_summary = self._get_result_text_summary(transition_result)
                tooltip += f"&#10;&#10;{result_text_summary}" if result_text_summary else ""

            edge_attrs.update(
                {
                    "penwidth": penwidth,
                    "color": color,
                    "fontsize": "8",
                    "fontname": "Times New Roman",
                    "style": style,
                    "tooltip": tooltip.replace(r"\n", "&#10;"),
                }
            )
            digraph.edge(transition.start_state.name, transition.end_state.name, **edge_attrs)

        return digraph

    def to_dot(self, result_summary: SessionSummary | None = None) -> str:
        return self.to_digraph(result_summary).source

    @staticmethod
    def _get_result_color(result: VisitsAndResults | None) -> Color:
        """Return a color value depending on supplied execution results"""
        if not result:
            return Color.MediumDark

        not_applicable = result.has_result(Result.NOT_APPLICABLE)
        passed = result.has_result(Result.PASSED)
        failed = result.has_result(Result.FAILED)
        flaky = passed and failed

        # Select color depending on results:
        if flaky:
            return Color.Orange
        if failed:
            return Color.Red
        if passed or not_applicable:
            return Color.Green
        return Color.MediumDark

    @staticmethod
    def _get_result_text_summary(result: VisitsAndResults | None) -> Color:
        """Return a multi-line string containing a summary of the execution result"""
        if not result:
            return ""

        not_applicable = result.has_result(Result.NOT_APPLICABLE)
        passed = result.has_result(Result.PASSED)
        failed = result.has_result(Result.FAILED)
        flaky = passed and failed

        # Select color depending on results:
        if flaky:
            result_status = "FLAKY"
            result_status += rf"&#10;Passed count: {result.pass_count}"
            result_status += rf"&#10;Failed count: {result.fail_count}"
        elif failed:
            result_status = "FAILED"
            result_status += rf"&#10;Visit count: {result.fail_count}"
        elif passed:
            result_status = "PASSED"
            result_status += rf"&#10;Visit count: {result.pass_count}"
        elif not_applicable:
            result_status = f"Visit count: {result.visits_count}"

        return result_status


####################
# DIJKSTRA CLASSES
#
class NavigationStrategy(Enum):
    OPTIMISTIC = 0
    PESSIMISTIC = 1


class PathGenerator:
    def __init__(self, gen_fn):
        self.gen_fn = gen_fn
        self.strategy: NavigationStrategy | None = None

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.gen_fn)


class Dijkstra:
    """Implement functionality for deciding the shortest path through a graph

    Adapted for use with Magpie models which may have conditionals on
    transitions, making it impossible to do deterministic path generation
    before entering each state.
    """

    def __init__(self, model: Model) -> None:
        self.model = model

    def neighbor_graph(
        self, strategy: NavigationStrategy = NavigationStrategy.OPTIMISTIC
    ) -> NeighborGraph:
        """Construct a graph from the current model

         When dealing with conditionals, we may apply two strategies:
        * Optimistic strategy:
          Assume that all conditionals will be True when visiting a state
        * Pessimistic strategy:
          Assume that all conditionals will be False when visiting a state
        """
        graph = {}
        for state in self.model.states.values():
            neighbor_distances = {}
            for outbound in state.outbounds:
                if outbound.condition and strategy == NavigationStrategy.PESSIMISTIC:
                    # Do not include outbound in graph
                    continue
                key = outbound.end_state.name
                neighbor_distances.update({key: 1})
            graph.update({state.name: neighbor_distances})
        return graph

    def shortest_path(self, start_state_name: str, end_state_name: str) -> PathGenerator:

        # Guard clauses:
        if not start_state_name in self.model.states:
            raise PathError(
                f"The start state name `{start_state_name}` "
                f"was not found in the model. {self.model.states} "
                "Please check your spelling."
            )

        if not end_state_name in self.model.states:
            raise PathError(
                f"The end state name `{end_state_name}` was not found in the model. "
                "Please check your spelling."
            )

        if start_state_name == end_state_name:
            return MyIter(item for item in [])  # Return empty iterator

        ##################
        # Neighbor graph
        #
        # Step 1. See if we can guaratee a path to the end node - adopt a
        #         pessimistic strategy (assume all coditionals are False):
        path = None
        strategy = NavigationStrategy.PESSIMISTIC
        try:
            path = self._shortest_path(start_state_name, end_state_name, strategy)
        except PathError:
            pass
        # Step 2. If we did not find a graph, adopt an optimistic strategy
        #         (assume all conditionals are True)
        if not path:
            strategy = NavigationStrategy.OPTIMISTIC
            path = self._shortest_path(start_state_name, end_state_name, strategy)

        path.strategy = strategy
        return path

    def _shortest_path(
        self,
        start_state_name: str,
        end_state_name: str,
        strategy: NavigationStrategy = NavigationStrategy.OPTIMISTIC,
    ) -> PathGenerator:
        """Return an ordered list of nodes representing the path to the end node.

        The list is a PathType which behaves like a list, but has an extra attribute
        `strategy` which tells what strategy was used to find the path.

        Raise a PathError exception if no path to the end node can be found.
        """
        # Declarations:
        distances: Dict[str, float] = {}
        unvisited: Set[str] = set()
        parents = {}
        current_node = start_state_name

        # Set distances
        graph = self.neighbor_graph(strategy)
        distances = {key: INF for key in graph}
        distances[start_state_name] = 0
        unvisited = set(graph.keys())

        #############
        # Main loop
        #
        while current_node != end_state_name:
            unvisited.remove(current_node)

            for neighbor in graph[current_node].keys():
                if neighbor in unvisited:
                    new_distance = distances[current_node] + graph[current_node][neighbor]
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        parents[neighbor] = current_node

            # The new node should be the one with the shortest
            # distance among the unvisited nodes:
            current_node, _ = min(
                [(key, value) for key, value in distances.items() if key in unvisited],
                key=lambda item: item[1],
            )

        # If we could not determine a distance to the end node
        # after traversal of the graph, there is no path to
        # the end node. Notify by raising an exception:
        if distances[end_state_name] == INF:
            raise PathError(f"No path from `{start_state_name}` to `{end_state_name}`")

        path = self._get_path(end_state_name, parents)[1:]  # Skip start state
        return PathGenerator(item for item in path)

    def _get_path(self, to_node: str, parents: Dict[str, str], path=None) -> List[str]:
        """Recursively build the path from a list of parents"""
        if path is None:
            path = []
        path.insert(0, to_node)
        if to_node not in parents:
            return path
        return self._get_path(parents[to_node], parents, path)
