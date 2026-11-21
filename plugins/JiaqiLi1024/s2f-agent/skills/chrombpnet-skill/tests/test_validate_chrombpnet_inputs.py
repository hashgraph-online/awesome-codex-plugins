#!/usr/bin/env python3
"""Tests for the ChromBPNet static input validator."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_chrombpnet_inputs.py"


class ValidateChromBPNetInputsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.genome = self.root / "genome.fa"
        self.chrom_sizes = self.root / "genome.chrom.sizes"
        self.peaks = self.root / "peaks.narrowPeak"
        self.nonpeaks = self.root / "nonpeaks.narrowPeak"
        self.fold = self.root / "fold.json"
        self.bam = self.root / "reads.bam"
        self.bias_model = self.root / "bias.h5"

        self.genome.write_text(
            ">chr1\n" + "A" * 5000 + "\n>chr2\n" + "C" * 5000 + "\n>chr3\n" + "G" * 5000 + "\n",
            encoding="utf-8",
        )
        self.chrom_sizes.write_text("chr1\t5000\nchr2\t5000\nchr3\t5000\n", encoding="utf-8")
        self.peaks.write_text("chr1\t2000\t2100\tpeak1\t0\t.\t0\t0\t0\t50\n", encoding="utf-8")
        self.nonpeaks.write_text("chr2\t2000\t2100\tnonpeak1\t0\t.\t0\t0\t0\t50\n", encoding="utf-8")
        self.fold.write_text(
            json.dumps({"train": ["chr1"], "valid": ["chr2"], "test": ["chr3"]}),
            encoding="utf-8",
        )
        self.bam.write_bytes(b"BAM fixture")
        Path(str(self.bam) + ".bai").write_bytes(b"BAI fixture")
        self.bias_model.write_bytes(b"HDF5 fixture")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_validator(self, *extra: str) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--assay",
            "ATAC",
            "--genome",
            str(self.genome),
            "--chrom-sizes",
            str(self.chrom_sizes),
            "--peaks",
            str(self.peaks),
            "--nonpeaks",
            str(self.nonpeaks),
            "--fold",
            str(self.fold),
            "--bam",
            str(self.bam),
            "--output-dir",
            str(self.root / "run"),
            *extra,
        ]
        return subprocess.run(command, check=False, capture_output=True, text=True)

    def test_chrombpnet_mode_renders_pipeline(self) -> None:
        result = self.run_validator("--mode", "chrombpnet", "--bias-model", str(self.bias_model))
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["command_argv"][:2], ["chrombpnet", "pipeline"])
        self.assertIn("--bias-model-path", report["command_argv"])

    def test_bias_mode_uses_assay_starting_threshold(self) -> None:
        result = self.run_validator("--mode", "bias")
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["command_argv"][:3], ["chrombpnet", "bias", "pipeline"])
        threshold_index = report["command_argv"].index("--bias-threshold-factor")
        self.assertEqual(report["command_argv"][threshold_index + 1], "0.5")

    def test_invalid_regions_fold_and_output_are_blocked(self) -> None:
        self.peaks.write_text("chr1\t2000\t2100\tpeak1\t0\t.\t0\t0\t0\t100\n", encoding="utf-8")
        self.fold.write_text(
            json.dumps({"train": ["chr1"], "valid": ["chr1"], "test": ["chr3"]}),
            encoding="utf-8",
        )
        (self.root / "run" / "models").mkdir(parents=True)
        result = self.run_validator("--mode", "chrombpnet", "--bias-model", str(self.bias_model))
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "error")
        self.assertNotIn("command", report)
        self.assertTrue(any("summit" in message for message in report["errors"]))
        self.assertTrue(any("overlap" in message for message in report["errors"]))
        self.assertTrue(any("already exist" in message for message in report["errors"]))


if __name__ == "__main__":
    unittest.main()
