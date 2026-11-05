#!/usr/bin/env python3
"""Exercise complete and filtered plugin artifacts outside the checkout."""

from pathlib import Path
import shutil
import tempfile
import unittest

from check_plugin_package import check_package, package_files


SOURCE = Path(__file__).resolve().parents[1]


class CheckPluginPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "plugin"
        for path in package_files(SOURCE):
            target = self.root / path.relative_to(SOURCE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)

    def test_complete_artifact_passes(self) -> None:
        self.assertEqual([], check_package(self.root, SOURCE))

    def test_missing_source_fails(self) -> None:
        source = Path(self.tmp.name) / "missing-source"
        self.assertIn(f"invalid source checkout: {source}", check_package(self.root, source))

    def test_filtered_artifact_fails(self) -> None:
        for name in ("references", "templates", "scripts"):
            shutil.rmtree(self.root / name)
        errors = check_package(self.root)
        for name in ("references", "templates", "scripts"):
            self.assertIn(f"missing package directory: {name}", errors)

    def test_missing_shared_reference_fails(self) -> None:
        (self.root / "references/harness-patterns.md").unlink()
        self.assertTrue(any("missing resource ../../references/harness-patterns.md" in error
                            for error in check_package(self.root)))

    def test_missing_profile_template_fails(self) -> None:
        (self.root / "templates/validation-matrix.md").unlink()
        self.assertTrue(any("missing template: templates/validation-matrix.md" in error
                            for error in check_package(self.root)))

    def test_missing_advertised_script_fails(self) -> None:
        (self.root / "scripts/check_skill_language.py").unlink()
        self.assertIn("package.json advertises missing script: scripts/check_skill_language.py",
                      check_package(self.root))

    def test_missing_skill_local_reference_fails(self) -> None:
        (self.root / "skills/validation-harness-design/references/environment-bootstrap.md").unlink()
        self.assertTrue(any("missing resource references/environment-bootstrap.md" in error
                            for error in check_package(self.root)))

    def test_omitted_unadvertised_resource_fails_source_comparison(self) -> None:
        (self.root / "scripts/test_validate_plugin_metadata.py").unlink()
        self.assertIn("missing source resource: scripts/test_validate_plugin_metadata.py",
                      check_package(self.root, SOURCE))

    def test_changed_resource_fails_source_comparison(self) -> None:
        (self.root / "references/harness-patterns.md").write_text("Changed\n")
        self.assertIn("source resource differs: references/harness-patterns.md",
                      check_package(self.root, SOURCE))

    def test_escaping_symlink_fails(self) -> None:
        target = self.root / "references/harness-patterns.md"
        target.unlink()
        target.symlink_to(SOURCE / "references/harness-patterns.md")
        self.assertIn("resource escapes package: references/harness-patterns.md",
                      check_package(self.root))


if __name__ == "__main__":
    unittest.main()
