import logging
import time
from collections import OrderedDict
from path import Path
import pickle

from addict import Dict
from rich.pretty import pprint
from rseed.formats.easyh5 import EasyTrajH5, EasyFoamTrajH5
from rseed.granary import Granary

from rshow import stream
from rshow.persist import PersistDictList
from rshow.stream import TrajStream

logger = logging.getLogger(__name__)

config = Dict(is_solvent=False, is_hydrogen=True)

traj_stream = None
traj_stream_by_foam_id = OrderedDict()


views_yaml = Path(__file__).abspath().parent / "last_views.yaml"
last_foam_id_views = PersistDictList(views_yaml, key="id")


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


def reset_foam_id(foam_id):
    new_config = Dict()
    logger.info(f"reset_foam_id {foam_id}")
    new_config.is_solvent = config.is_solvent
    new_config.is_hydrogen = config.is_hydrogen
    new_config.is_dev = config.is_dev
    new_config.command = "FoamTrajStream"
    new_config.trajectories = [foam_id]
    new_config.foam_id = foam_id
    init_traj_stream_from_config(new_config)
    tags = get_tags(foam_id)
    pieces = [f"{k}={v}" for k, v in tags.items()]
    title = " ".join(pieces)
    return {"title": tags}


def init_traj_stream_from_config(in_config):
    """
    Entry point of app from server
    """
    if not hasattr(stream, in_config.command):
        return False

    global traj_stream, config

    logger.info("config:")
    pprint(in_config)

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


def kill():
    pass


def get_config(foam_id, key):
    return traj_stream_by_foam_id[foam_id].config[key]


def get_pdb_lines(foam_id, i_frame_traj):
    return traj_stream_by_foam_id[foam_id].get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_as_communities(foam_id, i_frame):
    return traj_stream_by_foam_id[foam_id].get_pdb_lines_with_as_communities(i_frame)


def get_pdb_lines_with_as_pockets(foam_id, i_frame):
    return traj_stream_by_foam_id[foam_id].get_pdb_lines_with_as_pockets(i_frame)


def get_views(foam_id):
    return traj_stream_by_foam_id[foam_id].get_views()


def get_last_foamid_views(n=10):
    logger.info(f"get_last_foamid_views {n}")
    return last_foam_id_views.get(n)


def update_view(foam_id, view):
    view["foamId"] = foam_id
    view["timestamp"] = int(time.time())
    last_foam_id_views.append(view)
    logger.info(f"update_view {view}")
    return traj_stream_by_foam_id[foam_id].update_view(view)


def delete_view(foam_id, view):
    logger.info(f"delete_view {view}")
    return traj_stream_by_foam_id[foam_id].delete_view(view)


def get_h5(foam_id):
    traj_stream: TrajStream = traj_stream_by_foam_id[foam_id]
    traj_manager = traj_stream.traj_manager
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
    h5: EasyFoamTrajH5 = get_h5(foam_id)
    if h5.has_dataset("json_min"):
        data = h5.get_json_dataset("json_min")
        logger.info(f"get_min_frame {data}")
        return data["frame"]
    return None
