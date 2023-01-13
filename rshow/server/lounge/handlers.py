import logging
from collections import OrderedDict
from pathlib import Path

from addict import Dict

from rshow import mode as stream

logger = logging.getLogger(__name__)

config = {}
traj_stream = None
traj_stream_by_foam_id = OrderedDict()
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)


def select_new_key(foam_id, key):
    selectable_classes = ["ParallelStream", "ParallelDockStream"]
    traj_stream = traj_stream_by_foam_id[foam_id]
    if not traj_stream or traj_stream.__class__.__name__ not in selectable_classes:
        return
    logger.info(f"select_new_key {key}")
    global config
    config = Dict(config)
    config.key = key
    init_traj_stream_from_config(config)


def get_tags(foam_id):
    import os

    from foamdb.client import PostgresClient
    from foamdb.config import Config

    result = {}
    try:
        home = os.environ.get("HOME")
        if home is None:
            # when we are running under supervisord
            # in the lounge vm where there is no HOME
            config = Config("/home/bosco/.config/foamdb/config.json")
        else:
            config = Config()
        with PostgresClient(config.get("database")) as client:
            traj = client.get_trajectory(foam_id)
            for k, v in traj["tags"].items():
                if k in ["work_dir", "command"]:
                    continue
                result[k] = v
    except:
        pass
    return result


def reset_foam_traj(foam_id):
    new_config = Dict()
    logger.info(f"reset_foam_traj {foam_id}")
    new_config.is_solvent = config.is_solvent
    new_config.is_hydrogen = config.is_hydrogen
    new_config.background = config.background
    new_config.is_dev = config.is_dev
    new_config.command = "FoamTrajStream"
    new_config.trajectories = [foam_id]
    new_config.foam_id = foam_id
    init_traj_stream_from_config(new_config)
    tags = get_tags(foam_id)
    tags["foam_id"] = foam_id
    pieces = [f"{k}={v}" for k, v in tags.items()]
    title = " ".join(pieces)
    return {"title": title}


def init_traj_stream_from_config(in_config):
    """
    Entry point of app from server
    """
    if not hasattr(stream, in_config.command):
        return False

    logger.info(f"init_traj_stream_from_config {in_config.command}")
    global traj_stream, config

    foam_id = in_config.trajectories[0]

    if foam_id in traj_stream_by_foam_id:
        traj_stream = traj_stream_by_foam_id[foam_id]
    else:
        StreamingTrajectoryClass = getattr(stream, in_config.command)
        traj_stream = StreamingTrajectoryClass(in_config)
        traj_stream_by_foam_id[foam_id] = traj_stream
        # ensure the object stays small
        while len(traj_stream_by_foam_id) > 128:
            traj_stream_by_foam_id.popitem(last=False)

    config = Dict(traj_stream.config)

    return True


def kill():
    pass


def get_config(foam_id, key):
    return traj_stream_by_foam_id[foam_id].config[key]


def get_pdb_lines(foam_id, i_frame_traj):
    return traj_stream_by_foam_id[foam_id].get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_alphaspace(foam_id, i_frame):
    return traj_stream_by_foam_id[foam_id].get_pdb_lines_with_alphaspace(i_frame)
