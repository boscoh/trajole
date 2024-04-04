#!/usr/bin/env python
import logging
import os
import socket
from contextlib import closing

import click
import uvicorn
from addict import Dict
from easytrajh5.fs import dump_yaml, tic, toc
from path import Path
from rshow.app import make_app, init_logging, open_url_in_background

from rshow.server.local import handlers

logger = logging.getLogger(__name__)
this_dir = Path(__file__).parent


def find_free_port():
    logger.info(tic("find port"))
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = s.getsockname()[1]
    logger.info(toc() + f": {port}")
    return port


config = Dict(mode="")


def run(config):
    config.client_dir = this_dir / "server/local/client"
    config.data_dir = this_dir / "server/local/data"
    config.work_dir = os.getcwd()
    port = config.get("port")
    init_logging()
    if config.is_dev:
        if not port:
            # fix port so that dev client can find it
            port = 9023
        logger.info(f"port: {port}")
        os.chdir(this_dir)
        dump_yaml(config, "app.yaml")
        # Run uvicorn externally for reloading
        os.system(f"uvicorn run_app:app --reload --port {port}")
    else:
        if not port:
            # mix up ports so multiple copies can run
            port = find_free_port()
        logger.info(f"port: {port}")
        open_url_in_background(f"http://localhost:{port}/#/foamtraj/0")
        app = make_app(handlers, config)
        uvicorn.run(app, port=port, log_level="critical")


@click.group()
@click.option("--dev", is_flag=True, help="Run continuous server")
@click.option("--solvent", is_flag=True, help="Keep solvent")
@click.option("--port", default=None, help="port number")
def cli(dev, solvent, port):
    """
    rshow: mdtraj h5 viewer

    (C) 2021 Redesign Science
    """
    config.is_dev = dev
    config.is_solvent = solvent
    config.port = port


@cli.command()
@click.argument("h5")
def traj(h5):
    """
    Open H5
    """
    config.reader_class = "TrajReader"
    config.trajectories = [h5]
    run(config)


@cli.command()
@click.argument("foam_id")
def traj_foam(foam_id):
    """
    Open H5 stored on FoamDB
    """
    config.reader_class = "FoamTrajReader"
    config.trajectories = [foam_id]
    run(config)


@cli.command()
@click.argument("matrix_yaml", default="matrix.yaml", required=False)
@click.option("--mode", default="matrix-strip", required=False)
def matrix(matrix_yaml, mode):
    """
    Open H5 with matrix
    """
    config.reader_class = "MatrixTrajReader"
    config.matrix_yaml = matrix_yaml
    config.mode = mode
    run(config)


@cli.command()
@click.argument("re_dir", default=".", required=False)
@click.option("--key", default="u")
def re(re_dir, key):
    """
    Open multiple H5 in parallel
    """
    config.reader_class = "ParallelTrajReader"
    config.re_dir = re_dir
    config.key = key
    run(config)


@cli.command()
@click.argument("pdb")
@click.argument("sdf")
@click.argument("csv", required=False)
def ligands(pdb, sdf, csv):
    """
    Open PDB with ligands in SDF
    """
    config.reader_class = "LigandsReceptorReader"
    config.pdb = pdb
    config.ligands = sdf
    config.csv = csv
    run(config)


@cli.command()
@click.argument("pdb")
def frame(pdb):
    """
    Open PDB or PARMED
    """
    config.reader_class = "FrameReader"
    config.pdb_or_parmed = pdb
    run(config)


@cli.command()
@click.argument("test_url")
@click.argument("open_url", required=False)
def open_url(test_url, open_url):
    """
    Open OPEN_URL when TEST_URL works
    """

    logging.basicConfig(level=logging.INFO)
    open_url_in_background(test_url, open_url)


if __name__ == "__main__":
    cli()
