"""Fetch the pinned public PDB; extract model 1 chain A without changing coordinates."""
import argparse
import hashlib
from pathlib import Path
import urllib.request

URL = 'https://files.rcsb.org/download/1L2Y.pdb'
SHA256 = '5d1bbb545a312dfff1ae1e64b6d8addecb2f561ddc4011aeb5bee9d1dfcd4438'


def extract(data):
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Downloaded 1L2Y identity differs from the pinned example')
    atoms = []
    in_first = False
    for line in data.decode('ascii').splitlines():
        if line.startswith('MODEL '):
            in_first = int(line[10:14]) == 1
        elif line.startswith('ENDMDL') and in_first:
            break
        elif in_first and line.startswith('ATOM  ') and line[21:22] == 'A':
            atoms.append(line)
    residues = {line[22:27] for line in atoms}
    if len(residues) != 20:
        raise ValueError('Expected 20 residues in first model chain A')
    return ('\n'.join(atoms + ['TER', 'END']) + '\n').encode('ascii')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('1l2y_model1_A.pdb'))
    args = parser.parse_args()
    with urllib.request.urlopen(URL, timeout=30) as response:
        result = extract(response.read())
    if args.output.exists():
        if args.output.read_bytes() != result:
            raise FileExistsError(f'Different existing file: {args.output}')
    else:
        with args.output.open('xb') as stream:
            stream.write(result)
    print(f'{args.output}: sha256={hashlib.sha256(result).hexdigest()}')


if __name__ == '__main__':
    main()
