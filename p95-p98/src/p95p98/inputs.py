"""Explicit prepared-structure input, independent of dataset identifiers."""
import math
from pathlib import Path
from .io import read

def load_input(path):
    path = Path(path).resolve()
    data = read(path)
    required = {'structure', 'sequence', 'loops', 'local_energy_residues', 'seed', 'input_kind'}
    if set(data) != required:
        raise ValueError('Input fields must be exactly: '+', '.join(sorted(required)))
    structure = Path(data['structure'])
    if not structure.is_absolute():
        structure = path.parent/structure
    if not structure.is_file():
        raise ValueError('Prepared input structure is missing: '+str(structure))
    sequence = data['sequence']
    if not isinstance(sequence, str) or not sequence or set(sequence)-set('ACDEFGHIKLMNPQRSTVWY'):
        raise ValueError('A complete canonical target sequence is required')
    loops = data['loops']
    if not isinstance(loops, list) or not loops:
        raise ValueError('At least one internal loop is required')
    seen = set()
    for loop in loops:
        if not isinstance(loop, dict) or set(loop)-{'start','stop','cut','extended'} or not {'start','stop','cut'} <= set(loop):
            raise ValueError('Each loop requires start, stop and cut; optional extended')
        a,b,c = (loop[k] for k in ('start','stop','cut'))
        if any(type(x) is not int for x in (a,b,c)) or not 1<a<=c<b<len(sequence) or b-a+1<3:
            raise ValueError('Loops are internal one-based pose intervals, start <= cut < stop')
        if 'extended' in loop and type(loop['extended']) is not bool:
            raise ValueError('extended must be boolean')
        members = set(range(a,b+1))
        if seen & members:
            raise ValueError('Overlapping loops are unsupported')
        seen |= members
    local = data['local_energy_residues']
    if not isinstance(local,list) or not local or any(type(x) is not int or not 1<=x<=len(sequence) for x in local) or len(set(local))!=len(local) or not seen <= set(local):
        raise ValueError('Explicit unique local-energy pose indices must include all loop residues')
    if type(data['seed']) is not int or not 1<=data['seed']<=2147483647:
        raise ValueError('seed must be integer 1..2147483647')
    if data['input_kind'] not in ('W','S','hard'):
        raise ValueError('input_kind must be W, S or hard')
    return dict(data, structure=str(structure.resolve()))
