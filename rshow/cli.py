#!/usr/bin/env python
import click
from addict import Dict
from pathlib import Path
import json
import logging

from rshow import serve
from rshow.server.local import handlers


config = Dict()


def run_from_config():
    client_dir = Path(__file__).resolve().parent / "server/local/client"

    logging.basicConfig(level=logging.INFO)

    if not config.get("port"):
        port_json = Path(__file__).resolve().parent.parent / "config" / "port.json"
        port = json.load(open(port_json)).get("port")
    else:
        port = config.port

    if not config.is_dev:
        serve.open_url_in_background(f"http://localhost:{config.port}/#/foamtraj/0")

    handlers.init(config)

    serve.start_fastapi_server(handlers, client_dir, port)


@click.group()
@click.option(
    "--dev", is_flag=True, help="Run server in dev mode (no break/no open browser)"
)
@click.option("--solvent", is_flag=True, help="Keep solvent")
@click.option("--hydrogen", is_flag=True, help="Keep hydrogens")
@click.option("--background", default="#DDD", help="Background color to jolecule")
@click.option("--port", default=9023, help="port number")
def cli(dev, solvent, hydrogen, background, port):
    """
    rshow: : integrated analysis/protein viewer

    (C) 2021 Redesign Science
    """
    config.is_dev = dev
    config.is_solvent = solvent
    config.is_hydrogen = hydrogen
    config.background = background
    config.port = port


@cli.command()
@click.argument("h5")
def traj(h5):
    """
    Trajectory of an MD simulation
    """
    config.command = "TrajStream"
    config.trajectories = [h5]
    run_from_config()


@cli.command()
@click.argument("metad_dir", default=".", required=False)
@click.option("--n-bin", type=int)
def fes(metad_dir, n_bin):
    """
    Free-Energy Surface of Collective Variables
    """
    config.command = "FesStream"
    config.metad_dir = metad_dir
    if n_bin:
        config.n_bin = n_bin
    run_from_config()


@cli.command()
@click.argument("foam_id")
def traj_foam(foam_id):
    """
    Trajectory of a MD simulation loaded from FoamDB
    """
    config.command = "FoamTrajStream"
    config.trajectories = [foam_id]
    run_from_config()


@cli.command()
@click.argument("matrix_dir", default=".", required=False)
@click.option("--mode", default="matrix-strip", required=False)
def matrix(matrix_dir, mode):
    """
    Generic 2D surface linked to a set of trajectories
    """
    config.command = "MatrixStream"
    config.matrix_dir = matrix_dir
    config.mode = mode
    run_from_config()


@cli.command()
@click.argument("re_dir", default=".", required=False)
@click.option("--key", default="u")
def re(re_dir, key):
    """
    Replicas in a replica-exchange simulation
    """
    config.command = "ParallelStream"
    config.re_dir = re_dir
    config.key = key
    run_from_config()


@cli.command()
@click.argument("re_dir", default=".", required=False)
@click.option("--key", default="u")
def re_dock(re_dir, key):
    """
    Replicas in a replica-exchange simulation
    """
    config.command = "ParallelDockStream"
    config.re_dir = re_dir
    config.key = key
    run_from_config()


@cli.command()
@click.argument("pdb")
@click.argument("sdf")
@click.argument("csv", required=False)
def ligands(pdb, sdf, csv):
    """
    Ligand browser
    """
    config.command = "LigandsStream"
    config.pdb = pdb
    config.ligands = sdf
    config.csv = csv
    run_from_config()


@cli.command()
@click.argument("pdb")
def frame(pdb):
    """
    Ligand browser
    """
    config.command = "FrameStream"
    config.pdb_or_parmed = pdb
    run_from_config()
