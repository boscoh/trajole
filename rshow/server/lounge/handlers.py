import logging
import time
from collections import OrderedDict
from path import Path
import pickle

from addict import Dict
from rich.pretty import pprint
from rseed.formats.easyh5 import EasyTrajH5, EasyFoamTrajH5
from rseed.granary import Granary
from rseed.util.fs import tic, toc
from rseed.analysis.fes import get_i_frame_min

from rshow.persist import PersistDictList
from rshow.readers import FoamTrajReader
from rshow.util import get_pair_distances

logger = logging.getLogger(__name__)
traj_reader_by_foam_id = OrderedDict()
views_yaml = Path(__file__).abspath().parent / "last_views.yaml"
last_foam_id_views = PersistDictList(views_yaml, key="id")


def select_new_key(foam_id, key):
    # NOT supported for lounge
    return


def get_tags(foam_id):
    import os

    from foamdb.client import PostgresClient
    from foamdb.config import Config

    if os.environ.get("HOME") is None:
        # when we are running under supervisord
        # in the lounge vm where there is no HOME
        config = Config("/home/bosco/.config/foamdb/config.json")
    else:
        config = Config()

    result = {}
    with PostgresClient(config.get("database")) as client:
        traj = client.get_trajectory(foam_id)
        for k, v in traj["tags"].items():
            result[k] = v

    return result


def set_tags(foam_id, tags: dict):
    import os

    from foamdb.client import PostgresClient
    from foamdb.config import Config
    from foamdb.query import Trajectory

    if os.environ.get("HOME") is None:
        # when we are running under supervisord
        # in the lounge vm where there is no HOME
        config = Config("/home/bosco/.config/foamdb/config.json")
    else:
        config = Config()
    with PostgresClient(config.get("database")) as client:
        client.update(Trajectory(trajectory_id=foam_id, tags=tags))

    return {"success": True}


def get_traj_reader(foam_id):
    # implement an LRU cache for traj_reader
    if foam_id in traj_reader_by_foam_id:
        traj_reader_by_foam_id.move_to_end(foam_id)
    else:
        config = dict(trajectories=[foam_id], is_solvent=False)
        traj_reader_by_foam_id[foam_id] = FoamTrajReader(config)
        # ensure LRU cache stays small
        while len(traj_reader_by_foam_id) > 128:
            foam_id, traj_reader = traj_reader_by_foam_id.popitem(last=False)
            traj_reader.close()
            del traj_reader
    return traj_reader_by_foam_id[foam_id]


def reset_foam_id(foam_id):
    traj_reader = get_traj_reader(foam_id)
    return {"success": True}


def kill():
    pass


def get_config(foam_id, key):
    return get_traj_reader(foam_id).get_config(key)


def get_pdb_lines(foam_id, i_frame_traj):
    return get_traj_reader(foam_id).get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_as_communities(foam_id, i_frame):
    return get_traj_reader(foam_id).get_pdb_lines_with_as_communities(i_frame)


def get_pdb_lines_with_as_pockets(foam_id, i_frame):
    return get_traj_reader(foam_id).get_pdb_lines_with_as_pockets(i_frame)


def get_views(foam_id):
    return get_traj_reader(foam_id).get_views()


def get_last_foamid_views(n=10):
    logger.info(f"get_last_foamid_views {n}")
    return last_foam_id_views.get(n)


def update_view(foam_id, view):
    view["foamId"] = foam_id
    view["timestamp"] = int(time.time())
    last_foam_id_views.append(view)
    logger.info(f"update_view {view}")
    return get_traj_reader(foam_id).update_view(view)


def delete_view(foam_id, view):
    logger.info(f"delete_view {view}")
    return get_traj_reader(foam_id).delete_view(view)


def get_h5(foam_id):
    traj_reader = get_traj_reader(foam_id)
    traj_manager = traj_reader.traj_manager
    return traj_manager.get_h5(0)


def get_json_datasets(foam_id):
    return get_h5(foam_id).get_dataset_keys()


def get_json(foam_id, key):
    return get_h5(foam_id).get_json_dataset(key)


def get_parmed_blob(foam_id, i_frame=None) -> bytes:
    logger.info(f"get_parmed_blob {foam_id} {i_frame}")
    h5: EasyTrajH5 = get_h5(foam_id)
    if i_frame is None:
        blob = h5.get_bytes_dataset("parmed")
    else:
        i_frame = int(i_frame)
        granary = Granary.from_easy_h5(h5)
        if i_frame < 0:
            i_frame = h5.get_n_frame() + i_frame
        granary.set_frame_from_easy_h5(h5, i_frame)
        blob = pickle.dumps(granary.structure.__getstate__())
    logger.info(f"get_parmed_blob read {len(blob)} bytes")
    return blob


def get_min_frame(foam_id):
    h5 = get_h5(foam_id)
    if h5.has_dataset("json_min"):
        data = h5.get_json_dataset("json_min")
        result = data.get("iframe_min")
        if result is not None:
            logger.info(f"get_min_frame from dataset:`json_min`: {result}")
            return result

    if not h5.has_dataset("rshow_matrix"):
        return None

    traj_reader = get_traj_reader(foam_id)
    matrix = traj_reader.get_config("matrix")
    result = get_i_frame_min(matrix)
    h5.set_json_dataset("json_min", {"iframe_min": result})
    logger.info(f"get_min_frame from rshow_matrix: {result}")

    return result


def get_distances(foam_id, dpairs):
    traj_reader = get_traj_reader(foam_id)
    stream_manager = traj_reader.get_traj_manager()
    h5 = get_h5(foam_id)
    atom_indices = stream_manager.i_atoms
    if atom_indices is None:
        atom_indices = list(range(h5.topology.n_atoms))
    return get_pair_distances(dpairs, h5, atom_indices)
