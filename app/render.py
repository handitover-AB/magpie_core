"""Render graphs using Graphviz"""
from __future__ import annotations

import os

from app import OUTPUTDIR
from app.sessions import Session


def render_session(session: Session, output_path=None) -> str:  # pylint: disable=too-many-locals
    model = session.machine.model
    model.name = model.name + rf"\n{session.name}"
    summary = session.machine.summary
    output_path = output_path or OUTPUTDIR
    filename: str = os.path.join(output_path, session.name.replace(" ", "_") + ".dot")
    digraph = model.to_digraph(summary)

    return digraph.render(filename, cleanup=True, format="svg").replace("\\", "/")
