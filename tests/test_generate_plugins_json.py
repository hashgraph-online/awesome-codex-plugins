import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "generate_plugins_json", Path(__file__).resolve().parents[1] / "scripts/generate_plugins_json.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GeneratedBundleCleanupTests(unittest.TestCase):
    def test_removes_retired_identity_and_preserves_canonical_bundle(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            legacy = root / "samuelbushi/uizze"
            canonical = root / "uizze/uizze"
            failed_fetch = root / "other/listed"
            for bundle in (legacy, canonical, failed_fetch):
                bundle.mkdir(parents=True)
                (bundle / "SKILL.md").write_text(bundle.as_posix())
            canonical_bytes = (canonical / "SKILL.md").read_bytes()
            listed = [{"owner": "uizze", "repo": "uizze"}, {"owner": "other", "repo": "listed"}]
            self.assertEqual(MODULE.prune_unlisted_bundles(root, listed), ["samuelbushi/uizze"])
            self.assertFalse(legacy.exists())
            self.assertEqual((canonical / "SKILL.md").read_bytes(), canonical_bytes)
            self.assertTrue((failed_fetch / "SKILL.md").is_file())
            self.assertEqual(MODULE.prune_unlisted_bundles(root, listed), [])

    def test_refuses_symlink_without_touching_external_files(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            outside = Path(scratch) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "keep.txt").write_text("keep")
            (root / "owner").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                MODULE.prune_unlisted_bundles(root, [{"owner": "uizze", "repo": "uizze"}])
            self.assertEqual((outside / "keep.txt").read_text(), "keep")

    def test_empty_or_failed_source_parse_never_prunes_existing_bundles(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            bundle = root / "uizze/uizze"
            bundle.mkdir(parents=True)
            (bundle / "SKILL.md").write_text("preserve")
            readme = Path(scratch) / "README.md"
            readme.write_text("# Catalog\n## Community Plugins\nNo recognized plugin entries.\n")
            parsed = MODULE.parse_plugins(readme)
            self.assertEqual(parsed, [])
            with self.assertRaisesRegex(ValueError, "empty parsed README"):
                MODULE.prune_unlisted_bundles(root, parsed)
            self.assertEqual((bundle / "SKILL.md").read_text(), "preserve")

    def test_preserves_listed_bundle_across_owner_and_repository_display_case(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            bundle = root / "UIZZE/UiZzE"
            bundle.mkdir(parents=True)
            (bundle / "SKILL.md").write_text("canonical")
            listed = [{"owner": "uizze", "repo": "uizze"}]
            self.assertEqual(MODULE.prune_unlisted_bundles(root, listed), [])
            self.assertEqual((bundle / "SKILL.md").read_text(), "canonical")

    def test_dangling_root_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            root.symlink_to(Path(scratch) / "missing", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "root must not be a symlink"):
                MODULE.prune_unlisted_bundles(root, [{"owner": "uizze", "repo": "uizze"}])
            self.assertTrue(root.is_symlink())

    def test_later_invalid_owner_or_repo_aborts_before_any_retirement(self):
        for invalid_owner in (False, True):
            with self.subTest(invalid_owner=invalid_owner), tempfile.TemporaryDirectory() as scratch:
                root = Path(scratch) / "plugins"
                retired = root / "a/retired"
                retired.mkdir(parents=True)
                (retired / "SKILL.md").write_text("preserve-until-preflight-completes")
                invalid = root / "z"
                if not invalid_owner:
                    invalid.mkdir()
                    invalid = invalid / "linked"
                invalid.symlink_to(Path(scratch) / "missing", target_is_directory=True)
                with self.assertRaises(ValueError):
                    MODULE.prune_unlisted_bundles(root, [{"owner": "uizze", "repo": "uizze"}])
                self.assertEqual((retired / "SKILL.md").read_text(), "preserve-until-preflight-completes")


if __name__ == "__main__":
    unittest.main()
