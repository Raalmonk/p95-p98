"""Source-only geometry primitives extracted from pdb_metrics."""
from dataclasses import dataclass, field
import math
import numpy as np

IDEAL_BACKBONE_BOND_LENGTHS_A = {'N-CA': 1.458, 'CA-C': 1.525, 'C-N': 1.329}

class PDBMetricError(ValueError):
    """Raised for missing, malformed, or non-comparable coordinate sets."""

@dataclass
class Residue:
    name: str
    chain: str
    number: int
    insertion_code: str
    atoms: dict[str, np.ndarray] = field(default_factory=dict)
    elements: dict[str, str] = field(default_factory=dict)


def backbone_bond_rms_error(residues: list[Residue]) -> float:
    """Return RMS error from ideal N-CA, CA-C, and inter-residue C-N bond lengths."""

    errors: list[float] = []
    for index, residue in enumerate(residues):
        missing = {"N", "CA", "C"} - set(residue.atoms)
        if missing:
            raise PDBMetricError(
                f"missing backbone atoms at canonical residue {index + 1}: {sorted(missing)}"
            )
        errors.append(
            float(np.linalg.norm(residue.atoms["N"] - residue.atoms["CA"]))
            - IDEAL_BACKBONE_BOND_LENGTHS_A["N-CA"]
        )
        errors.append(
            float(np.linalg.norm(residue.atoms["CA"] - residue.atoms["C"]))
            - IDEAL_BACKBONE_BOND_LENGTHS_A["CA-C"]
        )
        if index + 1 < len(residues):
            next_residue = residues[index + 1]
            if "N" not in next_residue.atoms:
                raise PDBMetricError(
                    f"missing backbone atom N at canonical residue {index + 2}"
                )
            errors.append(
                float(np.linalg.norm(residue.atoms["C"] - next_residue.atoms["N"]))
                - IDEAL_BACKBONE_BOND_LENGTHS_A["C-N"]
            )
    if not errors:
        raise PDBMetricError("no backbone bonds available for geometry validation")
    values = np.asarray(errors, dtype=float)
    return float(np.sqrt(np.mean(values * values)))


def clashscore(residues: list[Residue], cutoff_A: float = 1.8) -> float:
    coords: list[np.ndarray] = []
    residue_ids: list[int] = []
    for residue_index, residue in enumerate(residues):
        for atom, xyz in residue.atoms.items():
            if residue.elements.get(atom, "") == "H" or atom.startswith("H"):
                continue
            coords.append(xyz)
            residue_ids.append(residue_index)
    if not coords:
        return float("inf")
    xyz = np.vstack(coords)
    rid = np.asarray(residue_ids, dtype=int)
    count = 0
    for i in range(len(xyz) - 1):
        eligible = np.abs(rid[i + 1 :] - rid[i]) > 1
        if not np.any(eligible):
            continue
        distances = np.linalg.norm(xyz[i + 1 :] - xyz[i], axis=1)
        count += int(np.count_nonzero((distances < cutoff_A) & eligible))
    return float(1000.0 * count / len(xyz))
