import copy
import logging
import os
import pickle
import time
from _thread import RLock
from collections import OrderedDict

import numpy as np
import pydash as py_
from addict import Dict
from path import Path

from easytrajh5.select import select_mask
from easytrajh5.struct import get_parmed_from_mdtraj
from rseed.analysis.fes import get_i_frame_min
from rseed.analysis.blast import align_parmed
from rshow.persist import PersistDictList
from rshow.readers import FoamTrajReader, FoamEnsembleReader
from rshow.util import get_pair_distances

logger = logging.getLogger(__name__)
this_dir = Path(__file__).abspath().parent
data_dir = this_dir / "data"

last_foam_id_views = PersistDictList(this_dir / "last_views.yaml", key="id")

traj_reader_by_foam_id = OrderedDict()


def get_reader_from_lru_cache(
    cache_id,
    init_reader_fn,
    traj_reader_by_foam_id=traj_reader_by_foam_id,
    maxsize=1000,
):
    lock = RLock()
    with lock:
        if cache_id in traj_reader_by_foam_id:
            traj_reader_by_foam_id.move_to_end(cache_id)
        else:
            traj_reader_by_foam_id[cache_id] = init_reader_fn(cache_id)
            while len(traj_reader_by_foam_id) > maxsize:
                cache_id, reader = traj_reader_by_foam_id.popitem(last=False)
                reader.close()
                del reader
        reader = traj_reader_by_foam_id[cache_id]
    return reader


def select_new_key(foam_id, key):
    traj_reader = get_foam_traj_reader(foam_id)
    if "opt_keys" in traj_reader.config:
        config = traj_reader.config
        config.matrix = config.matrix_by_key[key]
        config.key = key
    return {"success": True}



def get_tags(foam_id):
    from foamdb.client import PostgresClient
    from foamdb.config import Config

    if os.environ.get("HOME") is None:
        # when running under supervisord in the lounge vm, there is no HOME
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


def init_traj_reader(foam_id):
    return FoamTrajReader({"trajectories": [foam_id], "is_solvent": False})


def get_foam_traj_reader(foam_id) -> FoamTrajReader:
    return get_reader_from_lru_cache(foam_id, init_traj_reader)


def reset_foam_id(foam_id):
    # force reader to be reinitialized
    get_foam_traj_reader(foam_id)
    return {"success": True}


def kill():
    pass


def get_config(foam_id, key):
    return get_foam_traj_reader(foam_id).get_config(key)


def get_pdb_lines(foam_id, i_frame_traj):
    return get_foam_traj_reader(foam_id).get_pdb_lines(i_frame_traj)


def get_pdb_lines_with_as_communities(foam_id, i_frame_traj):
    return get_foam_traj_reader(foam_id).get_pdb_lines_with_as_communities(i_frame_traj)


def get_pdb_lines_with_as_pockets(foam_id, i_frame_traj):
    return get_foam_traj_reader(foam_id).get_pdb_lines_with_as_pockets(i_frame_traj)


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


def get_traj_file(foam_id):
    traj_reader = get_foam_traj_reader(foam_id)
    traj_manager = traj_reader.traj_manager
    return traj_manager.get_traj_file(0)


def get_json_datasets(foam_id):
    return get_traj_file(foam_id).get_dataset_keys()


def get_json(foam_id, key):
    return get_traj_file(foam_id).get_json_dataset(key)


def get_parmed_blob(foam_id, i_frame=None) -> bytes:
    logger.info(f"get_parmed_blob {foam_id} {i_frame}")
    traj_file = get_traj_file(foam_id)
    if i_frame is None:
        blob = traj_file.get_bytes_dataset("parmed")
    else:
        pmd = traj_file.get_parmed_from_dataset(int(i_frame))
        blob = pickle.dumps(pmd.__getstate__())
    logger.info(f"get_parmed_blob read {len(blob)} bytes")
    return blob


def get_min_frame(foam_id):
    traj_file = get_traj_file(foam_id)
    if traj_file.has_dataset("json_min"):
        data = traj_file.get_json_dataset("json_min")
        result = data.get("iframe_min")
        if result is not None:
            logger.info(f"get_min_frame from dataset:`json_min`: {result}")
            return result

    if not traj_file.has_dataset("json_rshow_matrix"):
        return None

    traj_reader = get_foam_traj_reader(foam_id)
    matrix = traj_reader.get_config("matrix")
    result = get_i_frame_min(matrix)
    traj_file.set_json_dataset("json_min", {"iframe_min": result})
    logger.info(f"get_min_frame from rshow_matrix: {result}")

    return result


def get_distances(foam_id, dpairs):
    traj_file = get_traj_file(foam_id)
    atom_indices = traj_file.atom_indices
    if atom_indices is None:
        atom_indices = list(range(traj_file.topology.n_atoms))
    return get_pair_distances(dpairs, traj_file, atom_indices)


def get_ensembles():
    results = [Dict(id=f.parent.name) for f in data_dir.glob("*/ensemble.csv")]
    results.sort(key=lambda x: x["id"])
    return results


def superpose(frame1, frame2, atom_mask1, atom_mask2=None):
    if not atom_mask2:
        atom_mask2 = atom_mask1

    pmd1 = get_parmed_from_mdtraj(frame1)
    i_ca_atoms1 = select_mask(pmd1, atom_mask1)

    pmd2 = get_parmed_from_mdtraj(frame2)
    i_ca_atoms2 = select_mask(pmd2, atom_mask2)

    frame2.xyz = np.copy(frame2.xyz)

    if len(i_ca_atoms2) == len(i_ca_atoms1):
        logger.info("superpose atoms")
        frame2.superpose(
            reference=frame1,
            atom_indices=i_ca_atoms2,
            ref_atom_indices=i_ca_atoms1,
        )
    else:
        logger.info(
            f"warning: fail to superpose atoms {len(i_ca_atoms1)} != {len(i_ca_atoms2)}"
        )
        old_center = frame1.xyz[-1].mean(axis=0)
        new_center = frame2.xyz[-1].mean(axis=0)
        frame2.xyz[-1] -= new_center
        frame2.xyz[-1] += old_center


def init_ensemble_reader(ensemble_id):
    csv = str(data_dir / ensemble_id / "ensemble.csv")
    ensemble_reader = FoamEnsembleReader({"ensemble_id": ensemble_id, "csv": csv})
    ensemble_reader.frame = None
    ensemble_reader.i_frame_traj = None

    def read_frame_traj(i_frame_traj):
        i_frame, ensemble_id = i_frame_traj[:2]

        traj_reader = get_foam_traj_reader(ensemble_id)
        last_i_frame_traj = ensemble_reader.i_frame_traj

        logger.info(f"get_frame_of_ensemble {last_i_frame_traj} {i_frame_traj}")

        frame = traj_reader.read_frame_traj([i_frame, 0])
        frame = copy.deepcopy(frame)

        if ensemble_reader.frame is not None:
            last_frame = ensemble_reader.frame
            if len(last_i_frame_traj) > 2 and len(i_frame_traj) > 2:
                logger.info("get_frame_of_ensemble superpose with different atom mask")
                last_atom_mask = last_i_frame_traj[2]
                atom_mask = i_frame_traj[2]
                superpose(last_frame, frame, last_atom_mask, atom_mask)
            else:
                logger.info("get_frame_of_ensemble superpose with default atom mask")
                atom_mask = "intersect {protein} {mdtraj name CA}"
                superpose(last_frame, frame, atom_mask)

        ensemble_reader.frame = frame
        ensemble_reader.i_frame_traj = i_frame_traj
        return frame

    ensemble_reader.read_frame_traj = read_frame_traj

    return ensemble_reader


def clear_ensemble_cache(ensemble_id):
    ensemble_reader = get_ensemble_reader(ensemble_id)
    ensemble_reader.frame = None
    ensemble_reader.i_frame_traj = None


def get_ensemble_reader(ensemble_id) -> FoamEnsembleReader:
    return get_reader_from_lru_cache(ensemble_id, init_ensemble_reader)


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


def update_ensemble_row(ensemble_id, i_row, foam_id, frame, atom_mask=""):
    ensemble_reader = get_ensemble_reader(ensemble_id)
    ensemble_reader.update_row(i_row, foam_id, frame, atom_mask)
    ensemble_reader.save()


def add_to_ensemble(ensemble_id, foam_id, frame, atom_mask=""):
    ensemble_reader = get_ensemble_reader(ensemble_id)
    ensemble_reader.add_row(foam_id, frame, atom_mask)
    ensemble_reader.save()


def remove_from_ensemble(ensemble_id, i_row):
    ensemble_reader = get_ensemble_reader(ensemble_id)
    ensemble_reader.remove_row(i_row)
    ensemble_reader.save()


def add_aligned_rows(ensemble_id, foam_id1, foam_id2, range_start, range_end):
    results = []
    ensemble_reader = get_ensemble_reader(ensemble_id)
    matched_segs_list = align_parmed(
        get_traj_file(foam_id1).get_topology_parmed(),
        get_traj_file(foam_id2).get_topology_parmed(),
        data_dir / "fasta1.fasta",
        data_dir / "fasta2.fasta",
        range_start,
        range_end,
    )
    for seg1, seg2 in matched_segs_list:
        ensemble_reader.add_row(foam_id1, 0, seg1)
        results.append([0, foam_id1, seg1])
        ensemble_reader.add_row(foam_id2, 0, seg2)
        results.append([0, foam_id2, seg2])
    ensemble_reader.save()

    return results
