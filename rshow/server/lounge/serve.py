import inspect
import json
import logging
import shutil
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from urllib.request import urlopen

import handlers
import uvicorn
from addict import Dict
from docopt import docopt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app_dir = Path(__file__).resolve().parent.parent.parent.parent
client_dir = Path(__file__).resolve().parent / "client"

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.post("/rpc-run")
async def rpc_run(data: dict):
    job_id = data.get("id", None)
    method = data.get("method")
    params = data.get("params", [])
    try:
        if not hasattr(handlers, method):
            raise Exception(f"rpc-run {method} is not found")
        fn = getattr(handlers, method)
        if inspect.iscoroutinefunction(fn):
            result = await fn(*params)
        else:
            result = fn(*params)
        logger.debug(f"rpc-run {method}")
        return {"result": result, "jsonrpc": "2.0", "id": job_id}
    except Exception as e:
        for line in str(traceback.format_exc()).splitlines():
            logger.debug(line)
        return {
            "error": {"code": -1, "message": str(e)},
            "jsonrpc": "2.0",
            "id": job_id,
        }


@app.get("/")
async def serve_index(request: Request):
    return FileResponse(client_dir / "index.html")


# All other calls diverted to static files
app.mount("/", StaticFiles(directory=client_dir), name="dist")


def open_url_in_background(url, sleep_in_s=1):
    """
    Polls server in background thread then opens a url in webbrowser
    """

    def inner():
        elapsed = 0
        while True:
            try:
                response_code = urlopen(url).getcode()
                if response_code < 400:
                    logger.info(f"open_url_in_background success")
                    webbrowser.open(url)
                    return
            except:
                time.sleep(sleep_in_s)
                elapsed += sleep_in_s
                logger.info(f"open_url_in_background waiting {elapsed}s")

    # creates a thread to poll server before opening client
    logger.debug(f"open_url_in_background searching {url}")
    threading.Thread(target=inner).start()


def run_from_config(in_config):
    """
    in_config:
      filename: str - file/folder for trajectory
      is_dev: bool - prevents client from killing server and no open open url
      is_solvent: bool - loads waters in trajectory
      is_hydrogen: bool - hydrogen
    """
    if in_config.is_dev:
        config_json = app_dir / "config" / "config.dev.json"
    else:
        config_json = app_dir / "config" / "lounge.config.prod.json"
    client_config_json = app_dir / "config" / "config.json"
    if client_config_json.exists():
        client_config_json.unlink()
    shutil.copy(config_json, client_config_json)

    config = Dict(json.load(open(config_json)))
    config.update(in_config)
    logger.info(f"start h5 server {json.dumps(config, indent=2)}")

    if not config.is_dev:
        open_url_in_background(f"http://{config.host}:{config.port}")

    handlers.config = config
    uvicorn.run(app, port=config.port, host=config.host, log_level="critical")


__doc__ = """
serve.py
Usage:
  serve.py [-cws] [<work_dir>]

Options:
  -h --help     Show this screen.
  -c            Run server continuously
  -w            Don't open url
  -s            Keep solvent
  -d            Keep hydrogens
"""


if __name__ == "__main__":
    args = docopt(__doc__)
    config = Dict()
    config.is_dev = args.get("-c")
    config.is_solvent = args.get("-s")
    config.is_hydrogen = args.get("-d")
    config.background = "#CCC"
    config.port = 9023
    config.command = "FoamTrajStream"
    config.foam_id = 15
    if args.get("<work_dir>"):
        filename = str(Path(args.get("<work_dir>")).resolve())
    else:
        filename = ""
    run_from_config(config)
