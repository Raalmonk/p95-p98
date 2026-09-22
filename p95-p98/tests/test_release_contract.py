"""Portable boundary/state-machine checks; these do not execute native methods."""
import copy
import hashlib
import importlib.resources
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from p95p98 import controller
from p95p98.controller import (Capability, OperationResult, PreparationPending,
                              Router, State, public_features)
from p95p98.inputs import load_input


def state(token):
    return State({key: token * 64 for key in controller.DIGEST_FIELDS},
                 {'sequence': 'AAAAAA', 'input_kind': 'W'},
                 {'private_reference_handle': 'never public'})


class ReleaseContractTests(unittest.TestCase):
    def test_frozen_policy_bytes(self):
        for name, expected in {
            'p95': '6c2330e612f4c2000d9965bd45d666c3ca26a74473b994b5ba4c513a06bb5ed8',
            'p98': '533a5549d5d8722f0ea43ce418c009a589c288696d906e4dd5e386945fd0fd83',
        }.items():
            raw = importlib.resources.files('p95p98.policies').joinpath(name + '.py').read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)

    def test_original_router_module_identity(self):
        raw = Path(inspect.getfile(controller)).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '465ac1dfdceb08433fe9235a1a03665b12c1d25505624cbe2fa348d8bf01161f')

    def test_rejects_target_fields_at_both_feature_depths(self):
        for field in ('reference', 'target_coordinates', 'local_rmsd', 'fitness'):
            with self.subTest(field=field):
                with self.assertRaises(PreparationPending):
                    public_features({'sequence': 'AAAAAA', field: 1})
                with self.assertRaises(PreparationPending):
                    public_features({'per_residue': [{'index': 0, field: 1}]})

    def router(self, executor):
        cap = Capability('ngk_refine', 'native', *(['a' * 64] * 3), 2.0, 1)
        return Router(state('a'), [cap], executor, budget=10, callback_work=.1,
                      protocol_sha256='b' * 64, policy_sha256='c' * 64,
                      clone_state=copy.deepcopy)

    def test_route_rng_and_memory_follow_commit_not_old_parent(self):
        contexts = []
        def execute(cap, parent, context):
            contexts.append(copy.deepcopy(context))
            parent.payload['mutated'] = True
            result = state('b' if len(contexts) == 1 else 'c')
            return OperationResult([result], 1.0, .5,
                                   policy_memory={'committed': len(contexts)},
                                   rng_sha256=result.binding['rng_sha256'])
        router = self.router(execute)
        views = []
        def choose_raw(view):
            views.append(copy.deepcopy(view))
            return {'decision': {'action': 'ngk_refine:native', 'parent_slot': 0,
                                 'keep_slots': [x['slot'] for x in view['observation']['states']]},
                    'memory': view['memory']}
        router.step(choose_raw)
        router.step(choose_raw)
        self.assertEqual(contexts[0]['rng_sha256'], 'a' * 64)
        self.assertEqual(contexts[1]['rng_sha256'], 'b' * 64)
        self.assertEqual(contexts[1]['policy_memory'], {'committed': 1})
        self.assertEqual(router.memory, {'committed': 2})
        self.assertNotIn('mutated', router.states[0].payload)
        self.assertNotIn('private_reference_handle', json.dumps(views))
        self.assertAlmostEqual(router.work, 2.2)

    def test_unresolved_operation_blocks_redispatch(self):
        calls = []
        def execute(*args):
            calls.append(1)
            raise RuntimeError('unresolved return')
        router = self.router(execute)
        choose = lambda view: {'decision': {'action': 'ngk_refine:native',
                                            'parent_slot': 0, 'keep_slots': [0]}, 'memory': {}}
        with self.assertRaises(RuntimeError): router.step(choose)
        with self.assertRaises(PreparationPending): router.step(choose)
        self.assertEqual(len(calls), 1)

    def test_input_validation_and_relative_structure_resolution(self):
        valid = dict(structure='source.pdb', sequence='AAAAAAAAAA',
                     loops=[dict(start=3, stop=6, cut=4)],
                     local_energy_residues=[3, 4, 5, 6], seed=1, input_kind='W')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'source.pdb').write_text('END\n')
            config = root / 'input.json'
            config.write_text(json.dumps(valid))
            self.assertEqual(load_input(config)['structure'], str((root / 'source.pdb').resolve()))
            bad = []
            for key, value in [('seed', True), ('seed', 0), ('sequence', 'AAA?'),
                               ('input_kind', 'reference'), ('local_energy_residues', [3, 4]),
                               ('local_energy_residues', [3, 4, 5, 6, 6]),
                               ('loops', [dict(start=3, stop=6, cut=6)]),
                               ('loops', [dict(start=3, stop=6, cut=4)] * 2)]:
                item = copy.deepcopy(valid); item[key] = value; bad.append(item)
            bad.append(dict(valid, reference='target.pdb'))
            for item in bad:
                with self.subTest(item=item):
                    config.write_text(json.dumps(item))
                    with self.assertRaises(ValueError): load_input(config)


if __name__ == '__main__':
    unittest.main()
