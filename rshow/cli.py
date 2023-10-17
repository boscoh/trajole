#!/usr/bin/env python
import json
import logging
import os
from path import Path

import click
from addict import Dict
from rich.pretty import pprint

from rseed.util.fs import dump_yaml

import rshow.openurl
from rshow.server.local import handlers
from rshow.make_app import make_app
from rshow.log import init_logging
import uvicorn

import socket
from contextlib import closing


logger = logging.getLogger(__name__)


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


config = Dict(mode="")


def run():
    global config

    this_dir = Path(__file__).abspath().parent

    init_logging()

    port = config.get("port")

    if config.is_dev:
        config.server = "local"

        config.work_dir = os.getcwd()
        if not port:
            port = 9023

        logger.info(f"port: {port}")
        os.chdir(this_dir)
        dump_yaml(config, "dev_config.yaml")

        # Run in uvicorn cli using the reload facility
        # Requires a module with configs loaded in already
        # to expose an app objct
        os.system(f"uvicorn app_from_dev_config:app --reload --port {port}")
    else:
        if not port:
            port = find_free_port()
        logger.info(f"port: {port}")

        rshow.openurl.open_url_in_background(f"http://localhost:{port}/#/foamtraj/0")

        handlers.init_traj_reader(config)
        client_dir = this_dir / "server/local/client"
        data_dir = this_dir / "server/local/data"

        app = make_app(handlers, client_dir, data_dir)

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
    MD Trajectory
    """
    config.stream_class = "TrajReader"
    config.trajectories = [h5]
    run()


@cli.command()
@click.argument("metad_dir", default=".", required=False)
def fes(metad_dir):
    """
    Integrated MD traj w/Free-Energy Surface of CV
    """
    config.stream_class = "FesMatrixTrajReader"
    config.metad_dir = metad_dir
    run()


@cli.command()
@click.argument("foam_id")
def traj_foam(foam_id):
    """
    MD trajectory stored on FoamDB
    """
    config.stream_class = "FoamTrajReader"
    config.trajectories = [foam_id]
    run()


@cli.command()
@click.argument("matrix_yaml", default="matrix.yaml", required=False)
@click.option("--mode", default="matrix-strip", required=False)
def matrix(matrix_yaml, mode):
    """
    Generic 2D surface linked to a set of MD trajs
    """
    config.stream_class = "MatrixTrajReader"
    config.matrix_yaml = matrix_yaml
    config.mode = mode
    run()


@cli.command()
@click.argument("re_dir", default=".", required=False)
@click.option("--key", default="u")
def re(re_dir, key):
    """
    Multiple replicas in a replica-exchange
    """
    config.stream_class = "ParallelTrajReader"
    config.re_dir = re_dir
    config.key = key
    run()


@cli.command()
@click.argument("pdb")
@click.argument("sdf")
@click.argument("csv", required=False)
def ligands(pdb, sdf, csv):
    """
    Multiple ligands in single receptor
    """
    config.stream_class = "LigandsReceptorReader"
    config.pdb = pdb
    config.ligands = sdf
    config.csv = csv
    run()


@cli.command()
@click.argument("pdb")
def frame(pdb):
    """
    Single frame of PDB or PARMED file
    """
    config.stream_class = "FrameReader"
    config.pdb_or_parmed = pdb
    run()


@cli.command()
@click.argument("test_url")
@click.argument("open_url", required=False)
def open_url(test_url, open_url):
    """
    Single frame of PDB or PARMED file
    """
    from rshow.openurl import open_url_in_background

    logging.basicConfig(level=logging.INFO)
    open_url_in_background(test_url, open_url)


if __name__ == "__main__":
    cli()
