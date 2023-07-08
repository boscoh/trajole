import inspect
import logging
import time
import traceback
from io import BytesIO
from rich.pretty import pretty_repr
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse, FileResponse
from starlette.staticfiles import StaticFiles


logger = logging.getLogger(__name__)


def make_app(handlers, client_dir):
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    @app.post("/rpc-run")
    async def rpc_run(data: dict):
        job_id = data.get("id", None)
        method = data.get("method")
        params = data.get("params", [])
        start_time = time.perf_counter_ns()
        try:
            if not hasattr(handlers, method):
                raise Exception(f"rpc-run {method} is not found")
            lines = pretty_repr(params).split("\n")
            lines[0] = f"rpc-run.{method}:start" + lines[0]
            for l in lines:
                logger.info(l)
            fn = getattr(handlers, method)
            if inspect.iscoroutinefunction(fn):
                result = await fn(*params)
            else:
                result = fn(*params)
            result = {"result": result, "jsonrpc": "2.0", "id": job_id}
            elapsed_ms = round((time.perf_counter_ns() - start_time) / 1e6)
            logger.info(f"rpc-run.{method}:finished in {elapsed_ms}ms")
        except Exception as e:
            elapsed_ms = round((time.perf_counter_ns() - start_time) / 1e6)
            logger.info(f"rpc-run.{method}:error after {elapsed_ms}ms:")
            error_lines = str(traceback.format_exc()).splitlines()
            for line in error_lines:
                logger.error(line)
            result = {
                "error": {"code": -1, "message": error_lines},
                "jsonrpc": "2.0",
                "id": job_id,
            }
        return result

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

    return app
