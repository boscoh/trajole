import os

import psutil

from rshow import mode

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
    if hasattr(mode, in_config.command):
        StreamingTrajectoryClass = getattr(mode, in_config.command)
        global traj_stream
        traj_stream = StreamingTrajectoryClass(in_config)
        return True
    return False


def reset_foam_traj(foam_id):
    return {"title": traj_stream.get_config('command')}


def get_config(foam_id, k):
    return traj_stream.get_config(k)


def kill():
    if not traj_stream.get_config("is_dev"):
        psutil.Process(os.getpid()).kill()


def get_pdb_lines(foam_id, i_frame_traj):
    return traj_stream.get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_alphaspace(foam_id, i_frame_traj):
    return traj_stream.get_pdb_lines_with_alphaspace(i_frame_traj)
