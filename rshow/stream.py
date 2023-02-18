import csv
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

import mdtraj
import numpy as np
import parmed
import pydash as py_
from addict import Dict
from rseed.formats.easyh5 import EasyFoamTrajH5, EasyTrajH5
from rseed.formats.pdb import filter_for_atom_lines, get_pdb_lines_of_traj_frame
from rseed.formats.stream import StreamingTrajectoryManager, TrajectoryManager
from rseed.freeenergy import (
    FreeEnergySampler,
    FreeEnergySurface,
    get_matrix,
    sort_temperatures,
)
from rseed.granary import Granary
from rseed.util.alphaspace import AlphaSpace
from rseed.util.fs import (
    dump_yaml,
    get_checked_path,
    get_empty_path_str,
    get_yaml_str,
    load_yaml,
)
from rseed.util.ligand import iter_ff_mol_from_file
from rseed.util.select import select_mask
from rseed.util.struct import get_parmed_from_traj_frame, get_traj_frame_from_parmed


class RshowStreamMixin(ABC):
    """
    Interface to the webclient in Rshow
    """

    @abstractmethod
    def __init__(self, config={}):
        pass

    @abstractmethod
    def process_config(self):
        pass

    @abstractmethod
    def get_config(self, k) -> Any:
        pass

    @abstractmethod
    def get_frame(self, i_frame_traj: [int, int] = None) -> mdtraj.Trajectory:
        pass

    def get_pdb_lines(self, i_frame_traj: [int, int]):
        logger.info(f"pdb {i_frame_traj}")
        return filter_for_atom_lines(
            get_pdb_lines_of_traj_frame(self.get_frame(i_frame_traj))
        )

    def get_pdb_lines_with_alphaspace(self, i_frame_traj: [int, int]):
        pmd = get_parmed_from_traj_frame(self.get_frame())

        i_protein_atoms = select_mask(pmd, "protein")
        alpha_space = AlphaSpace(self.get_frame().atom_slice(i_protein_atoms))
        alpha_space_pdb_lines = alpha_space.get_pdb_lines()

        alpha_pdb = get_empty_path_str("alphaspace.pdb")
        with open(alpha_pdb, "w") as f:
            f.write("\n".join(alpha_space_pdb_lines))
        logger.info(f"alphaspace({alpha_pdb} {i_frame_traj}")

        pdb_lines = self.get_pdb_lines(i_frame_traj)
        pdb_lines.extend(alpha_space_pdb_lines)
        return pdb_lines

    def get_views(self):
        return []

    def add_view(self, view):
        return {}

    def delete_view(self, view):
        return {}


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
        views.append(update_view)
    return views


def delete_view(views, to_delete_view):
    i = get_i_view(views, to_delete_view)
    if i is not None:
        del views[i]
    return views


class TrajStream(RshowStreamMixin):
    def __init__(self, config={}):
        self.config = Dict(
            mode="strip",  # "strip", "matrix", "sparse-matrix", "matrix-strip", "table"
            strip=[],  # Dictionary of frame, traj, colours for use in rshow
            title="",  # Title for rshow
            is_hydrogen=True,  # Keep hydrogen atoms
            is_solvent=True,
            atom_mask="",
        )
        self.config.update(config)
        self.i_frame_traj = None
        self.frame = None
        self.process_config()

    def get_atom_mask(self):
        atom_mask = ""
        if not self.config.atom_mask:
            if not self.config.is_solvent and not self.config.is_hydrogen:
                atom_mask = "intersect {not {solvent}} {not {mdtraj element H}}"
            elif not self.config.is_solvent:
                atom_mask = "not {solvent}"
            elif not self.config.is_hydrogen:
                atom_mask = "not {mdtraj element H}"
        else:
            atom_mask = self.config.atom_mask
        return atom_mask

    def get_traj_manager(self):
        return TrajectoryManager(
            self.config.trajectories, atom_mask=self.get_atom_mask()
        )

    def get_title(self):
        names = [Path(t).name for t in self.config.trajectories]
        if len(names) == 1:
            return f"Trajectory of {names[0]}"
        elif len(names) >= 1:
            return "Trajectories of:\n" + "\n".join(names)
        else:
            raise ValueError("No trajectories found.")

    def process_config(self):
        self.config.title = self.get_title()
        self.traj_manager = self.get_traj_manager()
        self.views_yaml = Path(self.config.trajectories[0]).with_suffix(".views.yaml")
        self.config.mode = "strip"
        self.config.strip = []
        for i_traj in range(self.traj_manager.get_n_trajectories()):
            n_frame = self.traj_manager.get_n_frame(i_traj)
            self.config.strip.append(
                [dict(iFrameTraj=[i, i_traj], p=i / n_frame) for i in range(n_frame)]
            )

    def get_config(self, k):
        return self.config[k]

    def get_frame(self, i_frame_traj=None):
        if i_frame_traj and i_frame_traj != self.i_frame_traj:
            new_frame = self.traj_manager.get_frame_traj(i_frame_traj)
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

    def add_view(self, view):
        views = self.get_views()
        update_view(views, view)
        dump_yaml(views, self.views_yaml)
        return {}

    def delete_view(self, to_delete_view):
        views = self.get_views()
        delete_view(views, to_delete_view)
        logger.info(f"delete_view view:{to_delete_view['id']}")
        dump_yaml(views, self.views_yaml)


class FoamTrajStream(TrajStream):
    def get_traj_manager(self):
        mask = self.get_atom_mask()
        return StreamingTrajectoryManager(
            self.config.trajectories, atom_mask=mask, is_foamdb=True
        )

    def get_title(self):
        return f"Connected: FoamDB {self.config.trajectories[0]}"

    def process_config(self):
        super().process_config()
        from rseed.formats.easyh5 import EasyFoamTrajH5

        h5: EasyFoamTrajH5 = self.traj_manager.get_h5(0)
        if h5.has_dataset("rshow_matrix"):
            self.config.matrix = h5.get_json_dataset("rshow_matrix")
            self.config.mode = "sparse-matrix"

    def get_views(self):
        h5: EasyFoamTrajH5 = self.traj_manager.get_h5(0)
        if h5.has_dataset("json_views"):
            return h5.get_json_dataset("json_views")
        return []

    def save_views(self, views):
        h5: EasyFoamTrajH5 = self.traj_manager.get_h5(0)
        h5.set_json_dataset("json_views", views)

    def add_view(self, view):
        views = self.get_views()
        self.save_views(update_view(views, view))
        return {"success": True}

    def delete_view(self, to_delete_view):
        views = self.get_views()
        delete_view(views, to_delete_view)
        self.save_views(views)


class FrameStream(TrajStream):
    def process_config(self):
        self.config.title = f"frame: {self.config.pdb_or_parmed}"
        self.config.mode = "frame"
        fname = Path(self.config.pdb_or_parmed)
        if fname.suffix == ".parmed":
            self.frame = get_traj_frame_from_parmed(Granary(fname).structure)
        else:
            self.frame = mdtraj.load_pdb(self.config.pdb_or_parmed)
        return True

    def get_frame(self, i_frame_traj=None):
        return self.frame

    def get_title(self):
        return self.config.title


class FesStream(TrajStream):
    def process_config(self):
        self.config.title = "Free-energy surface of collective variables"
        self.config.mode = "sparse-matrix"
        if self.config.n_bin:
            fes = FreeEnergySurface(self.config.metad_dir)
            fes.coarse_grain(n_bins=self.config.n_bin)
            data = fes.export()
            self.config.matrix = data.matrix
            self.config.trajectories = [fes.trajectory_path]
        else:
            data = get_matrix(self.config.metad_dir)
            self.config.matrix = data.matrix
            self.config.trajectories = data.trajectories
        self.traj_manager = TrajectoryManager(
            self.config.trajectories, atom_mask=self.get_atom_mask()
        )
        self.views_yaml = Path(self.config.trajectories[0]).with_suffix(".views.yaml")


class MatrixStream(TrajStream):
    def process_config(self):
        fname = Path(self.config.matrix_yaml)
        if fname.is_dir():
            fname = fname / "matrix.yaml"
        data = load_yaml(fname, is_addict=True)
        parent_dir = Path(fname).parent
        self.config.matrix = data.matrix
        self.config.title = "Matrix"
        self.config.trajectories = data.trajectories
        if not self.config.mode:
            self.config.mode = "matrix-strip"
        os.chdir(parent_dir)
        self.traj_manager = TrajectoryManager(
            self.config.trajectories, atom_mask=self.get_atom_mask()
        )
        self.views_yaml = fname.with_suffix(".views.yaml")


class LigandsStream(TrajStream):
    def process_config(self):
        self.config.title = f"Ligands for {Path(self.config.pdb).name}"
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
                        self.config.table[i - 1]["vals"].extend(row)
        self.views_yaml = Path(pdb).with_suffix(".views.yaml")

    def get_ligand_pdb_lines(self, i_ligand):
        traj = get_traj_frame_from_parmed(self.ligand_parmeds[i_ligand])
        return get_pdb_lines_of_traj_frame(traj)

    def get_pdb_lines(self, i_frame_traj):
        i_frame = i_frame_traj[0]
        return self.receptor_lines + self.get_ligand_pdb_lines(i_frame)


def convert_rows_to_p_rows(rows):
    values = py_.flatten_deep(rows)
    max_val = py_.max_(values)
    min_val = py_.min_(values)
    delta_val = max_val - min_val
    return [
        [(v - min_val) / delta_val if delta_val else 0 for v in row] for row in rows
    ]


class ParallelStream(TrajStream):
    def process_config(self):
        self.config.title = f"Replicas (row)"
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
        self.traj_manager = TrajectoryManager(
            trajectories=self.config.trajectories, atom_mask=self.get_atom_mask()
        )
        self.views_yaml = Path(self.config.trajectories[0]).with_suffix(".views.yaml")

        self.config.strip = []
        for i_traj in range(self.traj_manager.get_n_trajectories()):
            n_frame = self.traj_manager.get_n_frame(i_traj)
            self.config.strip.append(
                [dict(iFrameTraj=[i, i_traj], p=i / n_frame) for i in range(n_frame)]
            )

        rows = [sampler.var_kt[self.config.key][i] for i in i_sorted]
        p_rows = convert_rows_to_p_rows(rows)
        n_sample_max = py_.max_([len(row) for row in rows])
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


class ParallelDockStream(TrajStream):
    def process_config(self):
        self.config.title = f"Replicas (row)"
        self.config.mode = "matrix"
        parent_dir = Path(self.config.re_dir)

        fname = parent_dir / "ligand-trajectory.h5"
        logger.info(f"load rigid-receptor and ligand conformations: {fname}")
        self.h5 = EasyTrajH5(fname)
        self.frame = self.h5.get_frame_traj(0)
        self.i_ligand_atoms = self.h5.get_dataset("i_ligand_atoms")[:]
        self.conformations_nm = self.h5.get_dataset("ligand_conformations")
        self.views_yaml = fname.with_suffix(".views.yaml")

        energy_h5 = parent_dir / "energy.h5"
        sampler = FreeEnergySampler.from_h5(get_checked_path(energy_h5))
        i_sorted = sort_temperatures(sampler.temperatures)
        k_reverse = [i_sort for k, i_sort in enumerate(i_sorted)]
        self.config.opt_keys = list(sampler.var_kt.keys())

        rows = [sampler.var_kt[self.config.key][i] for i in i_sorted]
        p_rows = convert_rows_to_p_rows(rows)
        i_ligand_kt = sampler.var_kt["i_ligand"]
        n_sample_max = py_.max_([len(row) for row in rows])

        matrix = [[0 for k in range(len(rows))] for t in range(n_sample_max)]
        for k, row in enumerate(rows):
            offset = n_sample_max - len(row)
            for t, value in enumerate(row):
                matrix[t + offset][k] = {
                    "value": value,
                    "p": p_rows[k][t],
                    "label": f"u={value:.3f}",
                    "iFrameTraj": [i_ligand_kt[k_reverse[k]][t], 0],
                }
        self.config.matrix = matrix

    def get_frame(self, i_frame_traj=None):
        i_frame = i_frame_traj[0]
        self.frame.xyz[0][self.i_ligand_atoms] = self.conformations_nm[i_frame]
        return self.frame
