import logging
import os
from typing import Optional

import psutil
from path import Path
from easytrajh5.fs import load_yaml_dict, dump_yaml
from rseed.analysis.fes import get_i_frame_min
from rshow import readers
from rshow.util import get_pair_distances

traj_reader: Optional[readers.RshowReaderMixin] = None

logger = logging.getLogger(__name__)


data_dir = Path(__file__).abspath().parent / "data"


def select_new_key(foam_id, key):
    selectable_classes = ["ParallelTrajReader", "ParalleFixedReceptorLigandTrajReader"]
    if traj_reader and traj_reader.__class__.__name__ in selectable_classes:
        config = traj_reader.config
        config.key = key
        init_traj_reader(config)


def init_traj_reader(in_config):
    """
    Entry point of app from server, and will setup depending on the config options
    in the config dictionary.

    :return bool: False on failure
    """
    if not hasattr(readers, in_config.reader_class):
        raise ValueError(f"Couldn't find reader_class {in_config.reader_class}")

    if "work_dir" in in_config:
        os.chdir(in_config["work_dir"])

    global traj_reader
    TrajReaderClass = getattr(readers, in_config.reader_class)
    traj_reader = TrajReaderClass(in_config)


def reset_foam_id(foam_id):
    return {"success": True}


def get_tags(foam_id):
    return traj_reader.get_tags()


def get_config(foam_id, k):
    return traj_reader.get_config(k)


def kill():
    if not traj_reader.get_config("is_dev"):
        psutil.Process(os.getpid()).kill()


def get_pdb_lines(foam_id, i_frame_traj):
    return traj_reader.get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_as_communities(foam_id, i_frame_traj):
    return traj_reader.get_pdb_lines_with_as_communities(i_frame_traj)


def get_pdb_lines_with_as_pockets(foam_id, i_frame_traj):
    return traj_reader.get_pdb_lines_with_as_pockets(i_frame_traj)


def get_views(foam_id):
    return traj_reader.get_views()


def update_view(foam_id, view):
    return traj_reader.update_view(view)


def delete_view(foam_id, view):
    return traj_reader.delete_view(view)


def get_json_datasets(foam_id):
    return []


def get_json(foam_id, key):
    return {}


def get_parmed_blob(foam_id, i_frame=None):
    pass


def get_min_frame(foam_id):
    if not hasattr(traj_reader, "config"):
        return None
    config = traj_reader.config
    if not config.metad_dir:
        return None

    min_yaml = Path(config.metad_dir) / "min.yaml"
    if min_yaml.exists():
        min_frame = load_yaml_dict(min_yaml).get("iframe")
        if min_frame is not None:
            logger.info(f"read min_frame from {min_yaml}: {min_frame}")
            return min_frame

    min_frame = get_i_frame_min(config.matrix)
    logger.info(f"min_frame {min_frame}")
    dump_yaml({"iframe": min_frame}, min_yaml)

    return min_frame


def get_distances(foam_id, dpairs):
    stream_manager = traj_reader.traj_manager.streams
    h5 = stream_manager.get_h5(0)
    atom_indices = stream_manager.i_atoms
    if atom_indices is None:
        top = h5.topology
        atom_indices = list(range(top.n_atoms))
    dpairs = get_pair_distances(dpairs, h5, atom_indices)
    return dpairs
