# Public small input

`python examples/fetch_1l2y.py --output 1l2y_model1_A.pdb` downloads the pinned
[1L2Y PDB record](https://www.rcsb.org/structure/1L2Y) and extracts model 1, chain A.
It preserves each ATOM record's coordinates and checks the original file SHA256.
An existing identical output is reused; a different output is never overwritten.

The Trp-cage source has 20 residues. A compact internal loop can use pose residues
10–15, cut point 12, with the intact source as a refinement input. No reference
structure or target score is needed for the execution example. Supply the work
profile explicitly; the shipped reference tariff is historical rather than a
calibration of this new input.

PDB archive data are under [CC0](https://www.rcsb.org/pages/usage-policy).
Structure DOI: [10.2210/pdb1L2Y/pdb](https://doi.org/10.2210/pdb1L2Y/pdb).
