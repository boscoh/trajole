import csv
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from rich.pretty import pprint
import mdtraj
import numpy as np
import parmed
from addict import Dict
from easytrajh5.fs import (
    dump_yaml,
    get_checked_path,
    load_yaml,
)
from easytrajh5.fs import toc
from easytrajh5.manager import TrajectoryManager
from easytrajh5.pdb import filter_for_atom_lines, get_pdb_lines_of_traj_frame
from easytrajh5.select import select_mask
from easytrajh5.struct import get_parmed_from_mdtraj, get_mdtraj_from_parmed
from foamdb.easyh5 import FoamTrajectoryManager
from path import Path
from pydash import py_
from rich.pretty import pretty_repr
from rseed.analysis.fes import get_matrix_json as get_matrix
from rseed.analysis.fn import sort_temperatures
from rseed.analysis.replica import ReplicaEnergySampler as FreeEnergySampler
from rseed.granary import Granary
from rseed.util.ligand import iter_ff_mol_from_file

from rshow.alphaspace import AlphaSpace
from rshow.util import get_first_file

logger = logging.getLogger(__name__)


class RshowReaderMixin(ABC):
    """
    Interface to the webclient in Rshow
    """

    @abstractmethod
    def __init__(self, config={}):
        # self.config.mode = "strip",  # "strip", "matrix", "sparse-matrix", "matrix-strip", "table"
        self.config = Dict(config)
        self.traj_manager = None

    @abstractmethod
    def process_config(self):
        pass

    @abstractmethod
    def get_config(self, k) -> Any:
        pass

    @abstractmethod
    def get_tags(self) -> dict:
        pass

    @abstractmethod
    def read_frame_traj(self, i_frame_traj: [int, int] = None) -> mdtraj.Trajectory:
        pass

    def get_pdb_lines(self, i_frame_traj):
        logger.info(f"pdb {i_frame_traj}")
        return filter_for_atom_lines(
            get_pdb_lines_of_traj_frame(self.read_frame_traj(i_frame_traj))
        )

    def get_pdb_lines_with_as_communities(self, i_frame_traj: [int, int]):
        frame = self.read_frame_traj(i_frame_traj)
        pdb_lines = filter_for_atom_lines(get_pdb_lines_of_traj_frame(frame))

        pmd = get_parmed_from_mdtraj(frame)
        i_protein_atoms = select_mask(pmd, "diff {protein} {mdtraj type H}")

        alpha_space = AlphaSpace(frame.atom_slice(i_protein_atoms))
        alpha_space_pdb_lines = alpha_space.get_community_pdb_lines()

        alpha_pdb = "alphaspace.pdb"
        with open(alpha_pdb, "w") as f:
            f.write("\n".join(alpha_space_pdb_lines))

        pdb_lines.extend(alpha_space_pdb_lines)
        return pdb_lines

    def get_pdb_lines_with_as_pockets(self, i_frame_traj: [int, int]):
        frame = self.read_frame_traj(i_frame_traj)
        pdb_lines = filter_for_atom_lines(get_pdb_lines_of_traj_frame(frame))

        pmd = get_parmed_from_mdtraj(frame)
        i_protein_atoms = select_mask(pmd, "diff {protein} {mdtraj type H}")

        alpha_space = AlphaSpace(frame.atom_slice(i_protein_atoms))
        alpha_space_pdb_lines = alpha_space.get_pocket_pdb_lines()

        alpha_pdb = "alphaspace.pdb"
        with open(alpha_pdb, "w") as f:
            f.write("\n".join(alpha_space_pdb_lines))

        pdb_lines.extend(alpha_space_pdb_lines)
        return pdb_lines

    def get_views(self):
        return []

    def update_view(self, view):
        return {}

    def delete_view(self, view):
        return {}

    def close(self):
        pass


def get_i_view(views, test_view):
    for i, view in enumerate(views):
        if view["id"] == test_view["id"]:
            return i
    return None


def update_view(views, update_view):
    i = get_i_view(views, update_view)
    if i is not None:
        views[i] = update_view
    else:
        views.insert(0, update_view)
    return views


def delete_view(views, to_delete_view):
    i = get_i_view(views, to_delete_view)
    if i is not None:
        del views[i]
    return views


def repr_lines(o, prefix=""):
    lines = pretty_repr(o).split("\n")
    lines[0] = prefix + lines[0]
    return lines


class TrajReader(RshowReaderMixin):
    def __init__(self, config={}):
        self.config = Dict(
            mode="strip",  # "strip", "matrix", "sparse-matrix", "matrix-strip", "table"
            strip=[],  # Dictionary of frame, traj, colours for use in rshow
            title="",  # Title for rshow
            is_solvent=True,
        )
        self.config.update(config)
        for l in repr_lines(self.config, f"{self.__class__.__name__}.config = "):
            logger.info(l)

        self.i_frame_traj = None
        self.frame = None
        self.process_config()

    def get_traj_manager(self) -> TrajectoryManager:
        paths = self.config.trajectories
        is_not_writeable = any((not os.access(p, os.R_OK | os.W_OK)) for p in paths)
        mode = "r" if is_not_writeable else "a"
        if mode == "r":
            logger.info("Files are not writeable: read-only mode")
        is_dry_cache = not self.config.is_solvent
        return TrajectoryManager(paths, mode=mode, is_dry_cache=is_dry_cache)

    def get_tags(self):
        names = [Path(t).name for t in self.config.trajectories]
        if len(names) == 1:
            return {"h5": names[0]}
        elif len(names) >= 1:
            return {"h5": " ".join(names)}
        else:
            raise ValueError("No trajectories found.")

    def process_config(self):
        self.config.title = self.get_tags()
        self.traj_manager = self.get_traj_manager()
        self.views_yaml = Path(self.config.trajectories[0]).with_suffix(".views.yaml")
        self.config.mode = "strip"
        self.config.strip = []
        for i_traj in range(self.traj_manager.get_n_trajectories()):
            n_frame = self.traj_manager.get_n_frame(i_traj)
            self.config.strip.append(
                [dict(iFrameTraj=[i, i_traj], p=i / n_frame) for i in range(n_frame)]
            )

    def close(self):
        if hasattr(self, "traj_manager"):
            self.traj_manager.close()

    def get_config(self, k):
        return self.config[k]

    def read_frame_traj(self, i_frame_traj=None):
        if i_frame_traj and i_frame_traj != self.i_frame_traj:
            new_frame = self.traj_manager.read_as_frame_traj(i_frame_traj)
            if self.frame is not None:
                new_frame.xyz = np.copy(new_frame.xyz)
                new_frame.superpose(self.frame)
            self.frame = new_frame
            self.i_frame_traj = i_frame_traj
        return self.frame

    def get_views(self):
        if self.views_yaml.exists():
            result = load_yaml(self.views_yaml)
            if isinstance(result, list):
                return result
        return []

    def update_view(self, view):
        views = self.get_views()
        update_view(views, view)
        dump_yaml(views, self.views_yaml)
        return {}

    def delete_view(self, to_delete_view):
        views = self.get_views()
        delete_view(views, to_delete_view)
        logger.info(f"delete_view view:{to_delete_view['id']}")
        dump_yaml(views, self.views_yaml)


class FrameReader(TrajReader):
    def process_config(self):
        self.config.title = self.config.pdb_or_parmed
        self.config.mode = "frame"
        fname = Path(self.config.pdb_or_parmed)
        if fname.ext == ".parmed":
            self.frame = get_mdtraj_from_parmed(Granary(fname).structure)
        else:
            self.frame = mdtraj.load_pdb(self.config.pdb_or_parmed)
        self.views_yaml = fname.with_suffix(".views.yaml")
        return True

    def read_frame_traj(self, i_frame_traj=None):
        return self.frame

    def get_tags(self):
        fname = self.config.title.lower()
        if fname.endswith("parmed"):
            key = "parmed"
        elif fname.endswith("pdb"):
            key = "pdb"
        else:
            key = "file"
        return {key: self.config.title}


def get_first_value(matrix):
    value = py_.head(
        py_.filter(py_.flatten_deep(matrix), lambda v: py_.has(v, "iFrameTraj"))
    )
    if value is not None:
        return value
    value = py_.head(
        py_.filter(py_.flatten_deep(matrix), lambda v: py_.has(v, "iFrameTrajs"))
    )
    if value is not None:
        return value
    return None


class FesMatrixTrajReader(TrajReader):
    def process_config(self):
        self.config.title = "Free-energy surface of collective variables"
        fes_yaml = get_first_file(
            [
                Path(self.config.metad_dir) / "rshow.matrix.yaml",
                Path(self.config.metad_dir) / "fes.rshow.yaml",
            ]
        )
        if fes_yaml is not None:
            logger.info(f"Loading {fes_yaml}")
            data = load_yaml(fes_yaml, is_addict=True)
        else:
            logger.info(f"Generating fes matrix form {self.config.metad_dir}")
            logger.info(f"Current dir {os.getcwd()}")
            data = get_matrix(self.config.metad_dir)
            dump_yaml(data, fes_yaml)
        logger.info(toc())
        self.config.matrix = data.matrix
        self.config.mode = "matrix"
        for cell in py_.flatten_deep(self.config.matrix):
            if not cell:
                continue
            if py_.has(cell, "p") and not py_.has(cell, 'iFrameTraj'):
                self.config.mode = "sparse-matrix"
                break
        self.config.trajectories = [fes_yaml.parent / t for t in data.trajectories]
        self.traj_manager = self.get_traj_manager()
        self.views_yaml = Path(self.config.trajectories[0]).with_suffix(".views.yaml")


class MatrixTrajReader(TrajReader):
    def process_config(self):
        fname = Path(self.config.matrix_yaml)
        if fname.isdir():
            fname = fname / "matrix.yaml"
        data = load_yaml(fname, is_addict=True)
        parent_dir = Path(fname).abspath().parent
        self.config.matrix = data.matrix
        self.config.title = "Matrix"
        self.config.trajectories = data.trajectories
        if not self.config.mode:
            self.config.mode = "matrix-strip"
        os.chdir(parent_dir)
        self.traj_manager = self.get_traj_manager()
        self.views_yaml = fname.with_suffix(".views.yaml")


class LigandsReceptorReader(TrajReader):
    def process_config(self):
        self.config.title = f"{Path(self.config.pdb).name}"
        self.config.mode = "table"

        pdb = get_checked_path(self.config.pdb)
        self.frame = mdtraj.load_pdb(str(pdb))
        self.receptor_lines = get_pdb_lines_of_traj_frame(self.frame)

        labels = []
        self.ligand_parmeds = []
        ligand_file = get_checked_path(self.config.ligands)
        for i_mol, openff_mol in enumerate(iter_ff_mol_from_file(str(ligand_file))):
            label = openff_mol.name
            labels.append(label)
            j = i_mol + 1
            if j == 1:
                openff_mol.name = "LIG"
            else:
                openff_mol.name = f"Ll{j}" if i_mol < 10 else f"L{j}"
            top = openff_mol.to_topology().to_openmm()
            ligand_parmed = parmed.openmm.load_topology(
                top, xyz=openff_mol.conformers[0]
            )
            logger.info(
                f"ligand n_atom={len(ligand_parmed.atoms)} iFrameTraj=[{i_mol},0] title={label}"
            )
            self.ligand_parmeds.append(ligand_parmed)

        n = len(self.ligand_parmeds)
        self.config.table_headers = ["title", "i"]
        self.config.table = [
            dict(iFrameTraj=[i, 0], p=i / n, vals=[labels[i], i]) for i in range(n)
        ]
        if self.config.csv:
            with open(get_checked_path(self.config.csv)) as f:
                for i, row in enumerate(csv.reader(f)):
                    if i == 0:
                        self.config.table_headers.extend(row)
                    elif i > n:
                        break
                    else:
                        row = [round(float(x), 3) for x in row]
                        self.config.table[i - 1]["vals"].extend(row)
        self.views_yaml = Path(pdb).with_suffix(".views.yaml")

    def get_ligand_pdb_lines(self, i_ligand):
        traj = get_mdtraj_from_parmed(self.ligand_parmeds[i_ligand])
        return get_pdb_lines_of_traj_frame(traj)

    def get_pdb_lines(self, i_frame_traj):
        i_frame = i_frame_traj[0]
        return self.receptor_lines + self.get_ligand_pdb_lines(i_frame)

    def get_tags(self):
        return {"fname": self.config.title}


def convert_rows_to_p_rows(rows):
    values = py_.flatten_deep(rows)
    max_val = py_.max(values)
    min_val = py_.min(values)
    delta_val = max_val - min_val
    return [
        [(v - min_val) / delta_val if delta_val else 0 for v in row] for row in rows
    ]


class ParallelTrajReader(TrajReader):
    def process_config(self):
        self.config.title = "Replicas (row)"
        self.config.mode = "matrix"

        parent_dir = Path(self.config.re_dir)
        sampler = FreeEnergySampler.from_h5(get_checked_path(parent_dir / "energy.h5"))
        i_sorted = sort_temperatures(sampler.temperatures)
        k_reverse = [i_sort for k, i_sort in enumerate(i_sorted)]
        n_replica = len(sampler.temperatures)
        self.config.opt_keys = list(sampler.var_kt.keys())

        self.config.trajectories = [
            str(parent_dir / f"trajectory-{i}.h5") for i in range(n_replica)
        ]
        self.traj_manager = self.get_traj_manager()
        self.views_yaml = Path(self.config.trajectories[0]).with_suffix(".views.yaml")

        self.config.strip = []
        for i_traj in range(self.traj_manager.get_n_trajectories()):
            n_frame = self.traj_manager.get_n_frame(i_traj)
            self.config.strip.append(
                [dict(iFrameTraj=[i, i_traj], p=i / n_frame) for i in range(n_frame)]
            )

        rows = [sampler.var_kt[self.config.key][i] for i in i_sorted]
        p_rows = convert_rows_to_p_rows(rows)
        n_sample_max = py_.max([len(row) for row in rows])
        matrix = [[0 for k in range(n_replica)] for t in range(n_sample_max)]
        for k, row in enumerate(rows):
            offset = n_sample_max - len(row)
            for t, value in enumerate(row):
                matrix[t + offset][k] = {
                    "value": value,
                    "p": p_rows[k][t],
                    "label": f"u={value:.3f}",
                    "iFrameTraj": [t, k_reverse[k]],
                }
        self.config.matrix = matrix


class FoamTrajReader(TrajReader):
    def get_traj_manager(self):
        return FoamTrajectoryManager(
            self.config.trajectories,
            mode="a",
            is_dry_cache=not self.config.is_solvent,
        )

    def get_tags(self):
        return {"foam": self.config.trajectories[0]}

    def process_config(self):
        super().process_config()

        h5 = self.traj_manager.get_traj_file(0)

        # As the coordinates are superposed frame by frame, it's important
        # that the first frame (which is the reference frame) is correctly
        # loaded. Here, we determine the first frame

        if h5.has_dataset("json_rshow_matrix") or h5.has_dataset("rshow_matrix"):
            if h5.has_dataset("json_rshow_matrix"):
                data = h5.get_json_dataset("json_rshow_matrix")
            elif h5.has_dataset("rshow_matrix"):
                data = h5.get_json_dataset("rshow_matrix")
            if py_.has(data, "matrix"):
                # in case the key-value object was loaded
                self.config.matrix = data["matrix"]
            else:
                # in case just the matrix was loaded
                self.config.matrix = data
            self.config.mode = "sparse-matrix"
            logger.info("load matrix in init")
            value = get_first_value(self.config.matrix)
            self.config.i_frame_first = value["iFrameTraj"][0]

        if self.config.mode == "strip":
            self.config.i_frame_first = -1

        # Load the first frame
        logger.info("load first frame in init")
        self.read_frame_traj([self.config.i_frame_first, 0])

    def get_views(self):
        h5 = self.traj_manager.get_traj_file(0)
        if h5.has_dataset("json_views"):
            return h5.get_json_dataset("json_views")
        return []

    def save_views(self, views):
        h5 = self.traj_manager.get_traj_file(0)
        h5.set_json_dataset("json_views", views)

    def update_view(self, view):
        views = self.get_views()
        self.save_views(update_view(views, view))
        return {"success": True}

    def delete_view(self, to_delete_view):
        views = self.get_views()
        delete_view(views, to_delete_view)
        self.save_views(views)


class FoamEnsembleReader(RshowReaderMixin):
    """
    self.config
        table
            iFoamCol: int
            iFrameCol: int
            headers: [str]
            rows:
                - vals: [str]
                  iFrameTraj: [int, int]
    """

    def __init__(self, config={}):
        self.config = Dict(config)
        self.traj_manager = None
        self.process_config()

    def get_config(self, k) -> Any:
        return None

    def get_tags(self) -> dict:
        return {"csv": self.config.ensemble_id + ".csv"}

    def read_frame_traj(self, i_frame_traj: [int, int] = None) -> mdtraj.Trajectory:
        pass

    def process_config(self):
        ensemble_id = self.config.ensemble_id
        self.config.title = ensemble_id
        self.config.mode = "table"

        print(f"FoamEnsembleReader.process_config {self.config.csv}")
        self.config.table = Dict(
            ensembe_id=ensemble_id,
            rows=[],
            headers=[],
            iAtomMask=None,
            iFoamCol=None,
            iFrameCol=None,
        )
        with open(self.config.csv) as f:
            i_frame_col = None
            i_foam_col = None
            i_atom_mask = None
            for i, row in enumerate(csv.reader(f)):
                j = i - 1
                if i == 0:
                    self.config.table.headers.extend(row)
                    for label in ["foam_id", "foamid"]:
                        if label in self.config.table.headers:
                            i_foam_col = self.config.table.headers.index(label)
                            self.config.table.iFoamCol = i_foam_col
                            break
                    for label in ["i_frame", "foam_frame_idx"]:
                        if label in self.config.table.headers:
                            i_frame_col = self.config.table.headers.index(label)
                            self.config.table.iFrameCol = i_frame_col
                            break
                    for label in ["atom_mask"]:
                        if label in self.config.table.headers:
                            i_atom_mask = self.config.table.headers.index(label)
                            self.config.table.iAtomMask = i_atom_mask
                            break
                    if i_atom_mask is None:
                        i_atom_mask = len(self.config.table.headers)
                        self.config.table.headers.append("atom_mask")
                        self.config.table.iAtomMask = i_atom_mask
                    logger.info(
                        f"i_foam_col {i_foam_col} i_frame_col {i_frame_col} i_atom_mask {i_atom_mask}"
                    )
                else:
                    foam_id = row[i_foam_col]
                    frame = row[i_frame_col] if i_frame_col is not None else -1
                    if len(row) < len(self.config.table.headers):
                        row.append("")
                    result = {"vals": row}
                    try:
                        i_frame_traj = [int(frame), int(foam_id)]
                        if i_atom_mask is not None:
                            i_frame_traj.append(row[i_atom_mask])
                        result["iFrameTraj"] = i_frame_traj
                    except:
                        logger.warning(f"couldn't find foam_id in row {j}")
                    self.config.table.rows.append(result)

    def add_row(self, foam_id, frame, atom_mask=None):
        table = self.config.table
        headers = table.headers
        n = len(headers)
        i_frame_traj = [int(frame), int(foam_id)]
        if atom_mask:
            i_frame_traj.append(atom_mask)
        row = {"vals": [""] * n, "iFrameTraj": i_frame_traj}
        iFoamCol = table["iFoamCol"]
        if not py_.is_none(iFoamCol):
            row["vals"][iFoamCol] = int(foam_id)
        iFrameCol = table["iFrameCol"]
        if not py_.is_none(iFrameCol):
            row["vals"][iFrameCol] = int(frame)
        iAtomMask = table["iAtomMask"]
        if not py_.is_none(iAtomMask):
            row["vals"][iAtomMask] = atom_mask
        table["rows"].append(row)

    def update_row(self, i_row, foam_id, frame, atom_mask=None):
        i_frame_traj = [int(frame), int(foam_id)]
        if atom_mask:
            i_frame_traj.append(atom_mask)
        table = self.config.table
        row = table["rows"][i_row]
        row["iFrameTraj"] = i_frame_traj
        iFoamCol = table["iFoamCol"]
        if not py_.is_none(iFoamCol):
            row["vals"][iFoamCol] = int(foam_id)
        iFrameCol = table["iFrameCol"]
        if not py_.is_none(iFrameCol):
            row["vals"][iFrameCol] = int(frame)
        iAtomMask = table["iAtomMask"]
        if not py_.is_none(iAtomMask):
            row["vals"][iAtomMask] = atom_mask

    def remove_row(self, i_row):
        del self.config.table["rows"][i_row]

    def save(self):
        with open(self.config.csv, "w") as f:
            writer = csv.writer(f)
            table = self.config.table
            writer.writerow(table.headers)
            for row in table["rows"]:
                writer.writerow(row["vals"])

    def get_views(self):
        views_yaml = Path(self.config.csv).parent / "views.yaml"
        if views_yaml.exists():
            return load_yaml(views_yaml)
        return []

    def save_views(self, views):
        views_yaml = Path(self.config.csv).parent / "views.yaml"
        dump_yaml(views, views_yaml)

    def update_view(self, view):
        views = self.get_views()
        self.save_views(update_view(views, view))
        return {"success": True}

    def delete_view(self, to_delete_view):
        views = self.get_views()
        delete_view(views, to_delete_view)
        self.save_views(views)
