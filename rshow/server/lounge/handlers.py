import logging
import time
from collections import OrderedDict
from path import Path
import pickle
import shutil

from addict import Dict
import pydash as py_
from rich.pretty import pprint
from rseed.formats.easyh5 import EasyTrajH5, EasyFoamTrajH5
from rseed.granary import Granary
from rseed.util.fs import tic, toc
from rseed.analysis.fes import get_i_frame_min

from rshow.persist import PersistDictList
from rshow.readers import FoamTrajReader, FoamEnsembleReader
from rshow.util import get_pair_distances

from rseed.util.select import select_mask
from rseed.util.struct import get_parmed_from_traj_frame, get_traj_frame_from_parmed


import numpy as np

logger = logging.getLogger(__name__)

traj_reader_by_foam_id = OrderedDict()

this_dir = Path(__file__).abspath().parent
data_dir = this_dir / "data"
last_foam_id_views = PersistDictList(this_dir / "last_views.yaml", key="id")


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


def get_foam_traj_reader(foam_id):
    # implement an LRU cache for traj_reader
    if foam_id in traj_reader_by_foam_id:
        traj_reader_by_foam_id.move_to_end(foam_id)
    else:
        config = dict(trajectories=[foam_id], is_solvent=False)
        traj_reader_by_foam_id[foam_id] = FoamTrajReader(config)
        # ensure LRU cache stays small
        while len(traj_reader_by_foam_id) > 1000:
            foam_id, traj_reader = traj_reader_by_foam_id.popitem(last=False)
            traj_reader.close()
            del traj_reader
    return traj_reader_by_foam_id[foam_id]


def reset_foam_id(foam_id):
    traj_reader = get_foam_traj_reader(foam_id)
    return {"success": True}


def kill():
    pass


def get_config(foam_id, key):
    return get_foam_traj_reader(foam_id).get_config(key)


def get_pdb_lines(foam_id, i_frame_traj):
    return get_foam_traj_reader(foam_id).get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_as_communities(foam_id, i_frame):
    return get_foam_traj_reader(foam_id).get_pdb_lines_with_as_communities(i_frame)


def get_pdb_lines_with_as_pockets(foam_id, i_frame):
    return get_foam_traj_reader(foam_id).get_pdb_lines_with_as_pockets(i_frame)


def get_views(foam_id):
    return get_foam_traj_reader(foam_id).get_views()


def get_last_foamid_views(n=10):
    logger.info(f"get_last_foamid_views {n}")
    return last_foam_id_views.get(n)


def update_view(foam_id, view):
    view["foamId"] = foam_id
    view["timestamp"] = int(time.time())
    last_foam_id_views.append(view)
    logger.info(f"update_view {view}")
    return get_foam_traj_reader(foam_id).update_view(view)


def delete_view(foam_id, view):
    logger.info(f"delete_view {view}")
    return get_foam_traj_reader(foam_id).delete_view(view)


def get_h5(foam_id):
    traj_reader = get_foam_traj_reader(foam_id)
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

    traj_reader = get_foam_traj_reader(foam_id)
    matrix = traj_reader.get_config("matrix")
    result = get_i_frame_min(matrix)
    h5.set_json_dataset("json_min", {"iframe_min": result})
    logger.info(f"get_min_frame from rshow_matrix: {result}")

    return result


def get_distances(foam_id, dpairs):
    traj_reader = get_foam_traj_reader(foam_id)
    stream_manager = traj_reader.get_traj_manager()
    h5 = get_h5(foam_id)
    atom_indices = stream_manager.i_atoms
    if atom_indices is None:
        atom_indices = list(range(h5.topology.n_atoms))
    return get_pair_distances(dpairs, h5, atom_indices)


def get_ensembles():
    results = [Dict(id=f.parent.name) for f in data_dir.glob("*/ensemble.csv")]
    results.sort(key=lambda x: x["id"])
    return results


def superpose(last_frame, new_frame, atom_mask):
    last_pmd = get_parmed_from_traj_frame(last_frame)
    i_ca_atoms_last = select_mask(last_pmd, atom_mask)

    pmd = get_parmed_from_traj_frame(new_frame)
    i_ca_atoms = select_mask(pmd, atom_mask)

    logger.info(f"superpose atoms {len(i_ca_atoms_last)} {len(i_ca_atoms)}")
    new_frame.xyz = np.copy(new_frame.xyz)
    new_frame.superpose(
        reference=last_frame,
        atom_indices=i_ca_atoms,
        ref_atom_indices=i_ca_atoms_last,
    )


def get_ensemble_reader(ensemble_id):
    if ensemble_id in traj_reader_by_foam_id:
        traj_reader_by_foam_id.move_to_end(ensemble_id)
    else:
        config = Dict(
            ensemble_id=ensemble_id, csv=str(data_dir / ensemble_id / "ensemble.csv")
        )
        ensemble_traj_reader = FoamEnsembleReader(config)
        ensemble_traj_reader.last_frame = None

        def ensemble_get_frame(i_frame_traj):
            i_frame, ensemble_id = i_frame_traj
            traj_reader = get_foam_traj_reader(ensemble_id)
            frame = traj_reader.get_frame([i_frame, 0])
            if ensemble_traj_reader.last_frame is not None:
                superpose(
                    ensemble_traj_reader.last_frame,
                    frame,
                    "diff {protein} {mdtraj name CA}",
                )
            ensemble_traj_reader.last_frame = frame
            return frame

        ensemble_traj_reader.get_frame = ensemble_get_frame

        traj_reader_by_foam_id[ensemble_id] = ensemble_traj_reader
        # ensure LRU cache stays small
        while len(traj_reader_by_foam_id) > 1000:
            ensemble_id, traj_reader = traj_reader_by_foam_id.popitem(last=False)
            traj_reader.close()
            del traj_reader

    return traj_reader_by_foam_id[ensemble_id]


def load_ensemble_id(ensemble_id):
    traj_reader = get_ensemble_reader(ensemble_id)
    return traj_reader.config.table


def delete_ensemble(ensemble_id):
    logger.info(f"delete_ensemble {ensemble_id}")
    ensemble_dir = data_dir / ensemble_id
    ensemble_dir.rmtree_p()
    return {"deleted": ensemble_dir}


def create_ensemble(ensemble_id):
    original_ensemble_id = py_.kebab_case(ensemble_id)
    ensemble_dir = data_dir / ensemble_id
    i = 1
    while ensemble_dir.exists():
        ensemble_id = Path(f"{original_ensemble_id}({i})")
        ensemble_dir = data_dir / ensemble_id
        i += 1
    ensemble_dir.makedirs_p()
    fname = f"{ensemble_id}.csv"
    full_fname = ensemble_dir / "ensemble.csv"
    with open(full_fname, "w") as f:
        f.write("foam_id,i_frame\n")
    logger.info(f"Saved {full_fname} for {fname}")
    return {"filename": fname, "ensembleId": ensemble_id}

def add_to_ensemble(ensemble_id, foam_id, frame):
    ensemble_reader = get_ensemble_reader(ensemble_id)
    ensemble_reader.add(foam_id, frame)
    ensemble_reader.save()
