import os

import psutil

from rshow import stream

traj_stream = None


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
    if not hasattr(stream, in_config.command):
        raise ValueError(f"Couldn't find command {in_config.command}")
    StreamingTrajectoryClass = getattr(stream, in_config.command)
    global traj_stream
    traj_stream = StreamingTrajectoryClass(in_config)


def reset_foam_id(foam_id):
    return {"title": {"title": traj_stream.get_title()}}


def get_config(foam_id, k):
    return traj_stream.get_config(k)


def kill():
    if not traj_stream.get_config("is_dev"):
        psutil.Process(os.getpid()).kill()


def get_pdb_lines(foam_id, i_frame_traj):
    return traj_stream.get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_alphaspace(foam_id, i_frame_traj):
    return traj_stream.get_pdb_lines_with_alphaspace(i_frame_traj)


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
    return get_h5(foam_id).get_dataset_keys()


def get_json(foam_id, key):
    return get_h5(foam_id).get_json_dataset(key)

