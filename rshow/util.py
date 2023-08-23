from rich.pretty import pprint
import numpy


def get_i_frame_min(matrix):
    entries = []
    max_cvs = [-1e30, -1e30]
    for row in matrix:
        for cell in row:
            label = cell.get("label")
            if not label:
                continue
            cvs = parse_cv_from_label(label)
            for i_cv in range(2):
                if cvs[i_cv] > max_cvs[i_cv]:
                    max_cvs[i_cv] = cvs[i_cv]
            if "iFrameTraj" in cell:
                i_frame = cell["iFrameTraj"][0]
                value = cell.get("value")
                if value is None:
                    continue
                entries.append(
                    {
                        "i_frame": cell["iFrameTraj"][0],
                        "value": float(cell["value"]),
                        "cv": cvs,
                    }
                )
    cutoff_cvs = [0.95 * cv for cv in max_cvs]
    for entry in entries:
        for i_cv in range(2):
            if entry["cv"][i_cv] > cutoff_cvs[i_cv]:
                entry["value"] = 0.0
    entries.sort(key=lambda e: e["value"])
    return entries[0]["i_frame"]


def parse_cv_from_label(label):
    label = label.split("=")[1].replace("fe", "")
    pieces = label.split(",")
    return [float(p) for p in pieces]


def get_pair_distances(dpairs, h5, atom_indices):
    i_raw_atom_by_i_atom = {}
    for dpair in dpairs:
        for i_atom in dpair["i_atom1"], dpair["i_atom2"]:
            i_raw_atom_by_i_atom[i_atom] = atom_indices[i_atom]
    lookup_atom_indices = list(i_raw_atom_by_i_atom.values())
    lookup_atom_indices.sort()

    topology = h5.fetch_topology(atom_indices)
    for dpair in dpairs:
        atom1 = topology.atom(dpair["i_atom1"])
        atom2 = topology.atom(dpair["i_atom2"])
        dpair["label"] = f"{atom1}::{atom2}"

    n_frame = h5.get_n_frame()
    data = h5.read_atom_dataset_progressively(
        "coordinates", slice(0, n_frame), lookup_atom_indices
    )
    pprint(data.shape)

    def get_i(i_atom):
        i_raw_atom = i_raw_atom_by_i_atom[i_atom]
        return lookup_atom_indices.index(i_raw_atom)

    for dpair in dpairs:
        pprint(dpair)
        i_atom1 = get_i(dpair["i_atom1"])
        i_atom2 = get_i(dpair["i_atom2"])
        values = []
        for i_frame in range(n_frame):
            p1 = data[i_frame][i_atom1]
            p2 = data[i_frame][i_atom2]
            values.append(numpy.linalg.norm(p1 - p2) * 10)
        dpair["values"] = values

    return dpairs
