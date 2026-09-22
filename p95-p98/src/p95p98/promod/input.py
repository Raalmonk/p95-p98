"""Source-only gap serialization, extracted from the evaluated input recipe."""
import hashlib
import json
from pathlib import Path

AA = dict(zip(('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL').split(),
              'ARNDCQEGHILKMFPSTWYV'))


def prepare_source(source_pdb, sequence, loops, output_dir):
    """Remove declared loop atoms from a complete target-sequence source model.

    Loop start/stop are one-based pose positions (inclusive). Missing residues,
    insertions, alternate conformers, ligands and explicit indexed connectivity
    are unsupported here: upstream preparation must supply a complete source.
    The final mapping uses pose positions and original chain labels, exactly as
    the evaluated input converter; it does not retain arbitrary PDB numbering.
    """
    if not sequence or any(a not in AA.values() for a in sequence):
        raise ValueError('Target sequence must use the 20 canonical amino acids')
    movable = set()
    for definition in loops:
        start, stop = definition['start'], definition['stop']
        if type(start) is not int or type(stop) is not int or not 1 <= start <= stop <= len(sequence):
            raise ValueError('Invalid one-based inclusive loop range')
        movable.update(range(start, stop+1))
    if not movable:
        raise ValueError('At least one nonempty loop is required')
    residues, segments, seen, atoms = [], [], set(), set()
    current = None
    new_segment = True
    model_count = 0
    for line in Path(source_pdb).read_text().splitlines(keepends=True):
        record = line[:6].strip()
        if record == 'MODEL':
            model_count += 1
            if model_count > 1:
                raise ValueError('Multiple source models are unsupported')
        if record == 'TER':
            new_segment = True
            current = None
            continue
        if record in ('LINK', 'CONECT', 'SSBOND', 'HETATM'):
            raise ValueError('Unsupported source chemistry record: '+record)
        if record != 'ATOM':
            continue
        if len(line) < 78 or line[16] != ' ' or line[26] != ' ':
            raise ValueError('Source requires PDB element columns, no alternate atoms or insertion codes')
        key = (line[21], int(line[22:26]))
        name = line[17:20].strip()
        if name not in AA:
            raise ValueError('Noncanonical source residue: '+name)
        if key != current:
            if key in seen:
                raise ValueError('Repeated source residue identity')
            seen.add(key)
            if new_segment or not segments or segments[-1]['source_chain'] != key[0]:
                segments.append(dict(source_chain=key[0], indices=[]))
            residues.append(dict(name=name, lines=[], atoms=set()))
            segments[-1]['indices'].append(len(residues))
            current, new_segment = key, False
        if residues[-1]['name'] != name:
            raise ValueError('Mixed residue identities')
        atom = line[12:16].strip()
        if (key, atom) in atoms:
            raise ValueError('Duplicate source atom')
        atoms.add((key, atom))
        residues[-1]['atoms'].add(atom)
        residues[-1]['lines'].append(line)
    if ''.join(AA[r['name']] for r in residues) != sequence:
        raise ValueError('Source residue sequence must exactly match the complete target sequence')
    if any(not {'N', 'CA', 'C', 'O'} <= r['atoms'] for r in residues):
        raise ValueError('Source requires complete N/CA/C/O backbone for every residue')
    labels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    if len(segments) > len(labels):
        raise ValueError('Too many source segments')
    serial, lines = 0, []
    for k, segment in enumerate(segments):
        positions = segment['indices']
        if positions[0] in movable or positions[-1] in movable:
            raise ValueError('Requested loop touches source segment terminus')
        segment['chain'] = labels[k]
        segment['sequence'] = ''.join(sequence[i-1] for i in positions)
        segment['aligned_source'] = ''.join('-' if i in movable else sequence[i-1] for i in positions)
        for j, i in enumerate(positions, 1):
            if i in movable:
                continue
            for line in residues[i-1]['lines']:
                if line[76:78].strip() in ('H', 'D'):
                    continue
                serial += 1
                if serial > 99999:
                    raise ValueError('PDB atom serial limit exceeded')
                lines.append(line[:6]+f'{serial:5d}'+line[11:21]+labels[k]+f'{j:4d}'+line[26:])
        lines.append('TER\n')
    lines.append('END\n')
    payload = ''.join(lines).encode()
    data = dict(status='READY', segments=segments,
                source_pdb_sha256=hashlib.sha256(payload).hexdigest(),
                expected_sequence=sequence, loop_pose_union=sorted(movable),
                reference_coordinates_opened=False)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output/'source.pdb').open('xb') as stream:
        stream.write(payload)
    with (output/'input.json').open('x') as stream:
        json.dump(data, stream, indent=2)
    return output/'input.json'
