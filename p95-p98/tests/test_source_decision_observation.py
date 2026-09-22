"""Focused observation contract tests; suitable for remote unittest discovery."""
import copy
import json
import math
import unittest

from p95p98.native.source_decision_observation import observe_decision_state, normalize_source_export


def export(n=8):
    return {"residues": [{"index": i+1, "aa": "A", "name": "ALA", "chain": "A",
                          "atoms": {"N": [3*i, 0, 0], "CA": [3*i+1, 1, 0],
                                    "C": [3*i+2, 0, 1], "O": [3*i+2, 0, 2]}}
                         for i in range(n)], "projection": {"sequence": "A"*n}}


def observe(raw, current=None, loops=((2, 3),), edges=None, energy=None):
    n = len(raw["residues"])
    return observe_decision_state(raw, raw if current is None else current,
                                  sequence="A"*n, loops=loops,
                                  polymer_edges=[(i, i+1) for i in range(n-1)] if edges is None else edges,
                                  per_residue_energy=energy)


class SourceDecisionObservationTests(unittest.TestCase):
    def test_native_unindexed_export_projection_binding(self):
        raw = export()
        raw["projection"]["topology"] = [["ALA", [" N  ", " CA ", " C  ", " O  "]] for _ in raw["residues"]]
        for row in raw["residues"]:
            del row["index"]
        original = copy.deepcopy(raw)
        result = observe(raw)
        self.assertEqual(raw, original)
        self.assertEqual(result["residues"][0]["index"], 0)
        self.assertEqual(normalize_source_export(raw)["residues"][0]["index"], 1)
        raw["projection"]["topology"][0][0] = "GLY"
        with self.assertRaises(ValueError):
            observe(raw)

    def test_analytic_phi_psi_omega(self):
        raw = export(3)
        raw["residues"][0]["atoms"]["C"] = [0, 1, 0]
        raw["residues"][1]["atoms"].update(N=[0, 0, 0], CA=[1, 0, 0], C=[1, 0, 1])
        raw["residues"][2]["atoms"].update(N=[1, 1, 1], CA=[2, 1, 1])
        row = observe(raw, loops=((1, 1),))["residues"][1]
        angles = row["torsions_degrees"]
        self.assertAlmostEqual(angles["phi"]["value"], 90)
        self.assertAlmostEqual(angles["psi"]["value"], -90)
        self.assertAlmostEqual(angles["omega"]["value"], -90)

    def test_rigid_motion_preserves_angles_contacts_but_records_displacement(self):
        raw, moved = export(), export()
        for row in moved["residues"]:
            for atom, (x, y, z) in row["atoms"].items():
                row["atoms"][atom] = [-y+2, x+3, z+4]
        before, after = observe(raw), observe(raw, moved)
        for a, b in zip(before["residues"], after["residues"]):
            self.assertEqual(a["nonlocal_ca_contacts"], b["nonlocal_ca_contacts"])
            for name in ("phi", "psi", "omega"):
                av, bv = a["torsions_degrees"][name]["value"], b["torsions_degrees"][name]["value"]
                if av is None:
                    self.assertIsNone(bv)
                else:
                    self.assertAlmostEqual(av, bv)
            i = a["index"]
            self.assertAlmostEqual(b["ca_displacement_A"]["value"],
                                   math.dist(raw["residues"][i]["atoms"]["CA"], moved["residues"][i]["atoms"]["CA"]))
        self.assertGreater(after["loops"][0]["ca_displacement_mean_A"]["value"], 0)

    def test_dual_loops_connected_flanks_and_energy(self):
        result = observe(export(12), loops=((2, 3), (8, 8)), energy=list(range(12)))
        self.assertEqual([r["index"] for r in result["residues"]], list(range(11)))
        self.assertEqual(len(result["loops"]), 2)
        self.assertTrue(result["energy_supplied"])
        self.assertEqual(result["residues"][8]["weighted_per_residue_energy"], {"available": True, "value": 8.0})
        self.assertEqual(len(result["residues"][0]["contacts_outside_loops"]), 2)

    def test_break_missing_atoms_and_no_fake_energy(self):
        raw = export(7)
        del raw["residues"][2]["atoms"]["CA"]
        del raw["residues"][3]["atoms"]["N"]
        edges = [(0, 1), (2, 3), (3, 4), (5, 6)]
        result = observe(raw, loops=((2, 3),), edges=edges)
        self.assertEqual([r["index"] for r in result["residues"]], [2, 3, 4])
        row = result["residues"][0]
        self.assertEqual(row["backbone_missing_count"], 1)
        self.assertIsNone(row["ca_displacement_A"]["value"])
        self.assertIsNone(row["torsions_degrees"]["phi"]["value"])
        self.assertEqual(row["weighted_per_residue_energy"], {"available": False, "value": None})
        self.assertFalse(result["loops"][0]["connections"][0]["polymer_edge_present"])
        self.assertTrue(result["loops"][0]["connections"][1]["missing_n"])
        self.assertFalse(result["loops"][0]["outside_loop_ca_contacts"]["complete"])

    def test_contact_cutoff_connected_distance_and_other_loop(self):
        raw = export(6)
        for row in raw["residues"]:
            row["atoms"]["CA"] = [0, 0, 0]
        raw["residues"][5]["atoms"]["CA"] = [8, 0, 0]
        result = observe(raw, loops=((1, 1), (4, 4)))
        one = next(r for r in result["residues"] if r["index"] == 1)
        self.assertEqual(one["nonlocal_ca_contacts"]["count"], 2)
        self.assertEqual(one["contacts_outside_loops"][1]["count"], 1)
        broken = observe(raw, loops=((1, 1),), edges=[])
        self.assertEqual(broken["residues"][0]["nonlocal_ca_contacts"]["count"], 5)

    def test_whitelist_and_input_immutability(self):
        raw = export()
        raw.update(target_score=999, secret="never_emit")
        raw["residues"][2]["target"] = "never_emit"
        snapshot = copy.deepcopy(raw)
        result = observe(raw)
        self.assertEqual(raw, snapshot)
        self.assertNotIn("never_emit", json.dumps(result, allow_nan=False))
        self.assertNotIn("target", json.dumps(result))
        self.assertEqual(set(result), {"schema", "index_base", "sequence_length", "contact_cutoff_A", "energy_supplied", "residues", "loops"})

    def test_bad_correspondence_and_coordinates(self):
        for mutate in (
                lambda x: x["residues"][2].update(index=4),
                lambda x: x["residues"][2].update(name="GLY"),
                lambda x: x["projection"].update(sequence="G"*8),
                lambda x: x["residues"][2]["atoms"].update(CA=[float("nan"), 0, 0]),
                lambda x: x["residues"][2]["atoms"].update(CA=[0, 0]),
                lambda x: x["residues"][2]["atoms"].update(CA=[True, 0, 0])):
            raw, current = export(), export()
            mutate(current)
            with self.assertRaises(ValueError):
                observe(raw, current)

    def test_bounds_no_truncation_and_missing_energy(self):
        for loops in ((), ((2, 3), (3, 4)), ((-1, 2),), ((True, 2),), ((0, 0), (2, 2), (4, 4))):
            with self.assertRaises(ValueError):
                observe(export(), loops=loops)
        with self.assertRaises(ValueError):
            observe(export(260), loops=((2, 257),))
        with self.assertRaises(ValueError):
            observe(export(5001))
        for energy in ([0], [float("inf")]*8):
            with self.assertRaises(ValueError):
                observe(export(), energy=energy)
        result = observe(export(), energy=[None]*8)
        self.assertTrue(result["energy_supplied"])
        self.assertTrue(all(not r["weighted_per_residue_energy"]["available"] for r in result["residues"]))


if __name__ == "__main__":
    unittest.main()
