# Small public example input

We use the Trp-cage protein (PDB 1L2Y), a 20-residue structure, as the example input.

## Get the input

Run:

```sh
python examples/fetch_1l2y.py --output 1l2y_model1_A.pdb
```

This downloads the pinned [1L2Y PDB record](https://www.rcsb.org/structure/1L2Y) and extracts model 1, chain A. The script:

- checks the SHA256 of the original file
- keeps every ATOM record's coordinates unchanged
- reuses an existing output if it is identical, and never overwrites one that differs

## Suggested settings

- Loop: pose residues 10–15 (a short internal loop).
- Cut point: 12.
- Use the intact structure as the refinement input.
- Supply the work profile explicitly. The shipped reference tariff is historical; it was not calibrated for this input.

You do not need a reference structure or target score to run the example.

## License

PDB archive data are under [CC0](https://www.rcsb.org/pages/usage-policy). Structure DOI: [10.2210/pdb1L2Y/pdb](https://doi.org/10.2210/pdb1L2Y/pdb).
