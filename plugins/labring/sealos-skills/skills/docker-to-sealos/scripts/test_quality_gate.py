#!/usr/bin/env python3
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import quality_gate


class QualityGateArtifactTests(unittest.TestCase):
    def test_resolve_artifact_targets_prefers_env_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.dict(os.environ, {"DOCKER_TO_SEALOS_ARTIFACTS": "template/demo/index.yaml"}, clear=False):
                self.assertEqual("template/demo/index.yaml", quality_gate._resolve_artifact_targets(root))

    def test_resolve_artifact_targets_prefers_cli_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.dict(os.environ, {"DOCKER_TO_SEALOS_ARTIFACTS": "template/env/index.yaml"}, clear=False):
                self.assertEqual(
                    "template/cli/index.yaml",
                    quality_gate._resolve_artifact_targets(root, " template/cli/index.yaml "),
                )

    def test_parse_args_accepts_artifacts(self):
        args = quality_gate.parse_args(["--artifacts", "template/demo/index.yaml"])
        self.assertEqual("template/demo/index.yaml", args.artifacts)
        self.assertFalse(args.strict)

    def test_parse_args_accepts_strict_aliases(self):
        self.assertTrue(quality_gate.parse_args(["--strict"]).strict)
        self.assertTrue(quality_gate.parse_args(["--strict-artifacts"]).strict)
        self.assertTrue(quality_gate.parse_args(["--require-topology-evidence"]).strict)

    def test_resolve_artifact_targets_returns_empty_when_template_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual("", quality_gate._resolve_artifact_targets(root))

    def test_resolve_artifact_targets_collects_index_yaml_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_a = root / "template" / "a" / "index.yaml"
            app_b = root / "template" / "b" / "index.yaml"
            app_a.parent.mkdir(parents=True, exist_ok=True)
            app_b.parent.mkdir(parents=True, exist_ok=True)
            app_a.write_text("kind: Template\n", encoding="utf-8")
            app_b.write_text("kind: Template\n", encoding="utf-8")

            with mock.patch.dict(os.environ, {}, clear=True):
                targets = quality_gate._resolve_artifact_targets(root)
            self.assertEqual(f"{app_a},{app_b}", targets)

    def test_resolve_artifact_targets_discovers_evidence_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template_file = root / "template" / "demo" / "index.yaml"
            topology_file = root / ".sealos" / "topology-evidence" / "demo.yaml"
            runtime_file = root / ".sealos" / "runtime-bundle.yaml"
            template_file.parent.mkdir(parents=True, exist_ok=True)
            topology_file.parent.mkdir(parents=True, exist_ok=True)
            template_file.write_text("kind: Template\n", encoding="utf-8")
            topology_file.write_text("kind: TopologyEvidence\n", encoding="utf-8")
            runtime_file.write_text("kind: RuntimeBundleEvidence\n", encoding="utf-8")

            with mock.patch.dict(os.environ, {}, clear=True):
                targets = quality_gate._resolve_artifact_targets(root)

            self.assertEqual(
                ",".join(str(path) for path in sorted((template_file, topology_file, runtime_file), key=str)),
                targets,
            )

    def test_resolve_artifact_targets_returns_empty_for_template_without_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "template" / "demo").mkdir(parents=True)
            (root / "template" / "demo" / "README.md").write_text("demo\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual("", quality_gate._resolve_artifact_targets(root))

    def test_validate_artifact_targets_fails_without_artifacts_by_default(self):
        ok, message = quality_gate.validate_artifact_targets("", allow_empty=False)
        self.assertFalse(ok)
        self.assertIn("no template artifacts found", message)

    def test_validate_artifact_targets_allows_empty_when_explicitly_enabled(self):
        ok, message = quality_gate.validate_artifact_targets("", allow_empty=True)
        self.assertTrue(ok)
        self.assertTrue(message.startswith("[WARN]"))

    def test_validate_artifact_targets_strict_mode_overrides_empty_allowance(self):
        ok, message = quality_gate.validate_artifact_targets("", allow_empty=True, strict=True)
        self.assertFalse(ok)
        self.assertIn("strict artifact mode", message)

    def test_validate_artifact_targets_strict_mode_requires_evidence(self):
        ok, message = quality_gate.validate_artifact_targets("template/demo/index.yaml", allow_empty=False, strict=True)
        self.assertFalse(ok)
        self.assertIn("TopologyEvidence", message)

        ok, message = quality_gate.validate_artifact_targets(
            "template/demo/index.yaml,.sealos/topology-evidence/demo.yaml",
            allow_empty=False,
            strict=True,
        )
        self.assertTrue(ok)
        self.assertEqual(message, "")

    def test_strict_artifact_environment_flag(self):
        with mock.patch.dict(os.environ, {"DOCKER_TO_SEALOS_STRICT_ARTIFACTS": "true"}, clear=True):
            self.assertTrue(quality_gate._strict_artifacts())
        with mock.patch.dict(os.environ, {"DOCKER_TO_SEALOS_REQUIRE_TOPOLOGY_EVIDENCE": "true"}, clear=True):
            self.assertTrue(quality_gate._strict_artifacts())

    def test_build_commands_includes_artifacts_argument(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            commands = quality_gate.build_commands(root, "template/demo/index.yaml")
            command_args = [list(item[1]) for item in commands]
            self.assertTrue(
                any("--artifacts" in args and "template/demo/index.yaml" in args for args in command_args)
            )

    def test_build_commands_omits_artifacts_argument_when_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            commands = quality_gate.build_commands(root, "")
            command_args = [list(item[1]) for item in commands]
            self.assertTrue(all("--artifacts" not in args for args in command_args))


if __name__ == "__main__":
    unittest.main()
