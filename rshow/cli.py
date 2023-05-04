#!/usr/bin/env python
import json
import logging
from pathlib import Path

import click
from addict import Dict

from rshow import serve
from rshow.server.local import handlers

config = Dict()


def run():
    global config

    if "mode" not in config:
        config.mode = ""

    logging.basicConfig(level=logging.INFO)

    handlers.init_traj_stream_from_config(config)

    client_dir = Path(__file__).resolve().parent / "server/local/client"

    if not config.get("port"):
        port_json = Path(__file__).resolve().parent.parent / "config" / "port.json"
        port = json.load(open(port_json)).get("port")
    else:
        port = config.port

    if not config.is_dev:
        serve.open_url_in_background(f"http://localhost:{config.port}/#/foamtraj/0")

    serve.start_fastapi_server(handlers, client_dir, port, config.is_dev)


@click.group()
@click.option("--dev", is_flag=True, help="Run continuous server")
@click.option("--solvent", is_flag=True, help="Keep solvent")
@click.option("--hydrogen", is_flag=True, help="Keep hydrogens")
@click.option("--port", default=9023, help="port number")
def cli(dev, solvent, hydrogen, port):
    """
    rshow: mdtraj h5 viewer

    (C) 2021 Redesign Science
    """
    config.is_dev = dev
    config.is_solvent = solvent
    config.is_hydrogen = hydrogen
    config.port = port


@cli.command()
@click.argument("h5")
def traj(h5):
    """
    MD Trajectory
    """
    config.command = "TrajStream"
    config.trajectories = [h5]
    run()


@cli.command()
@click.argument("metad_dir", default=".", required=False)
@click.option("--n-bin", type=int)
def fes(metad_dir, n_bin):
    """
    Integrated MD traj w/Free-Energy Surface of CV
    """
    config.command = "FesStream"
    config.metad_dir = metad_dir
    if n_bin:
        config.n_bin = n_bin
    run()


@cli.command()
@click.argument("foam_id")
def traj_foam(foam_id):
    """
    MD trajectory stored on FoamDB
    """
    config.command = "FoamTrajStream"
    config.trajectories = [foam_id]
    run()


@cli.command()
@click.argument("matrix_yaml", default="matrix.yaml", required=False)
@click.option("--mode", default="matrix-strip", required=False)
def matrix(matrix_yaml, mode):
    """
    Generic 2D surface linked to a set of MD trajs
    """
    config.command = "MatrixStream"
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
    config.command = "ParallelStream"
    config.re_dir = re_dir
    config.key = key
    run()


@cli.command()
@click.argument("re_dir", default=".", required=False)
@click.option("--key", default="u")
def re_dock(re_dir, key):
    """
    Multiple replicas in a replica-exchange w/fixed receptor
    """
    config.command = "ParallelDockStream"
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
    config.command = "LigandsStream"
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
    config.command = "FrameStream"
    config.pdb_or_parmed = pdb
    run()


@cli.command()
@click.argument("test_url")
@click.argument("open_url", required=False)
def open_url(test_url, open_url):
    """
    Single frame of PDB or PARMED file
    """
    from rshow.serve import open_url_in_background

    logging.basicConfig(level=logging.INFO)
    open_url_in_background(test_url, open_url)


if __name__ == "__main__":
    cli()
