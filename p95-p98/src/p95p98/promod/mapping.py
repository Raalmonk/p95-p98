"""Non-computing retained ProMod3 IO checks. No native imports or dispatch."""
from __future__ import annotations
import gzip
import hashlib
from pathlib import Path
from .errors import PreparationPending


def read_content(path):
    p = Path(path)
    if not p.exists() and Path(str(p) + '.gz').exists():
        p = Path(str(p) + '.gz')
    stored = p.read_bytes()
    content = gzip.decompress(stored) if stored.startswith(b'\x1f\x8b') else stored
    return content, dict(path=str(p), stored_sha256=hashlib.sha256(stored).hexdigest(),
                        content_sha256=hashlib.sha256(content).hexdigest())


def residue_mapping(data):
    mapping, destinations, chains = {}, set(), set()
    for s in data['segments']:
        chain, source = s['chain'], s['source_chain']
        if any(type(c) is not str or len(c) != 1 for c in (chain, source)) or chain in chains:
            raise PreparationPending('Duplicate or unsupported segment chain')
        chains.add(chain)
        if not s['indices']:
            raise PreparationPending('Empty segment')
        if 'sequence' in s and len(s['indices']) != len(s['sequence']):
            raise PreparationPending('Sequence and mapping lengths differ')
        for j, i in enumerate(s['indices'], 1):
            if type(i) is not int or not 1 <= i <= 9999 or (source, i) in destinations:
                raise PreparationPending('Duplicate or unsupported destination residue')
            destinations.add((source, i)); mapping[chain, j] = (i, source)
    return mapping


def map_output_lines(lines, data):
    """Strict one-model PDB projection; only chain and residue number may change."""
    mapping = residue_mapping(data)
    seen, atoms, output, closed = set(), set(), [], set()
    current, last, models = None, None, 0
    for line in lines:
        record = line[:6].strip()
        if record == 'MODEL':
            models += 1
            if models > 1: raise PreparationPending('Multiple output models')
        if record in ('ATOM', 'HETATM'):
            if len(line) < 54 or line[26] != ' ' or line[16] != ' ':
                raise PreparationPending('Unsupported insertion code or alternate atom')
            try: key = (line[21], int(line[22:26]))
            except ValueError as exc: raise PreparationPending('Invalid residue number') from exc
            if key not in mapping: raise PreparationPending('Unmapped output residue')
            if current != key:
                if key in seen or key[0] in closed: raise PreparationPending('Repeated output residue or chain')
                seen.add(key); current = key
            atom = (key, line[12:16])
            if atom in atoms: raise PreparationPending('Duplicate output atom')
            atoms.add(atom)
            index, chain = mapping[key]
            output.append(line[:21] + chain + f'{index:4d}' + line[26:]); last = key
        elif record == 'TER':
            if last is None: raise PreparationPending('TER without preceding residue')
            if len(line.rstrip('\n')) >= 26:
                try: key = (line[21], int(line[22:26]))
                except ValueError as exc: raise PreparationPending('Invalid TER') from exc
                if key != last: raise PreparationPending('TER identity differs')
                index, chain = mapping[key]
                line = line[:21] + chain + f'{index:4d}' + line[26:]
            closed.add(last[0]); current = None; last = None; output.append(line)
        elif record in ('ANISOU', 'SIGATM', 'SIGUIJ', 'LINK', 'SSBOND', 'CONECT'):
            raise PreparationPending('Unsupported indexed PDB record: ' + record)
        else: output.append(line)
    if seen != set(mapping): raise PreparationPending('Incomplete native sequence mapping')
    return output


def sequence_coverage(model, data):
    """Inspect an OST entity without energy, atom rebuilding or geometry changes."""
    expected = {(s['chain'], j): aa for s in data['segments']
                for j, aa in enumerate(s['sequence'], 1)}
    residue_mapping(data)
    actual = {}
    for chain in model.chains:
        for residue in chain.residues:
            number = residue.GetNumber()
            key = (chain.name, number.GetNum())
            # OST 2.12 represents absent insertion codes as a NUL character.
            # Keep rejecting genuine insertion codes and duplicate identities.
            if str(number.GetInsCode()) not in ('', ' ', '\x00') or key in actual:
                raise PreparationPending('Ambiguous native residue identity')
            actual[key] = residue.one_letter_code
    return dict(complete=actual == expected, expected_residues=len(expected),
                actual_residues=len(actual), missing=len(expected.keys()-actual.keys()),
                extra=len(actual.keys()-expected.keys()),
                sequence_mismatches=sum(actual[k] != expected[k] for k in actual.keys() & expected.keys()))


def reuse_disposition(*, metadata_match, source_verified=False, endpoint_verified=False):
    """IO evidence alone can never grant execution-cache readiness."""
    level = 'UNVERIFIED'
    if metadata_match: level = 'METADATA_MATCH'
    if metadata_match and source_verified: level = 'SOURCE_CONSTRUCTION_VERIFIED'
    if metadata_match and source_verified and endpoint_verified: level = 'RETAINED_ENDPOINT_LOAD_VERIFIED'
    return dict(level=level, exact_operation_cache_ready=False,
                missing=['exact_parent_state_and_topology', 'ProMod3_pre_and_post_rng_state',
                         'method_and_runtime_binding', 'resource_binding', 'logical_price_binding',
                         'qualified_native_state_converter'],
                fixed_local_energy=None, fixed_global_energy=None)


def require_unstarted(folder):
    folder = Path(folder)
    if (folder/'native_started.json').exists() or (folder/'native_result.json').exists():
        raise PreparationPending('Retained operation requires reconciliation, never automatic retry')
