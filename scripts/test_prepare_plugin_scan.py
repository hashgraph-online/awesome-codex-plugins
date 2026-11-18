"""The admission scan must cover the bundle the catalog actually delivers."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("prepare_plugin_scan", ROOT / "scripts/prepare-plugin-scan.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SKILL = b"---\nname: demo\ndescription: Review a command\n---\n# Demo\ncurl -X POST https://example.invalid\n"


class PrepareBundleTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.git("init", "-q", "--initial-branch=plugin-ref")
        previous = MODULE.generator.PLUGINS_ROOT
        self.addCleanup(setattr, MODULE.generator, "PLUGINS_ROOT", previous)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args], env=self.env, text=True)

    def commit(self, files):
        for path, content in files.items():
            target = self.source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content if isinstance(content, bytes) else content.encode())
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")

    def test_nested_portable_bundle_retains_actual_skill_and_canonical_identity(self):
        manifest = {"$schema": SCHEMA, "name": "demo", "version": "1.0.0", "description": "Demo",
                    "extensions": {"com.openai": {"name": "forged", "interface": {"displayName": "Demo"}}}}
        self.commit({"plugins/demo/plugin.json": json.dumps(manifest),
                     "plugins/demo/skills/demo/SKILL.md": SKILL})
        # A working-tree edit or an untracked secret must not enter a HEAD archive.
        source_skill = self.source / "plugins/demo/skills/demo/SKILL.md"
        source_skill.write_text("uncommitted edit")
        (self.source / ".env").write_text("not committed")
        before = self.git("status", "--porcelain")
        bundle = MODULE.prepare_bundle(self.source, self.root / "output", "maker", "demo", "Demo")
        self.assertEqual((bundle / "skills/demo/SKILL.md").read_bytes(), SKILL)
        self.assertEqual(json.loads((bundle / "plugin.json").read_text()), manifest)
        generated = json.loads((bundle / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(generated["name"], "demo")
        self.assertEqual(generated["skills"], "./skills/")
        self.assertEqual(generated["interface"]["displayName"], "Demo")
        self.assertFalse((bundle / ".env").exists())
        self.assertEqual(source_skill.read_text(), "uncommitted edit")
        self.assertEqual(self.git("status", "--porcelain"), before)

    def test_legacy_bundle_still_uses_original_manifest(self):
        raw = '{"name":"demo","version":"1.0.0","description":"Legacy","skills":"./skills/"}\n'
        self.commit({".codex-plugin/plugin.json": raw, "skills/demo/SKILL.md": SKILL})
        bundle = MODULE.prepare_bundle(self.source, self.root / "output", "maker", "demo", "Demo")
        self.assertEqual(json.loads((bundle / ".codex-plugin/plugin.json").read_text()), json.loads(raw))
        self.assertEqual((bundle / "skills/demo/SKILL.md").read_bytes(), SKILL)

    def test_display_name_selects_the_catalog_bundle(self):
        self.commit({f"plugins/{name}/plugin.json": json.dumps({"$schema": SCHEMA, "name": name})
                     for name in ("alpha", "beta")})
        bundle = MODULE.prepare_bundle(self.source, self.root / "output", "maker", "demo", "Beta")
        self.assertEqual(json.loads((bundle / "plugin.json").read_text())["name"], "beta")

    def test_no_manifest_fails_instead_of_scanning_an_empty_bundle(self):
        self.commit({"README.md": "not a plugin"})
        with self.assertRaises(ValueError):
            MODULE.prepare_bundle(self.source, self.root / "output", "maker", "demo", "Demo")

    def test_output_does_not_overwrite_existing_files_or_source(self):
        output = self.root / "output"
        output.mkdir()
        keeper = output / "keep.txt"
        keeper.write_text("keep")
        for destination in (output, self.source / "generated", self.root):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                MODULE.prepare_bundle(self.source, destination, "maker", "demo", "Demo")
        self.assertEqual(keeper.read_text(), "keep")
        self.assertFalse((self.source / "generated").exists())

    def test_owner_and_repo_cannot_escape_output(self):
        for owner, repo in [("..", "demo"), ("maker", "../demo"), ("a/b", "demo"), ("maker", ".")]:
            with self.subTest(owner=owner, repo=repo), self.assertRaises(ValueError):
                MODULE.prepare_bundle(self.source, self.root / "output", owner, repo, "Demo")


class ScanWorkflowTests(unittest.TestCase):
    def test_both_admission_paths_scan_source_and_delivered_bundle(self):
        for name in ("validate-contribution.yml", "sweep-open-prs.yml"):
            with self.subTest(workflow=name):
                workflow = yaml.safe_load((ROOT / ".github/workflows" / name).read_text())
                steps = workflow["jobs"]["scan"]["steps"]
                scans = [step for step in steps if step.get("uses", "").startswith("hashgraph-online/ai-plugin-scanner-action@")]
                self.assertEqual(len(scans), 2)
                self.assertEqual([step["with"]["plugin_dir"] for step in scans],
                                 ["${{ runner.temp }}/contributed", "${{ steps.bundle.outputs.path }}"])
                self.assertTrue(all(step["with"]["min_score"] == 75 for step in scans))
                self.assertTrue(all(step["with"]["fail_on_severity"] == "none" for step in scans))
                prepare = next(step for step in steps if step.get("id") == "bundle")
                self.assertEqual(prepare["env"]["CONTRIBUTION_NAME"], "${{ matrix.contribution.name }}")
                self.assertIn('"$CONTRIBUTION_NAME"', prepare["run"])
                permissions = workflow["jobs"]["scan"].get("permissions", workflow["permissions"])
                self.assertNotIn("write", permissions.values())
                if name == "sweep-open-prs.yml":
                    checkout = next(step for step in steps if step["name"] == "Check out catalog converter")
                    self.assertEqual(checkout["with"]["ref"], "${{ github.event.repository.default_branch }}")


if __name__ == "__main__":
    unittest.main()
