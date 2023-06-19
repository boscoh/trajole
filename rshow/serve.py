import logging
import json
from pathlib import Path

import uvicorn
from rshow.make_app import make_app
from rshow.server.lounge import handlers

# Entry point of lounge web-server

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger("root").setLevel(logging.WARNING)
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.INFO)

client_dir = Path(__file__).resolve().parent / "server/lounge/client"

port_json = Path(__file__).resolve().parent.parent / "config" / "port.json"
port = json.load(open(port_json)).get("port")

app = make_app(handlers, client_dir)
logger.info(f"start rshow server on port {port}")
uvicorn.run(app, port=port, log_level="critical")
