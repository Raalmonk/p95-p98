# ProMod3 runtime and resources

The inference worker requires ProMod3 3.7.0, upstream commit
`6817e1819152078d2d0ab9fa1fd053d8057d4454`, and OpenStructure 2.12.0.
Both versions are checked before modelling. The evaluated runtime built this
unmodified ProMod3 source against the OpenStructure image
`registry.scicore.unibas.ch/schwede/openstructure@sha256:9f2669ffde16c45939fc6e8e6dd4f907697301c081edf3d97d464c034a421d19`.
The runtime used Python 3.14 for these libraries. PyRosetta and ProMod3 can use
separate Python environments; the process boundary exchanges PDB and JSON.

Acquire ProMod3 from its [official repository](https://git.scicore.unibas.ch/schwede/ProMod3)
under its own license, following the [upstream build instructions](https://openstructure.org/promod3/3.7.0/).
The exact source checkout and build options are:

```sh
git clone https://git.scicore.unibas.ch/schwede/ProMod3.git ProMod3
git -C ProMod3 checkout 6817e1819152078d2d0ab9fa1fd053d8057d4454
cmake -S ProMod3 -B ProMod3/build -DOST_ROOT=/path/to/ost-2.12.0 \
  -DOPTIMIZE=1 -DENABLE_SSE=1 -DDISABLE_DOCUMENTATION=1 \
  -DBoost_PYTHON_VERSION=3.14 -DCMAKE_INSTALL_PREFIX=/path/to/promod3-3.7.0
cmake --build ProMod3/build --parallel 4
cmake --install ProMod3/build
```

The compiler, Boost.Python, Eigen and OpenMM development dependencies must match
the OpenStructure installation; the pinned upstream container supplies the
compatible baseline used by the original build. Install the main controller with
Python 3.12. Its package metadata deliberately rejects other Python versions.
For the separate ProMod3 Python 3.14 process, expose the same release's `src`
directory through `PYTHONPATH`; do not install the main package with that
interpreter. The worker imports only the standard-library `p95p98.promod`
subtree and the native ProMod3/OpenStructure modules. For example, a wrapper
passed as the CLI's ProMod3 Python command can export
`PYTHONPATH=/path/to/p95-p98/src:/path/to/native/site-packages` and then execute
the native Python 3.14 interpreter with `"$@"`.
Set `OST_ROOT`, the library loader path and
`PROMOD3_SHARED_DATA_PATH` to the installed runtime/data location as appropriate
for that installation. The latter directory contains `loop_data`, `scoring_data`
and `sidechain_data`. The launcher fixes native thread counts to one.

No third-party library or database is distributed in this repository. The upstream
source/install data supply the original StructureDB, fragment database, torsion
samplers, scoring tables and rotamer libraries. The measured upstream 3.7.0
StructureDB has SHA256
`0f1c6e35a3f248fddd0c2c0da2c0d1145b502d4663fe8adb7239f27adad3301a`
(520676726 bytes); the corresponding upstream FragDB has SHA256
`c8edc3828d7e3faaa0e1f2b7fc5ed2d5ebeb9482fe2b0e417e98c0d235f5b5f8`
(305574667 bytes). Check acquisitions with `sha256sum` before building resources.

## Build a source-excluded library

`python -m p95p98.promod.build_resources` extracts the existing resource builder:
the same native C++ three-state global affine BLOSUM62 alignment, gap costs
-11/-1, score/matches/negative-gap tie order, exclusion at
`matches * 5 >= min(lengths) * 2`, and whole-PDB-entry exclusion. It rebuilds the
coupled native FragDB for lengths 3–14, distance bin 1 Å, angle bin 20 degrees,
RMSD cutoff 1 Å. There are no reference coordinates in this construction.

Prepare `protected.json` from your source/target sequence(s), with lowercase PDB
entry identifiers when known:

```json
{"entries": [], "sequences": [{"label": "input", "sequence": "ACDEFGHIKLMNPQRSTVWY"}]}
```

The sequence above only illustrates the format: replace it with the actual input
sequence before constructing the library. Run the following in the ProMod3
environment, where `PM3_DATA` is the upstream shared-data directory:

```sh
c++ -O3 -shared -fPIC src/p95p98/promod/identity.cpp -o identity.so
python -m p95p98.promod.build_resources --protected protected.json \
  --identity-library ./identity.so --structure-db "$PM3_DATA/loop_data/structure_db.dat" \
  --output resources --workers 4
```

The output includes `resources.json`, `filter-ledger.json`, both databases and a
completion receipt. Keep the directory together; the manifest paths are relative.
Database construction is one-time preparation CPU, recorded separately from
inference. These files are user-supplied resources, not a structure-result cache.
The worker loads both databases explicitly and verifies their SHA256 and the
filter ledger before modelling. The ledger must explicitly protect the input's
complete target/source sequence; a manifest for another input is rejected before
model construction. Known source PDB entry identifiers should also be included
in the protected list when constructing resources.

The evaluated BENCH48 library excluded the combined development sources and
contained 13334 coordinate records. Its StructureDB SHA256 was
`eeaa2d9d8cb6e327da2b2fea44b1dea73d51cee8cd927290011679ffe1fd615f`,
FragDB `806f9bb2ecf738798945291effadb484df6110e6660c5e977f06ebeb9115ae7d`,
and ledger `ea4163715f9d6e8731c0f1fc7013036fec23948425acad80e0cf81f21d545474`.
A library built for new inputs has its own identities; identical policy files
do not imply identical candidate resources or reproduce the evaluation numbers.

## Native branch semantics and input conversion

Each ProMod3 action restarts from the original source-derived gap construction.
`prepare_source(source_pdb, sequence, loops, output_dir)` accepts a complete,
canonical source whose residue sequence equals the target sequence; `loops`
contains one-based inclusive pose-index `start`/`stop` dictionaries. It removes
requested loop coordinates, constructs the native target/template alignment and
keeps source segment boundaries. Missing residues, target/source mismatches,
terminal loops, alternate conformers, insertion codes and indexed nonstandard
chemistry are rejected. Target insertions therefore need a complete prepared
source before this release's inference entry point.

`FillLoopsByDatabase` or `FillLoopsByMonteCarlo` uses the original native defaults.
A branch with remaining gaps returns `PARTIAL_MODEL`, without an eligible final
structure. Complete models pass through `ReconstructSidechains` with existing
sidechains kept, native `MinimizeModelEnergy`, then `CheckFinalModel`. This does
not call `BuildSidechains`, whose ring-punch repair can launch additional search.
Output chain labels are restored and residue numbers use one-based pose indices.
The process launcher records CPU/wall usage, applies the evaluated 1800 CPU-second
and 5400 wall-second maximum per action, further bounded by the caller's remaining
budget, and never automatically reruns an interrupted attempt. `SIGXCPU` is
reported as `CPU_LIMIT`; an unexplained `SIGKILL` is `KILLED_UNKNOWN_CAUSE`,
regardless of whether observed CPU usage is near the limit.
