#!/usr/bin/env python3
"""Tests for diff_runs.py, built on the validator's compliant fixture."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

from test_validate_ranking import compliant_run


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DiffRunsTests(unittest.TestCase):
    def setUp(self):
        self.mod = load("diff_runs")

    def test_identical_runs_have_no_changes_and_reuse_all_peers(self):
        run = compliant_run()
        result = self.mod.diff(run, copy.deepcopy(run))
        self.assertFalse(result["manuscript_changed"])
        self.assertEqual(result["peers_shared"], 14)
        self.assertEqual(result["relation_changes"], {})
        self.assertEqual(len(result["reusable_from_old"]), 14)
        self.assertNotIn("target", result["reusable_from_old"])

    def test_separates_manuscript_and_peer_set_changes(self):
        old, new = compliant_run(), compliant_run()
        new["run"]["manuscript_sha256"] = "b" * 64
        new["papers"][14]["key"] = "ref-new"
        new["papers"][4]["relation_to_target"] = "unresolved"
        result = self.mod.diff(old, new)
        self.assertTrue(result["manuscript_changed"])
        self.assertEqual(result["peers_added"], ["ref-new"])
        self.assertEqual(result["peers_removed"], ["ref-15"])
        self.assertEqual(result["relation_changes"], {"ref-5": ["below", "unresolved"]})

    def test_rubric_change_blocks_reuse(self):
        old, new = compliant_run(), compliant_run()
        new["run"]["rubric_version"] = "4.1-r2"
        self.assertEqual(self.mod.diff(old, new)["reusable_from_old"], [])


if __name__ == "__main__":
    unittest.main()
