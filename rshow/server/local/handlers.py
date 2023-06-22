import logging
import os

import psutil
from path import Path
from pydash import py_
from rich.pretty import pprint
from rseed.formats.easyh5 import EasyFoamTrajH5, EasyTrajH5
from rseed.util.fs import load_yaml_dict
from rshow import stream

traj_stream = None

logger = logging.getLogger(__name__)


def select_new_key(foam_id, key):
    selectable_classes = ["ParallelStream", "ParallelDockStream"]
    if traj_stream and traj_stream.__class__.__name__ in selectable_classes:
        config = traj_stream.config
        config.key = key
        init_traj_stream_from_config(config)


def init_traj_stream_from_config(in_config):
    """
    Entry point of app from server, and will setup depending on the config options
    in the config dictionary.

    :return bool: False on failure
    """
    if not hasattr(stream, in_config.stream_class):
        raise ValueError(f"Couldn't find stream_class {in_config.stream_class}")

    if "work_dir" in in_config:
        os.chdir(in_config["work_dir"])

    global traj_stream
    StreamingTrajectoryClass = getattr(stream, in_config.stream_class)
    traj_stream = StreamingTrajectoryClass(in_config)


def reset_foam_id(foam_id):
    return {"title": traj_stream.get_title()}


def get_config(foam_id, k):
    return traj_stream.get_config(k)


def kill():
    if not traj_stream.get_config("is_dev"):
        psutil.Process(os.getpid()).kill()


def get_pdb_lines(foam_id, i_frame_traj):
    return traj_stream.get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_as_communities(foam_id, i_frame_traj):
    return traj_stream.get_pdb_lines_with_as_communities(i_frame_traj)


def get_pdb_lines_with_as_pockets(foam_id, i_frame_traj):
    return traj_stream.get_pdb_lines_with_as_pockets(i_frame_traj)


def get_views(foam_id):
    return traj_stream.get_views()


def add_view(foam_id, view):
    return traj_stream.add_view(view)


def delete_view(foam_id, view):
    return traj_stream.delete_view(view)


def get_tags(foam_id):
    traj_manager = traj_stream.traj_manager
    return traj_manager.get_h5(0)


def get_h5(foam_id):
    traj_manager = traj_stream.traj_manager
    return traj_manager.get_h5(0)


def get_json_datasets(foam_id):
    return ["json_min"]


def get_json(foam_id, key):
    return get_h5(foam_id).get_json_dataset(key)


def get_parmed_blob(foam_id, i_frame=None):
    pass


def get_min_frame(foam_id):
    if hasattr(traj_stream, "config"):
        config = traj_stream.config
        print_config = py_.clone(config)
        py_.unset(print_config, "matrix")
        if hasattr(config, "metad_dir"):
            min_yaml = Path(traj_stream.config["metad_dir"]) / "min.yaml"
            data = load_yaml_dict(min_yaml)
            logger.info(f"get_min_frame {data}")
            return data["frame"]
    return None
