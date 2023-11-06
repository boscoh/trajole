import logging
import json
import os
from path import Path
import sys

import uvicorn
from easytrajh5.fs import dump_yaml
from rshow.make_app import make_app
from rshow.server.lounge import handlers
from rshow.log import init_logging

# Entry point of lounge web-server

logger = logging.getLogger(__name__)

init_logging()

this_dir = Path(__file__).abspath().parent

client_dir = this_dir / "server/lounge/client"
data_dir = this_dir / "server/lounge/data"
port_json = this_dir.parent / "config" / "port.json"
port = json.load(open(port_json)).get("port")

if "--dev" in sys.argv:
    # Run in uvicorn cli using the reload facility
    # Send dev_config to app_from_dev_config.py
    os.chdir(this_dir)
    dump_yaml({"server": "lounge", "work_dir": os.getcwd()}, "dev_config.yaml")
    os.system(f"uvicorn app_from_dev_config:app --reload --port {port}")
else:
    app = make_app(handlers, client_dir, data_dir)
    logger.info(f"start rshow server on port {port}")
    uvicorn.run(app, port=port, log_level="critical")
