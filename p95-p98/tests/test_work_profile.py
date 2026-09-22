import copy
import json
from pathlib import Path
import tempfile
import unittest

from p95p98.work_profile import load_work_profile, native_prices, validate_work_profile


class WorkProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            'schema': 'p95p98-work-profile-v1', 'name': 'test-fixture',
            'operation_prices': {key: 1.0 for key in (
                'kic', 'repack', 'rotamer_trials', 'minimize', 'observe_state',
                'controller', 'archive_save', 'restore')},
            'tariff': dict(status='MEASURED', view=0.1, fresh_state=0.2,
                           cached_state=0.01, archive_displacement=0.03),
            'policy_setup_work': 0.5, 'delivery_reserve_cpu_seconds': 19,
            'provenance_sha256': {'receipt': 'a' * 64}}

    def test_rejects_missing_nonpositive_and_nonfinite_consumed_prices(self):
        for section in ('operation_prices', 'tariff'):
            for field, value in self.profile[section].items():
                if field == 'status':
                    continue
                for invalid in (None, 0, -1, True, float('nan'), float('inf')):
                    with self.subTest(section=section, field=field, invalid=invalid):
                        p = copy.deepcopy(self.profile)
                        p[section][field] = invalid
                        with self.assertRaises(ValueError): validate_work_profile(p)
                p = copy.deepcopy(self.profile)
                del p[section][field]
                with self.assertRaises(ValueError): validate_work_profile(p)

    def test_setup_and_explicit_selection(self):
        with self.assertRaises(ValueError): load_work_profile(None)
        for invalid in (0, None, True, float('nan')):
            p = copy.deepcopy(self.profile)
            p['policy_setup_work'] = invalid
            with self.assertRaises(ValueError): validate_work_profile(p)
            p = copy.deepcopy(self.profile)
            p['delivery_reserve_cpu_seconds'] = invalid
            with self.assertRaises(ValueError): validate_work_profile(p)

    def test_terminal_reservation_and_immutable_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'profile.json'
            path.write_text(json.dumps(self.profile))
            p = load_work_profile(path)
        self.assertEqual(len(p['profile_sha256']), 64)
        self.assertAlmostEqual(native_prices(p)['observe_state'], 0.74)
        self.assertEqual(p['operation_prices']['observe_state'], 1.0)

    def test_shipped_reference_profile(self):
        path = Path(__file__).parents[1] / 'src/p95p98/profiles/reference.json'
        p = load_work_profile(path)
        self.assertEqual(p['scope'], 'historical_reference_tariff_not_input_specific_calibration')
        self.assertTrue(all(value > 0 for value in native_prices(p).values()))


if __name__ == '__main__':
    unittest.main()
