"""A very simple http - sqlcmd command bridge"""
import http.server
import os
import json
import logging
import signal
import socketserver
import subprocess
import sys

import urllib.parse

from pathlib import Path
from typing import List



############
# DEFAULTS
#
OUTPUTDIR = os.environ.get("OUTPUTDIR", ".")
PORT = 80
SQL_SERVER_HOST = os.environ.get("MAGPIE_DBPROXY_SQL_SERVER_HOST")
SQL_SERVER_USER = os.environ.get("MAGPIE_DBPROXY_SQL_SERVER_USER")
SQL_SERVER_PASSWORD = os.environ.get("MAGPIE_DBPROXY_SQL_SERVER_PASSWORD")
SQL_SERVER_DBNAME = os.environ.get("MAGPIE_DBPROXY_SQL_SERVER_DBNAME")
PASSWORD_FOR_HUMANS = "***** (hey, it's secret, right?)" if SQL_SERVER_PASSWORD else "NOT SET!"
SEPARATOR_CHAR = ","


# To create ASCII big letters:
# http://www.patorjk.com/software/taag/#p=display&f=Standard&t=Magpie%20dbproxy

STARTUP_STRING = rf"""
               ::---:.
           -+#%%#####%%*=:
      .+%############*++*###-
     .#############+:=**+:=##%
    .%############*:#  ###==##+
   :%#############==#######:###%===-.
   +###############-=####*:*###********+-.
   +################*----+##%%************+=.
   +#######################%#################-
:-+*%###########################%#===----´´´
##%%%%%%%%%%%%%%%%############%.     __  __                   _
%%%#+=:..    .:-=%%%%##########     |  \/  | __ _  __ _ _ __ (_) ___
+-.              :+#%#%#######%.    | |\/| |/ _` |/ _` | '_ \| |/ _ \
                   :##%%######%:    | |  | | (_| | (_| | |_) | |  __/
                    +###%######:    |_|  |_|\__,_|\__, | .__/|_|\___/
                     +###%######                  /___/|_|                             
                                     _ _                               
                                  __| | |__  _ __  _ __ _____  ___   _ 
                                 / _` | '_ \| '_ \| '__/ _ \ \/ / | | |
                                | (_| | |_) | |_) | | | (_) >  <| |_| |
                                 \__,_|_.__/| .__/|_|  \___/_/\_\\__, |
                                            |_|                  |___/ 

Using environment variables to find the database server with which to connect:
    MAGPIE_DBPROXY_SQL_SERVER_HOST        the host address and port to use, e.g. "localhost:1433"
    MAGPIE_DBPROXY_SQL_SERVER_USER        the user name, e.g. "sa"
    MAGPIE_DBPROXY_SQL_SERVER_PASSWORD    the password, e.g. "MyS3cretP4ssw0rd"
    MAGPIE_DBPROXY_SQL_SERVER_DBNAME      the database name, e.g. "master"

Current settings:
    MAGPIE_DBPROXY_SQL_SERVER_HOST        {SQL_SERVER_HOST}
    MAGPIE_DBPROXY_SQL_SERVER_USER        {SQL_SERVER_USER}
    MAGPIE_DBPROXY_SQL_SERVER_PASSWORD    {PASSWORD_FOR_HUMANS}
    MAGPIE_DBPROXY_SQL_SERVER_DBNAME      {SQL_SERVER_DBNAME}


Send a query (example):
  curl -X GET "http://.../sql?q=<URLENCODED SQL QUERY>"
"""


def get_logger() -> logging.Logger:
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.INFO)
    log_file = Path(OUTPUTDIR) / "magpie_dbproxy.log"

    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(threadName)s] - %(message)s")
    handler.setFormatter(formatter)
    _logger.handlers = [handler]

    return _logger


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        self.logger = get_logger()
        super().__init__(*args, **kwargs)

    def _send_response(self, code, msg: str, content_type: str = "text/plain"):
        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(msg.encode("utf-8"))

        output = str(msg)[:77].replace("\n", r"\n")
        if len(output) == 77:
            output += "..."
        self.logger.info("--> [%s] %s", code, output)

    def _run_command_and_send_response(self, cmd: List[str], raw_text: bool = False) -> None:
        try:
            result_raw = subprocess.run(cmd, capture_output=True, check=False)
        except FileNotFoundError as exc:
            self._send_response(500, str(exc))
            self.logger.info("500: %s", str(exc))
            return

        stderr = result_raw.stderr.decode("utf-8")
        stdout = result_raw.stdout.decode("utf-8")
        if stderr:
            self._send_response(500, stderr)
            self.logger.error("STDERR:\n%s", stderr)
            return

        if raw_text:
            self._send_response(200, stdout)
            return

        lines = stdout.split("\n")
        fields = lines[0].split(SEPARATOR_CHAR)
        out_list = []
        for line in lines[2:-3]:
            out_list.append(dict(zip(fields, line.split(SEPARATOR_CHAR))))
        self._send_response(200, json.dumps(out_list), "application/json")

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_dict = urllib.parse.parse_qs(parsed_url.query)
        query_expr = query_dict.get("q")
        file_expr = query_dict.get("file")
        host = SQL_SERVER_HOST

        self.logger.info("<-- %s", self.path)

        cmd_args = (
            ["/opt/mssql-tools/bin/sqlcmd"]
            + ["-S", host.replace(":", SEPARATOR_CHAR)]
            + ["-U", SQL_SERVER_USER]
            + ["-P", SQL_SERVER_PASSWORD]
            + ["-s", SEPARATOR_CHAR]
            + ["-W"]
            + ["-C"]
        )

        # Routing:
        raw_text = False
        extra_args = []
        query = ""
        file_path = ""
        # Health route:
        if self.path == "/health":
            self._send_response(200, "Healthy")
            return

        # Root route / index route:
        if self.path in ("/", "/index", "/index.html"):
            self._send_response(200, STARTUP_STRING)
            return

        # Other routes:
        if self.path.startswith("/sql"):
            extra_args = ["-d", SQL_SERVER_DBNAME]
            if query_expr:
                query = query_expr[0]
            elif file_expr:
                file_path = str(Path("/opt/dbproxy/sql") / file_expr[0])

            if query:
                extra_args += ["-Q", query]
            elif file_path:
                extra_args += ["-i", file_path]
            else:
                msg = "Malformed url. One of the query parameters 'q' or 'file' must be provided."
                self._send_response(400, msg)
                return

            # Run the db command and send the response:
            if extra_args:
                self._run_command_and_send_response(cmd_args + extra_args, raw_text)
            else:
                super().do_GET()
        else:
            self._send_response(404, "Not Found")
            return


def shutdown_handler(*_):
    """Tell the user that the application is shutting down"""
    logger.info("Shutdown requested. Shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    logger = get_logger()
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        logger.info(STARTUP_STRING)
        logger.info("Serving on localhost:80 inside the Docker container")
        logger.info("Expected location for the database server: %s", SQL_SERVER_HOST)
        logger.info("-----")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("\nUser pressed Ctrl+C. Shutting down...")
            sys.exit(0)
