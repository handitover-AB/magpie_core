"""Settings for FSM execution"""

from enum import Enum, auto


class Strategy(Enum):
    """Specify the different execution options for the FSM"""

    HappyPath = auto()  # pylint: disable=invalid-name
    ShortestPath = auto()  # pylint: disable=invalid-name
    FullCoverage = auto()  # pylint: disable=invalid-name
    PureRandom = auto()  # pylint: disable=invalid-name
    SmartRandom = auto()  # pylint: disable=invalid-name
    Random = auto()  # pylint: disable=invalid-name
