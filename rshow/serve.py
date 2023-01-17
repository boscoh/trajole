import inspect
import logging
import threading
import time
import traceback
import webbrowser
from urllib.request import urlopen

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


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


def start_fastapi_server(config, handlers, client_dir, port):
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    handlers.init(config)

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

    if client_dir:
        # All other calls diverted to static files
        app.mount("/", StaticFiles(directory=client_dir), name="dist")

    logger.info(f"start rshow server on port {port}")
    uvicorn.run(app, port=port, log_level="critical")


if __name__ == "__main__":
    from pathlib import Path
    import json
    from server.lounge import handlers
    from addict import Dict

    config = Dict(is_solvent=False, is_hydrogen=False)

    client_dir = Path(__file__).resolve().parent / "server/lounge/client"

    port_json = Path(__file__).resolve().parent.parent / "config" / "port.json"
    port = json.load(open(port_json)).get("port")

    start_fastapi_server(config, handlers, client_dir, port)




