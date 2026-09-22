"""Extracted native resource identifiers and original BLOSUM62 constants."""
from __future__ import annotations
from typing import Any
import re
import hashlib
_AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")
_COORDINFO_ID_PATTERN = re.compile(r"(?i)(?:^|[^0-9A-Za-z])([0-9][A-Za-z0-9]{3})(?=$|[^0-9A-Za-z])", re.ASCII)
_ASCII_EDGE_WHITESPACE = "\t\n\v\f\r "
_ASCII_LOWER_TRANSLATION = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
_ASCII_UPPER_TRANSLATION = str.maketrans("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_DATABASE_SEQUENCE_REMOVALS = str.maketrans("", "", "\t\n\v\f\r -.")
_BLOSUM62_ORDER = "ARNDCQEGHILKMFPSTWYV"
_BLOSUM62_ROWS = (
    (4, -1, -2, -2, 0, -1, -1, 0, -2, -1, -1, -1, -1, -2, -1, 1, 0, -3, -2, 0),
    (-1, 5, 0, -2, -3, 1, 0, -2, 0, -3, -2, 2, -1, -3, -2, -1, -1, -3, -2, -3),
    (-2, 0, 6, 1, -3, 0, 0, 0, 1, -3, -3, 0, -2, -3, -2, 1, 0, -4, -2, -3),
    (-2, -2, 1, 6, -3, 0, 2, -1, -1, -3, -4, -1, -3, -3, -1, 0, -1, -4, -3, -3),
    (0, -3, -3, -3, 9, -3, -4, -3, -3, -1, -1, -3, -1, -2, -3, -1, -1, -2, -2, -1),
    (-1, 1, 0, 0, -3, 5, 2, -2, 0, -3, -2, 1, 0, -3, -1, 0, -1, -2, -1, -2),
    (-1, 0, 0, 2, -4, 2, 5, -2, 0, -3, -3, 1, -2, -3, -1, 0, -1, -3, -2, -2),
    (0, -2, 0, -1, -3, -2, -2, 6, -2, -4, -4, -2, -3, -3, -2, 0, -2, -2, -3, -3),
    (-2, 0, 1, -1, -3, 0, 0, -2, 8, -3, -3, -1, -2, -1, -2, -1, -2, -2, 2, -3),
    (-1, -3, -3, -3, -1, -3, -3, -4, -3, 4, 2, -3, 1, 0, -3, -2, -1, -3, -1, 3),
    (-1, -2, -3, -4, -1, -2, -3, -4, -3, 2, 4, -2, 2, 0, -3, -2, -1, -2, -1, 1),
    (-1, 2, 0, -1, -3, 1, 1, -2, -1, -3, -2, 5, -1, -3, -1, 0, -1, -3, -2, -2),
    (-1, -1, -2, -3, -1, 0, -2, -3, -2, 1, 2, -1, 5, 0, -2, -1, -1, -1, -1, 1),
    (-2, -3, -3, -3, -2, -3, -3, -3, -1, 0, 0, -3, 0, 6, -4, -2, -2, 1, 3, -1),
    (-1, -2, -2, -1, -3, -1, -1, -2, -2, -3, -3, -1, -2, -4, 7, -1, -1, -4, -3, -2),
    (1, -1, 1, 0, -1, 0, 0, 0, -1, -2, -2, 0, -1, -2, -1, 4, 1, -3, -2, -2),
    (0, -1, 0, -1, -1, -1, -1, -2, -2, -1, -1, -1, -1, -2, -1, 1, 5, -2, -2, 0),
    (-3, -3, -4, -4, -2, -2, -3, -2, -2, -3, -2, -3, -1, 1, -4, -3, -2, 11, 2, -3),
    (-2, -2, -2, -3, -2, -1, -2, -3, 2, -1, -1, -2, -1, 3, -3, -2, -2, 2, 7, -1),
    (0, -3, -3, -3, -1, -2, -2, -3, -3, 3, 1, -2, 1, -1, -2, -2, 0, -3, -1, 4),
)
_BLOSUM62 = {
    (aa_i, aa_j): _BLOSUM62_ROWS[i][j]
    for i, aa_i in enumerate(_BLOSUM62_ORDER)
    for j, aa_j in enumerate(_BLOSUM62_ORDER)
}

def _db_sequence_string(value: Any) -> str:
    """Apply the contract's ASCII-only StructureDB sequence normalization."""

    if isinstance(value, str):
        candidate = value
    elif isinstance(value, bytes):
        candidate = value.decode("utf-8")
    else:
        candidate: Any = None
        for method_name in ("GetGaplessString", "GetString"):
            method = getattr(value, method_name, None)
            if callable(method):
                candidate = method()
                break
        if candidate is None:
            for attribute_name in ("string", "sequence"):
                attribute = getattr(value, attribute_name, None)
                if isinstance(attribute, (str, bytes)):
                    candidate = attribute
                    break
        if isinstance(candidate, bytes):
            candidate = candidate.decode("utf-8")
    if not isinstance(candidate, str):
        raise ValueError("StructureDB sequence is not representable as text")
    sequence = candidate.translate(_ASCII_UPPER_TRANSLATION).translate(
        _DATABASE_SEQUENCE_REMOVALS
    )
    if not sequence or any(aa not in _AMINO_ACIDS for aa in sequence):
        raise ValueError("StructureDB sequence is empty or nonstandard")
    return sequence


def _coordinfo_identity(value: Any) -> tuple[str, str | None, str]:
    """Return raw id, one valid PDB token if present, and whole-entry key."""

    if isinstance(value, bytes):
        raw_id = value.decode("utf-8")
    elif isinstance(value, str):
        raw_id = value
    else:
        raise ValueError("CoordInfo.id is not UTF-8 text")
    normalized = raw_id.strip(_ASCII_EDGE_WHITESPACE).translate(
        _ASCII_LOWER_TRANSLATION
    )
    matches = [match.group(1) for match in _COORDINFO_ID_PATTERN.finditer(normalized)]
    if len(matches) == 1:
        entry = matches[0].translate(_ASCII_LOWER_TRANSLATION)
        return raw_id, entry, entry
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return raw_id, None, f"unparseable:{digest}"

