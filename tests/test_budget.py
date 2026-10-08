#!/usr/bin/env python3
"""Regression tests for isolated action spending configuration (no API calls)."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tomllib
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("budget", Path(__file__).parents[1] / "_core/prepare-budget.py")
budget = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(budget)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {"RUNNER_TEMP": str(self.root), "OCTOMIND_DATA_DIR": str(self.root / "data")}

    def validate(self, args, env, **kwargs):
        selected = Path(env["OCTOMIND_CONFIG_PATH"])
        if not list(selected.parent.glob("*.toml")):
            selected.write_text("model = 'test:model'\nmax_session_spending_threshold = 0.0\n")

    def prepare(self, value="2.00", config=""):
        with patch.object(budget.subprocess, "run", side_effect=self.validate):
            return budget.prepare(value, config, self.env)

    def test_default_is_initialized_and_overridden(self):
        selected = self.prepare()
        self.assertTrue(selected.exists())
        overlay = next(selected.parent.glob("*.budget.toml"))
        self.assertEqual(overlay.read_text(), "max_session_spending_threshold = 2.0\n")
        self.assertFalse((self.root / "data").exists())

    def test_custom_and_sibling_files_are_preserved(self):
        source = self.root / "source"
        source.mkdir()
        main = source / "custom.toml"
        main.write_text("max_session_spending_threshold = 0.1\n")
        sibling = source / "zzzz.toml"
        sibling.write_text("max_session_spending_threshold = 9.0\n")
        mcp = source / "mcp-zzzz.toml"
        mcp.write_text("max_session_spending_threshold = 12.0\n")
        self.env["OCTOMIND_CONFIG_PATH"] = str(source / "missing.toml")
        selected = self.prepare(config=str(main))
        self.assertEqual(selected.read_text(), main.read_text())
        self.assertEqual((selected.parent / sibling.name).read_text(), sibling.read_text())
        self.assertEqual((selected.parent / mcp.name).read_text(), mcp.read_text())
        ordered = sorted(selected.parent.glob("*.toml"), key=lambda p: (0 if p.name == "config.toml" else 2 if p.name.startswith("mcp-") else 1, p.name))
        self.assertTrue(ordered[-1].name.endswith(".budget.toml"))
        self.assertEqual(main.read_text(), "max_session_spending_threshold = 0.1\n")

    def test_environment_config_is_honored(self):
        source = self.root / "custom.toml"
        source.write_text("model = 'test:model'\n")
        self.env["OCTOMIND_CONFIG_PATH"] = str(source)
        self.assertEqual(self.prepare().read_text(), source.read_text())

    def test_existing_default_data_config_is_preserved(self):
        source = Path(self.env["OCTOMIND_DATA_DIR"]) / "config/config.toml"
        source.parent.mkdir(parents=True)
        source.write_text("max_session_spending_threshold = 7.0\n")
        self.assertEqual(self.prepare().read_text(), source.read_text())

    def test_invalid_values_fail_before_octomind(self):
        for value in ("", "0", "0.00", "-2", "nan", "inf", "1e3", "2;exit", " 2", "2\n", "9" * 400, "0." + "0" * 400 + "1"):
            with self.subTest(value=value), patch.object(budget.subprocess, "run") as run:
                with self.assertRaises(ValueError):
                    budget.prepare(value, "", self.env)
                run.assert_not_called()

    def test_missing_custom_file_fails_closed(self):
        with self.assertRaises(ValueError):
            self.prepare(config=str(self.root / "missing.toml"))

    @unittest.skipUnless(shutil.which("octomind"), "Octomind binary not installed")
    def test_native_validation_with_default_and_sibling_overrides(self):
        env = dict(os.environ, **self.env)
        env.pop("OCTOMIND_CONFIG_PATH", None)
        selected = budget.prepare("2.00", "", env)
        (selected.parent / "zzzz.toml").write_text("max_session_spending_threshold = 90.0\n")
        (selected.parent / "mcp-zzzz.toml").write_text("max_session_spending_threshold = 99.0\n")
        prepared = budget.prepare("1.50", str(selected), env)
        files = sorted(prepared.parent.glob("*.toml"), key=lambda p: (0 if p.name == "config.toml" else 2 if p.name.startswith("mcp-") else 1, p.name))
        threshold = None
        for path in files:
            values = tomllib.loads(path.read_text())
            threshold = values.get("max_session_spending_threshold", threshold)
        self.assertEqual(threshold, 1.5)

    def test_validation_failure_removes_temporary_copy(self):
        with patch.object(budget.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "octomind")):
            with self.assertRaises(subprocess.CalledProcessError):
                budget.prepare("2", "", self.env)
        self.assertEqual(list(self.root.glob("octomind-budget-*")), [])


if __name__ == "__main__":
    unittest.main()
