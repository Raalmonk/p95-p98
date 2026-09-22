"""Concrete ProMod3 input and finalization adapter, with no automatic execution.

Uses the installed 3.7.0 entrypoint contracts. Native validation is still required
in a permitted source-isolated runtime. Never falls back to a privileged launcher.
"""
from __future__ import annotations
import copy
import hashlib
import inspect
import json
from pathlib import Path

from .errors import PreparationPending
from .mapping import map_output_lines, sequence_coverage
from contextlib import contextmanager


class ProModNative:
    def __init__(self, *, modelling, loop, sidechain, io, seq, input_root,
                 database_receipt, verified_resources, resource_paths=None,
                 checkpoint=None):
        required = {'structure_db_sha256', 'fragment_db_sha256', 'source_filter_sha256'}
        if not required <= set(database_receipt) or database_receipt.get('status') != 'VERIFIED':
            raise PreparationPending('Exact source-filtered database receipt required')
        if verified_resources != {key:database_receipt[key] for key in required}:
            raise PreparationPending('Measured resource identities differ')
        if resource_paths is None or set(resource_paths) != required:
            raise PreparationPending('Actual resource paths required; receipt equality is insufficient')
        measured = {k: file_sha256(resource_paths[k]) for k in required}
        if measured != verified_resources:
            raise PreparationPending('Actual resource file hashes differ')
        self.resource_paths = {k: Path(v).resolve() for k, v in resource_paths.items()}
        self.loaded_databases = None
        self.prepared = {}
        self.modelling, self.loop, self.sidechain = modelling, loop, sidechain
        self.io, self.seq, self.root = io, seq, Path(input_root).resolve()
        self.resources = copy.deepcopy(database_receipt)
        self.events = []
        self.checkpoint = checkpoint or (lambda stage, handle: None)

    def prepare(self, input_path, expected_json_sha256):
        """Only a pre-bound, source-derived gap construction; no reference inputs."""
        input_path = Path(input_path).resolve()
        if not input_path.is_relative_to(self.root):
            raise PreparationPending('Input is outside the isolated source namespace')
        payload = input_path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected_json_sha256:
            raise PreparationPending('Source construction binding differs')
        data = json.loads(payload)
        if (data.get('status') != 'READY' or data.get('reference_coordinates_bound', False)
                or data.get('reference_coordinates_opened', False)):
            raise PreparationPending('Input is not a source-only READY construction')
        source = input_path.parent/'source.pdb'
        if not source.resolve().is_relative_to(self.root):
            raise PreparationPending('Source symlink escaped permitted inputs')
        if hashlib.sha256(source.read_bytes()).hexdigest() != data['source_pdb_sha256']:
            raise PreparationPending('Source PDB bytes differ')
        ledger = json.loads(self.resource_paths['source_filter_sha256'].read_text())
        verify_source_exclusion(data, ledger)
        entity = self.io.LoadPDB(str(source))
        alignments = self.seq.AlignmentList()
        for segment in data['segments']:
            alignment = self.seq.CreateAlignment()
            alignment.AddSequence(self.seq.CreateSequence('target',segment['sequence']))
            template = self.seq.CreateSequence('source',segment['aligned_source'])
            template.AttachView(entity.Select('cname='+segment['chain']))
            alignment.AddSequence(template)
            alignments.append(alignment)
        raw = self.modelling.BuildRawModel(alignments,
            chain_names=[s['chain'] for s in data['segments']], include_ligands=False,
            spdbv_style=False, aln_preprocessing='default')
        self.prepared[id(raw)] = (raw, copy.deepcopy(data))
        self.events.append(dict(operation='BuildRawModel',gaps=len(raw.gaps)))
        return raw, data

    def finish_without_gap_search(self, handle, *, rotamer_library):
        """Do not call BuildSidechains: its ring-punch repair performs hidden search."""
        if len(handle.gaps) != 0:
            return dict(status='PARTIAL_MODEL',model=None,remaining_gaps=len(handle.gaps),
                        additional_gap_search=False)
        self.checkpoint('before_sidechain', handle)
        self.modelling.ReconstructSidechains(handle.model, keep_sidechains=True,
                                             rotamer_library=rotamer_library)
        self.events.append(dict(operation='ReconstructSidechains'))
        self.checkpoint('after_sidechain', handle)
        rings = self.modelling.GetRings(handle.model)
        punches = self.modelling.GetRingPunches(rings,handle.model)
        self.modelling.MinimizeModelEnergy(handle)
        self.events.append(dict(operation='MinimizeModelEnergy'))
        self.checkpoint('after_minimize', handle)
        self.modelling.CheckFinalModel(handle)
        self.events.append(dict(operation='CheckFinalModel'))
        return dict(status='MODEL_RETURNED',model=handle.model,remaining_gaps=len(handle.gaps),
                    ring_punches_before_minimize=len(punches),additional_gap_search=False)

    def load_filtered_databases(self):
        """Explicit file loaders; never use the default unfiltered database."""
        for key, path in self.resource_paths.items():
            if file_sha256(path) != self.resources[key]:
                raise PreparationPending('Resource changed since preflight')
        if self.loaded_databases is None:
            structure = self.loop.StructureDB.Load(str(self.resource_paths['structure_db_sha256']))
            fragment = self.loop.FragDB.Load(str(self.resource_paths['fragment_db_sha256']))
            self.loaded_databases = structure, fragment
        return self.loaded_databases

    @contextmanager
    def filtered_native_loaders(self, structure, fragment):
        """Dedicated worker only: bind the full pipeline's exact loader module."""
        function = self.modelling.BuildFromRawModel
        if getattr(function, '__globals__', {}).get('loop') is not self.loop:
            raise PreparationPending('Native pipeline loader module is not verified')
        old_structure, old_fragment = self.loop.LoadStructureDB, self.loop.LoadFragDB
        self.loop.LoadStructureDB = lambda: structure
        self.loop.LoadFragDB = lambda: fragment
        try:
            yield
        finally:
            self.loop.LoadStructureDB, self.loop.LoadFragDB = old_structure, old_fragment

    def branch(self, handle, *, action, frozen_parameters, fragment_db=None,
               structure_db=None, torsion_sampler=None, rotamer_library=None):
        """Original evaluated native operations; resource binding is deployment-specific."""
        if action not in ('promod3_native', 'promod3_database', 'promod3_mc'):
            raise PreparationPending('Unknown ProMod3 branch')
        bound = self.prepared.get(id(handle))
        if bound is None or bound[0] is not handle:
            raise PreparationPending('Handle requires bound source sequence and coverage')
        data = bound[1]
        structure, fragment = self.load_filtered_databases()
        if ((structure_db is not None and structure_db is not structure) or
                (fragment_db is not None and fragment_db is not fragment)):
            raise PreparationPending('Database objects were not loaded from measured filtered files')
        if action == 'promod3_native':
            if frozen_parameters:
                raise PreparationPending('Full native pipeline has no unqualified overrides')
            with self.filtered_native_loaders(structure, fragment):
                output = self.modelling.BuildFromRawModel(handle)
            self.events.append(dict(operation='BuildFromRawModel', branch='FULL_NATIVE'))
            result = dict(model=output, branch='FULL_NATIVE')
        else:
            if action == 'promod3_database':
                function = self.modelling.FillLoopsByDatabase
                resources = dict(fragment_db=fragment, structure_db=structure,
                                 torsion_sampler=torsion_sampler)
            else:
                function = self.modelling.FillLoopsByMonteCarlo
                resources = dict(torsion_sampler=torsion_sampler)
            if set(frozen_parameters) & set(resources):
                raise PreparationPending('Profile cannot replace verified resources')
            inspect.signature(function).bind(handle, **resources, **frozen_parameters)
            before = len(handle.gaps)
            function(handle, **resources, **copy.deepcopy(frozen_parameters))
            self.checkpoint('branch_returned', handle)
            self.events.append(dict(operation=function.__name__, gaps_before=before,
                                    gaps_after=len(handle.gaps)))
            result = self.finish_without_gap_search(handle, rotamer_library=rotamer_library)
            result.update(branch=action, finalization='SIDECHAIN_RECONSTRUCTION_AND_ENERGY_MINIMIZATION'
                          if result['model'] is not None else 'NOT_RUN')
        coverage = sequence_coverage(handle.model if result['model'] is None else result['model'], data)
        complete = len(handle.gaps) == 0 and coverage['complete']
        result.update(status='MODEL_RETURNED' if complete else 'PARTIAL_MODEL',
                      remaining_gaps=len(handle.gaps), coverage=coverage,
                      candidate_count=None, stem_match=None, score_gap=None, cluster_count=None,
                      rng_restore_qualified=False, events=copy.deepcopy(self.events))
        if not complete:
            result['model'] = None
        return result


def verify_source_exclusion(data, ledger):
    """An unrelated hashed database is not evidence of source exclusion."""
    sequence = ''.join(segment['sequence'] for segment in data['segments'])
    if data.get('expected_sequence', sequence) != sequence:
        raise PreparationPending('Input sequence and segment sequences differ')
    protected = {record['sequence'] for record in ledger.get('protected', {}).get('sequences', [])}
    if not sequence or sequence not in protected:
        raise PreparationPending('Resource filter does not protect this input sequence; build source-excluded resources')


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()
