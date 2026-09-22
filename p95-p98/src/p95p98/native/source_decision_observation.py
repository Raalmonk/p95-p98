"""Bounded source-only Cartesian observations, without scoring or validity gates.

Loops and polymer edges use zero-based inclusive indices. Exports use explicit
one-based residue ``index`` values. Displacement is in the shared raw coordinate
frame (no alignment). Torsions are signed degrees in [-180, 180].
"""
import math
from copy import deepcopy
from collections.abc import Mapping


def normalize_source_export(export):
    """Copy an ordered native export and bind its implicit indices to projection.

    Exports already containing indices are copied unchanged for the observation
    validator. Missing indices require an explicit full sequence and topology,
    equal residue counts and matching per-position residue names. No connectivity
    is inferred and no atom or coordinate is rewritten.
    """
    if not isinstance(export, Mapping) or not isinstance(export.get("residues"), (list, tuple)):
        raise ValueError("Export residues required")
    rows = export["residues"]
    if any("index" in row for row in rows):
        if not all(type(row.get("index")) is int and row["index"] == i+1 for i, row in enumerate(rows)):
            raise ValueError("Mixed or nonconsecutive export indices")
        return deepcopy(export)
    projection = export.get("projection", {})
    sequence, topology = projection.get("sequence"), projection.get("topology")
    if not isinstance(sequence, str) or not isinstance(topology, (list, tuple)) or not len(rows) == len(sequence) == len(topology):
        raise ValueError("Unindexed export requires full ordered sequence/topology")
    for row, entry in zip(rows, topology):
        if (not isinstance(entry, (list, tuple)) or len(entry) != 2 or
                not isinstance(entry[0], str) or row.get("name") != entry[0].split(":")[0] or
                not isinstance(entry[1], (list, tuple)) or not all(isinstance(a, str) for a in entry[1])):
            raise ValueError("Ordered residue/topology identity differs")
        if not isinstance(row.get("atoms"), Mapping) or not set(row["atoms"]) <= {a.strip() for a in entry[1]}:
            raise ValueError("Export atom identity differs from source topology")
    result = deepcopy(export)
    for i, row in enumerate(result["residues"]):
        row["index"] = i+1
    return result


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected finite numeric value")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Expected finite numeric value")
    return value


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _distance(a, b):
    return _number(math.dist(a, b))


def _torsion(points):
    if any(p is None for p in points):
        return None
    b0 = _sub(points[0], points[1])
    b1 = _sub(points[2], points[1])
    b2 = _sub(points[3], points[2])
    norm = math.hypot(*b1)
    if norm == 0:
        return None
    axis = tuple(x / norm for x in b1)
    v = _sub(b0, tuple(_dot(b0, axis)*x for x in axis))
    w = _sub(b2, tuple(_dot(b2, axis)*x for x in axis))
    nv, nw = math.hypot(*v), math.hypot(*w)
    if nv == 0 or nw == 0:
        return None
    v, w = tuple(x/nv for x in v), tuple(x/nw for x in w)
    return _number(math.degrees(math.atan2(_dot(_cross(axis, v), w), _dot(v, w))))


def _value(value):
    return {"available": value is not None, "value": value}


def _exports(raw, current, sequence):
    raw, current = normalize_source_export(raw), normalize_source_export(current)
    result = []
    for export in (raw, current):
        if not isinstance(export, Mapping):
            raise ValueError("Export must be a mapping")
        rows = export.get("residues")
        if not isinstance(rows, (list, tuple)) or len(rows) != len(sequence):
            raise ValueError("Residue correspondence differs")
        projection = export.get("projection", {})
        if "sequence" in projection and projection["sequence"] != sequence:
            raise ValueError("Export sequence differs")
        atoms = []
        for i, row in enumerate(rows):
            if type(row.get("index")) is not int or row["index"] != i + 1:
                raise ValueError("Explicit consecutive one-based export indices required")
            if "aa" in row and row["aa"] != sequence[i]:
                raise ValueError("Export amino-acid identity differs")
            source_atoms = row.get("atoms")
            if not isinstance(source_atoms, Mapping):
                raise ValueError("Export atoms must be a mapping")
            clean = {}
            for name, xyz in source_atoms.items():
                if not isinstance(name, str) or not isinstance(xyz, (list, tuple)) or len(xyz) != 3:
                    raise ValueError("Invalid atom coordinate")
                clean[name] = tuple(_number(x) for x in xyz)
            atoms.append(clean)
        result.append(atoms)
    for a, b in zip(raw["residues"], current["residues"]):
        for key in ("aa", "name", "chain", "residue_id"):
            if a.get(key) != b.get(key):
                raise ValueError("Raw/current residue identity differs")
    return result


def observe_decision_state(raw_export, current_export, *, sequence, loops,
                           polymer_edges, per_residue_energy=None):
    """Observe 1–2 disjoint loops plus up to two connected flanks per side.

    ``per_residue_energy`` is an optional sequence of already weighted values
    (or None per missing residue), one entry per source residue. No energy is
    calculated. Contact counts use available CA pairs at <=8 A, excluding pairs
    separated by <=2 explicitly connected polymer edges. Completeness is explicit.
    """
    if not isinstance(sequence, str) or not 1 <= len(sequence) <= 5000 or any(
            aa not in "ACDEFGHIKLMNPQRSTVWYBXZJUO" for aa in sequence):
        raise ValueError("Expected source amino-acid sequence of length 1..5000")
    n = len(sequence)
    if not isinstance(loops, (list, tuple)) or not 1 <= len(loops) <= 2:
        raise ValueError("Expected one or two loops")
    intervals, occupied = [], set()
    for pair in loops:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2 or
                any(type(x) is not int for x in pair) or not 0 <= pair[0] <= pair[1] < n):
            raise ValueError("Loops must be zero-based inclusive intervals")
        members = set(range(pair[0], pair[1] + 1))
        if members & occupied:
            raise ValueError("Loops must be disjoint")
        occupied.update(members)
        intervals.append(tuple(pair))
    edges = set()
    if not isinstance(polymer_edges, (list, tuple, set, frozenset)):
        raise ValueError("Explicit source polymer edges required")
    for pair in polymer_edges:
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2 or
                any(type(x) is not int for x in pair) or not 0 <= pair[0] < n - 1 or pair[1] != pair[0] + 1):
            raise ValueError("Polymer edges must be adjacent increasing zero-based pairs")
        if tuple(pair) in edges:
            raise ValueError("Duplicate polymer edge")
        edges.add(tuple(pair))
    selected = set(occupied)
    for start, end in intervals:
        for direction, endpoint in ((-1, start), (1, end)):
            i = endpoint
            for _ in range(2):
                j = i + direction
                if (min(i, j), max(i, j)) not in edges:
                    break
                selected.add(j)
                i = j
    if len(selected) > 256:
        raise ValueError("Selected residue limit is 256; truncation is forbidden")
    raw, current = _exports(raw_export, current_export, sequence)
    if per_residue_energy is None:
        energies = [None] * n
    else:
        if not isinstance(per_residue_energy, (list, tuple)) or len(per_residue_energy) != n:
            raise ValueError("Weighted per-residue energy must match source length")
        energies = [None if x is None else _number(x) for x in per_residue_energy]

    def near(i, j):
        lo, hi = sorted((i, j))
        return hi - lo <= 2 and all((k, k+1) in edges for k in range(lo, hi))

    def contacts(i, exclude=()):
        ca = current[i].get("CA")
        eligible = [j for j in range(n) if j not in exclude and not near(i, j)]
        missing = sum("CA" not in current[j] for j in eligible)
        count = None if ca is None else sum(
            _distance(ca, current[j]["CA"]) <= 8.0 for j in eligible if "CA" in current[j])
        return {"available": ca is not None, "count": count,
                "complete": ca is not None and missing == 0,
                "eligible_partner_count": len(eligible), "missing_partner_ca_count": missing}

    displacement = {i: (_distance(raw[i]["CA"], current[i]["CA"])
                       if "CA" in raw[i] and "CA" in current[i] else None) for i in selected}
    residues = []
    for i in sorted(selected):
        atom = current[i].get
        before, after = (i-1, i) in edges, (i, i+1) in edges
        torsions = {
            "phi": _torsion([current[i-1].get("C"), atom("N"), atom("CA"), atom("C")]) if before else None,
            "psi": _torsion([atom("N"), atom("CA"), atom("C"), current[i+1].get("N")]) if after else None,
            "omega": _torsion([atom("CA"), atom("C"), current[i+1].get("N"), current[i+1].get("CA")]) if after else None,
        }
        residues.append({"index": i, "aa": sequence[i], "in_loop": i in occupied,
                         "torsions_degrees": {key: _value(val) for key, val in torsions.items()},
                         "ca_displacement_A": _value(displacement[i]),
                         "backbone_missing_count": sum(a not in current[i] for a in ("N", "CA", "C", "O")),
                         "nonlocal_ca_contacts": contacts(i),
                         "contacts_outside_loops": [{"loop_index": k, **contacts(i, range(s, e+1))}
                                                    for k, (s, e) in enumerate(intervals)],
                         "weighted_per_residue_energy": _value(energies[i])})

    def connection(a, b, kind):
        connected = (a, b) in edges
        c = current[a].get("C") if 0 <= a < n else None
        nn = current[b].get("N") if 0 <= b < n else None
        distance = _distance(c, nn) if connected and c is not None and nn is not None else None
        return {"residues": [a, b], "kind": kind, "polymer_edge_present": connected,
                "missing_c": c is None, "missing_n": nn is None, "distance_A": _value(distance)}

    summaries = []
    for k, (s, e) in enumerate(intervals):
        values = [displacement[i] for i in range(s, e+1) if displacement[i] is not None]
        cs = [contacts(i, range(s, e+1)) for i in range(s, e+1)]
        summaries.append({"loop_index": k, "start": s, "end": e,
                          "ca_displacement_mean_A": _value(math.fsum(v / len(values) for v in values) if values else None),
                          "ca_displacement_max_A": _value(max(values) if values else None),
                          "ca_displacement_observed_count": len(values),
                          "ca_displacement_missing_count": e-s+1-len(values),
                          "connections": [connection(s-1, s, "left_seam")] +
                              [connection(i, i+1, "internal") for i in range(s, e)] +
                              [connection(e, e+1, "right_seam")],
                          "outside_loop_ca_contacts": {
                              "count": (sum(c["count"] for c in cs if c["count"] is not None)
                                        if any(c["available"] for c in cs) else None),
                              "complete": all(c["complete"] for c in cs),
                              "observed_residue_count": sum(c["available"] for c in cs)}})
    return {"schema": "source-decision-observation-v1", "index_base": 0,
            "sequence_length": n, "contact_cutoff_A": 8.0,
            "energy_supplied": per_residue_energy is not None,
            "residues": residues, "loops": summaries}
