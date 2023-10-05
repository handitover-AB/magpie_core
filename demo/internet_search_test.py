"""Do a simple internet search"""
import actors

from app import Strategy
from app.actors.model_based_actor import ModelBasedActor
from app.sessions import Session


maggie_actor = ModelBasedActor(actor_module=actors.internet_searcher)


maggie = Session(
    name="Maggie the Magpie",
    actor=maggie_actor,
    browser="chromium",
    max_run_time_s=10,
    strategy=Strategy.SmartRandom,
)
