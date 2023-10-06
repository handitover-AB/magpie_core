import argparse
import webbrowser
from pathlib import Path
from threading import Thread
from typing import List

import werkzeug
from flask import Flask, jsonify, render_template, request, send_from_directory

from app.parser import FileParser, ParsingError
from app.fsm.model import ModelError


flask_app = Flask(__name__)
path = Path(__file__)


class Colors:
    # From https://flatcolors.net
    Red = "#C82647"
    Green = "#97CE68"
    Orange = "#EB9532"
    White = "#FFFFFF"
    Dark = "#333333"
    Light = "#E7E7E7"


class Model:
    def __init__(self, actor: str) -> None:
        self.model_path = ""
        if actor == "null":
            return
        actor = actor.replace("/", ".").replace("\\", ".").replace("tests.actors.", "")
        model_file = f"tests.actors.{actor}.model".replace(".", "/")
        model_path = Path(model_file)
        if not model_path.exists():
            raise FileNotFoundError(f"I looked hard, but couldn't find the file {model_path}")
        self.model_path = model_path
        self.errors: List[str] = []
        self.actor_name = actor
        self.check_model()

    def check_model(self):
        parser = FileParser()
        self.errors = []
        try:
            self.model = parser.parse(self.model_path)
            self.model.name = self.actor_name
        except (ParsingError, ModelError) as err:
            self.errors = []
            for error in str(err).split("\n"):
                if error != "":
                    # Strip away path from error:
                    self.errors.append(error.lstrip(f'"{self.model_path}",').strip())

    def get_source(self) -> str:
        """Read the model file and return its contents"""
        if not self.model_path:
            return ""

        with open(self.model_path, "r") as f:
            contents = f.read()
            self.check_model()
        return contents

    def update_source(self, source: str):
        """Save new contents"""
        if not self.model_path:
            return ""

        with open(self.model_path, "w") as f:
            f.write(source)
            self.check_model()

    def to_dot(self) -> str:
        """Converts a Magpie actor model to dot DiGraph"""
        if not self.model_path:
            return ""
        return self.model.to_dot()


###########
# WEB APP
#
@flask_app.route("/")
@flask_app.route("/index.html")
def home():
    return render_template("index.html")


@flask_app.route("/js/<path:libpath>")
def send_js(libpath):
    return send_from_directory(path.parent / "js", libpath)


@flask_app.route("/api/model/<path:actor>", methods=["GET"])
def get_model(actor):
    model = Model(actor)
    data = {
        "source": model.get_source(),
        "dot": model.to_dot(),
        "errors": model.errors,
    }
    return jsonify(data)


@flask_app.route("/api/model/<path:actor>", methods=["PUT"])
def save_model(actor):
    print("SAVE", actor)
    source = request.form.get("source", "")
    model = Model(actor)
    model.update_source(source)
    return "OK"


def start_server(port: int):
    # Monkey-patching
    #
    # Patch the log_startup function in order to hide
    # the warning message that a WSGI server should be used
    # in a production environment. The intended use of this
    # application is to serve a single user, so we won't run
    # into any issues.
    werkzeug.serving.BaseWSGIServer.log_startup = lambda *_: None
    # Now, start the server:
    flask_app.run(port=port)


def main(actor: str, port: int):
    server_thread = Thread(target=start_server, args=(port,))
    server_thread.start()

    actor = actor.replace("/", ".").replace("\\", ".")
    actor = actor.replace("tests.actors.", "")
    print(f"Listening on port {port}")
    print(f"Opening http://localhost:{port}/?actor={actor} in your default browser")
    webbrowser.open(f"http://localhost:{port}/?actor={actor}")

    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\nUser pressed CTRL+C. I'll stop now, bye-bye 👋")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Start a webserver to offer online-rendered graphs from models."
    )
    parser.add_argument(
        "actor",
        metavar="ACTOR",
        type=str,
        help="the actor whose model should be rendered.",
    )
    parser.add_argument("--port", type=int, default=8888, help="webserver port (default=8888)")
    args = parser.parse_args()
    main(args.actor, args.port)
