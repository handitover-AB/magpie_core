"""Do a simple internet search"""
import actors
from actors.todo.common.util import start_test_env, stop_test_env

from app import Strategy
from app.sessions import Session


def test_setup():
    start_test_env()


def test_teardown():
    stop_test_env()


# Actors

prodcuer1 = Session(
    name="Margaret - producer (chrome)",
    actor_module=actors.todo.todo_producer,
    browser="chromium",
    max_run_time_s=5,
    strategy=Strategy.SmartRandom,
)

consumer1 = Session(
    name="Magnus the consumer",
    actor_module=actors.todo.todo_consumer,
    browser="chromium",
    max_run_time_s=10,
    strategy=Strategy.SmartRandom,
)
