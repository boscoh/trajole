import inspect
import logging
import threading
import time
import traceback
import webbrowser
from io import BytesIO
from typing import Union
from urllib.request import urlopen

from rich.pretty import pprint
import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

logger = logging.getLogger(__name__)


def open_url_in_background(test_url, open_url=None, sleep_in_s=1):
    """
    Polls server in background thread then opens a url in webbrowser
    """
    if open_url is None:
        open_url = test_url

    def inner():
        elapsed = 0
        while True:
            try:
                response_code = urlopen(test_url).getcode()
                if response_code < 400:
                    logger.info(f"open_url_in_background open {open_url}")
                    webbrowser.open(open_url)
                    return
            except:
                time.sleep(sleep_in_s)
                elapsed += sleep_in_s
                logger.info(f"testing {test_url} waiting {elapsed}s")

    # creates a thread to poll server before opening client
    logger.debug(f"open_url_in_background testing {test_url} to open {open_url}")
    threading.Thread(target=inner).start()


def start_fastapi_server(handlers, client_dir, port, is_dev=False):
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
            params_str = ", ".join(repr(p) for p in params)
            logger.info(f"rpc-run {method}({params_str})")

            fn = getattr(handlers, method)
            if inspect.iscoroutinefunction(fn):
                result = await fn(*params)
            else:
                result = fn(*params)
            return {"result": result, "jsonrpc": "2.0", "id": job_id}
        except Exception as e:
            error_lines = str(traceback.format_exc()).splitlines()
            for line in error_lines:
                logger.error(line)
            return {
                "error": {"code": -1, "message": error_lines},
                "jsonrpc": "2.0",
                "id": job_id,
            }

    @app.get("/parmed/{foam_id}")
    async def get_parmed(foam_id: str, i_frame: int = None):
        try:
            logger.info(f"get_parmed {foam_id} {i_frame}")
            blob = handlers.get_parmed_blob(foam_id, i_frame)
            bytes_io = BytesIO(blob)
        except Exception as e:
            error_lines = str(traceback.format_exc()).splitlines()
            for line in error_lines:
                logger.debug(line)
            raise e
        return StreamingResponse(bytes_io, media_type="application/octet-stream")

    @app.get("/")
    async def serve_index(request: Request):
        return FileResponse(client_dir / "index.html")

    if client_dir:
        # All other calls diverted to static files
        app.mount("/", StaticFiles(directory=client_dir), name="dist")

    logger.info(f"start rshow server on port {port}")

    uvicorn.run(app, port=port, log_level="critical")


if __name__ == "__main__":
    import json
    from pathlib import Path

    from server.lounge import handlers

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("root").setLevel(logging.WARNING)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.INFO)

    client_dir = Path(__file__).resolve().parent / "server/lounge/client"

    port_json = Path(__file__).resolve().parent.parent / "config" / "port.json"
    port = json.load(open(port_json)).get("port")

    start_fastapi_server(handlers, client_dir, port)
