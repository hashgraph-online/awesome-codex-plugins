from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import zipfile
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("validate-plugin-pr.py")
SPEC = importlib.util.spec_from_file_location("validate_plugin_pr", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


class ReadmeEntryRegexTests(unittest.TestCase):
    def parse_new_entries(self, diff: str, base_readme: str, current_readme: str):
        with (
            patch.object(VALIDATOR, "git", side_effect=(diff, "abc123mergebase", base_readme or "## Community Plugins\n")),
            patch.object(Path, "read_text", return_value=current_readme),
        ):
            return VALIDATOR.get_new_readme_entries("origin/main")

    def test_repository_urls_preserve_owner_repo_and_description_groups(self) -> None:
        for suffix in (
            "",
            "/",
            "/tree/main",
            "/tree/feat+plugin",
            "/tree/release%2Fv1",
            "?tab=readme-ov-file#setup",
        ):
            with self.subTest(suffix=suffix):
                url = "https://github.com/example/plugin" + suffix
                entry = f"- [Example]({url}) - A useful plugin."

                match = VALIDATOR.README_ENTRY_RE.fullmatch(entry)

                self.assertIsNotNone(match)
                assert match is not None
                self.assertEqual(
                    match.groups(),
                    (
                        "Example",
                        url,
                        "example",
                        "plugin",
                        "main" if suffix == "/tree/main" else (
                            "feat+plugin" if suffix == "/tree/feat+plugin" else (
                                "release%2Fv1" if suffix == "/tree/release%2Fv1" else None
                            )
                        ),
                        "A useful plugin.",
                    ),
                )

    def test_trailing_slash_before_query_is_not_a_new_repository(self) -> None:
        diff = "\n".join(
            (
                "diff --git a/README.md b/README.md",
                "- [Example](https://github.com/example/plugin?tab=readme) - Existing entry.",
                "+- [Example](https://github.com/example/plugin/?tab=readme) - Existing entry.",
            )
        )
        base_readme = (
            "## Community Plugins\n"
            "- [Example](https://github.com/example/plugin?tab=readme) - Existing entry."
        )
        current_readme = (
            "## Community Plugins\n"
            "- [Example](https://github.com/example/plugin/?tab=readme) - Existing entry."
        )

        entries = self.parse_new_entries(diff, base_readme, current_readme)

        self.assertEqual(entries, [])

    def test_seen_urls_are_normalized_before_deduplication(self) -> None:
        diff = "\n".join(
            (
                "diff --git a/README.md b/README.md",
                "+- [Example](https://github.com/example/plugin?tab=readme) - First entry.",
                "+- [Example](https://github.com/example/plugin/?tab=readme) - Duplicate entry.",
            )
        )

        current_readme = (
            "## Community Plugins\n"
            "### Development & Workflow\n"
            "- [Example](https://github.com/example/plugin?tab=readme) - First entry.\n"
            "- [Example](https://github.com/example/plugin/?tab=readme) - Duplicate entry."
        )
        entries = self.parse_new_entries(diff, "", current_readme)

        self.assertEqual(len(entries), 1)

    def test_tree_ref_and_subpath_case_are_preserved(self) -> None:
        base_readme = (
            "## Community Plugins\n"
            "- [Example](https://github.com/example/plugin/tree/Main/Plugins/Foo) "
            "- Existing entry."
        )
        diff = "\n".join(
            (
                "diff --git a/README.md b/README.md",
                "- " + base_readme,
                "+- [Example](https://github.com/example/plugin/tree/main/plugins/foo) "
                "- Updated entry.",
            )
        )

        current_readme = (
            "## Community Plugins\n"
            "- [Example](https://github.com/example/plugin/tree/main/plugins/foo) "
            "- Updated entry."
        )
        entries = self.parse_new_entries(diff, base_readme, current_readme)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source_ref"], "main/plugins/foo")

    def test_branch_case_changes_are_not_normalized_away(self) -> None:
        base_readme = (
            "## Community Plugins\n"
            "- [Example](https://github.com/example/plugin/tree/Main) - Existing.\n"
        )
        current_readme = base_readme.replace("/tree/Main", "/tree/main")
        diff = "\n".join(
            (
                "diff --git a/README.md b/README.md",
                "- " + base_readme.splitlines()[-1],
                "+" + current_readme.splitlines()[-1],
            )
        )

        entries = self.parse_new_entries(diff, base_readme, current_readme)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source_ref"], "main")

    def test_branch_ref_is_passed_to_remote_manifest_validation(self) -> None:
        with (
            patch.object(VALIDATOR, "fetch_repo_archive") as fetch,
            patch.object(VALIDATOR, "find_plugin_root", return_value=None),
        ):
            fetch.return_value = object()
            errors, _warnings = VALIDATOR.validate_remote_repo(
                "example", "plugin", "feat+plugin"
            )

        fetch.assert_called_once_with("example", "plugin", "feat+plugin")
        self.assertTrue(any("does not contain" in error for error in errors))

    def test_same_repository_added_on_both_branches_is_validated(self) -> None:
        # A moving main tip may contain the URL even though the contributor
        # independently introduced it relative to their actual fork point.
        entry = "- [Shared](https://github.com/example/shared) - A new plugin."
        diff = "diff --git a/README.md b/README.md\n+" + entry
        ancestor_readme = "## Community Plugins\n"
        current_readme = "## Community Plugins\n" + entry + "\n"
        with (
            patch.object(
                VALIDATOR, "git",
                side_effect=(diff, "123abcmergebase", ancestor_readme),
            ) as git_mock,
            patch.object(Path, "read_text", return_value=current_readme),
        ):
            entries = VALIDATOR.get_new_readme_entries("origin/main")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["repo"], "shared")
        self.assertEqual(git_mock.call_args_list[1].args,
                         ("merge-base", "origin/main", "HEAD"))
        self.assertEqual(git_mock.call_args_list[2].args,
                         ("show", "123abcmergebase:README.md"))

    def test_missing_merge_base_fails_closed(self) -> None:
        entry = "- [Shared](https://github.com/example/shared) - Plugin."
        with (
            patch.object(VALIDATOR, "git", side_effect=("+" + entry, "")),
            patch.object(Path, "read_text", return_value=entry),
        ):
            with self.assertRaisesRegex(RuntimeError, "merge base"):
                VALIDATOR.get_new_readme_entries("origin/main")

    def test_related_project_links_are_not_plugin_submissions(self) -> None:
        diff = "\n".join(
            (
                "diff --git a/README.md b/README.md",
                "+- [Koto](https://github.com/mehrdadxzaker/Koto) - Related project.",
            )
        )
        current_readme = (
            "## Community Plugins\n"
            "### Development & Workflow\n"
            "- [Existing](https://github.com/example/plugin) - Plugin.\n"
            "## Related Projects\n"
            "- [Koto](https://github.com/mehrdadxzaker/Koto) - Related project."
        )

        entries = self.parse_new_entries(diff, "", current_readme)

        self.assertEqual(entries, [])



class MalformedManifestTests(unittest.TestCase):
    """Malformed contributor manifests should produce errors, not tracebacks."""

    @staticmethod
    def valid_fields(interface: object) -> dict:
        return {
            "name": "demo",
            "version": "1.0.0",
            "description": "demo",
            "repository": "https://github.com/maker/demo",
            "license": "MIT",
            "interface": interface,
        }

    def remote_errors(self, manifest: object) -> list[str]:
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as out:
            out.writestr("demo-main/.codex-plugin/plugin.json", json.dumps(manifest))
        with zipfile.ZipFile(io.BytesIO(raw.getvalue())) as archive:
            with patch.object(VALIDATOR, "fetch_repo_archive", return_value=archive):
                errors, warnings = VALIDATOR.validate_remote_repo("maker", "demo")
        self.assertEqual(warnings, [])
        return errors

    def test_non_object_remote_root_is_validation_error(self) -> None:
        errors = self.remote_errors([])
        self.assertIn("plugin.json must contain a JSON object", errors)

    def test_null_remote_root_is_validation_error(self) -> None:
        errors = self.remote_errors(None)
        self.assertIn("plugin.json must contain a JSON object", errors)
        self.assertNotIn("Could not read valid plugin.json from source repo", errors)

    def test_invalid_json_remote_root_is_unreadable(self) -> None:
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as out:
            out.writestr("demo-main/.codex-plugin/plugin.json", "{invalid")
        with zipfile.ZipFile(io.BytesIO(raw.getvalue())) as archive:
            with patch.object(VALIDATOR, "fetch_repo_archive", return_value=archive):
                errors, warnings = VALIDATOR.validate_remote_repo("maker", "demo")
        self.assertIn("Could not read valid plugin.json from source repo", errors)
        self.assertEqual(warnings, [])

    def test_corrupt_remote_manifest_member_is_unreadable(self) -> None:
        for failure in (
            zipfile.BadZipFile("manifest CRC mismatch"),
            EOFError("truncated manifest member"),
        ):
            with self.subTest(failure=type(failure).__name__):
                raw = io.BytesIO()
                with zipfile.ZipFile(raw, "w") as output:
                    output.writestr(
                        "demo-main/.codex-plugin/plugin.json",
                        json.dumps(self.valid_fields({
                            "displayName": "Demo",
                            "shortDescription": "Demo",
                            "composerIcon": "",
                        })),
                    )
                with zipfile.ZipFile(io.BytesIO(raw.getvalue())) as archive:
                    with patch.object(VALIDATOR, "fetch_repo_archive", return_value=archive):
                        with patch.object(archive, "read", side_effect=failure):
                            errors, warnings = VALIDATOR.validate_remote_repo("maker", "demo")
                self.assertIn("Could not read valid plugin.json from source repo", errors)
                self.assertEqual(warnings, [])

    def test_non_utf8_remote_root_is_unreadable(self) -> None:
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as out:
            out.writestr("demo-main/.codex-plugin/plugin.json", b"\xff\xfe")
        with zipfile.ZipFile(io.BytesIO(raw.getvalue())) as archive:
            with patch.object(VALIDATOR, "fetch_repo_archive", return_value=archive):
                errors, warnings = VALIDATOR.validate_remote_repo("maker", "demo")
        self.assertIn("Could not read valid plugin.json from source repo", errors)
        self.assertEqual(warnings, [])

    def test_non_utf8_local_root_is_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "plugins" / "maker" / "demo"
            (bundle / ".codex-plugin").mkdir(parents=True)
            (bundle / ".codex-plugin" / "plugin.json").write_bytes(b"\xff\xfe")
            with patch.object(VALIDATOR, "REPO_ROOT", root):
                errors, warnings = VALIDATOR.validate_local_bundle(bundle)
        self.assertTrue(any("plugin.json is not valid JSON" in error for error in errors))
        self.assertEqual(warnings, [])

    def test_directory_shaped_local_manifest_is_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "plugins" / "maker" / "demo"
            (bundle / ".codex-plugin" / "plugin.json").mkdir(parents=True)
            with patch.object(VALIDATOR, "REPO_ROOT", root):
                errors, warnings = VALIDATOR.validate_local_bundle(bundle)
        self.assertTrue(any("plugin.json must be a regular file" in e for e in errors))
        self.assertEqual(warnings, [])

    def test_escaping_local_manifest_symlink_is_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "plugins" / "maker" / "demo"
            (bundle / ".codex-plugin").mkdir(parents=True)
            outside = root / "outside.json"
            outside.write_text(
                json.dumps(self.valid_fields({
                    "displayName": "Demo",
                    "shortDescription": "Demo",
                    "composerIcon": "",
                })),
                encoding="utf-8",
            )
            try:
                (bundle / ".codex-plugin" / "plugin.json").symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")
            with patch.object(VALIDATOR, "REPO_ROOT", root):
                errors, warnings = VALIDATOR.validate_local_bundle(bundle)
        self.assertTrue(any("plugin.json must be a regular file" in e for e in errors))
        self.assertEqual(warnings, [])

    def test_non_string_required_fields_rejected_in_remote_submission(self) -> None:
        valid_interface = {
            "displayName": "Demo",
            "shortDescription": "Demo",
            "composerIcon": "./assets/icon.svg",
        }
        for field, value in (
            ("name", []),
            ("version", 123),
            ("description", {}),
            ("repository", False),
            ("license", ["MIT"]),
        ):
            with self.subTest(field=field):
                manifest = self.valid_fields(valid_interface)
                manifest[field] = value
                errors = self.remote_errors(manifest)
                self.assertIn(f"Required field '{field}' must be a string", errors)

    def test_non_string_interface_fields_rejected_in_remote_submission(self) -> None:
        for field, value in (
            ("displayName", []),
            ("shortDescription", 7),
            ("composerIcon", {}),
        ):
            with self.subTest(field=field):
                interface = {
                    "displayName": "Demo",
                    "shortDescription": "Demo",
                    "composerIcon": "./assets/icon.svg",
                }
                interface[field] = value
                errors = self.remote_errors(self.valid_fields(interface))
                self.assertIn(f"interface.{field} must be a string", errors)

    def test_non_string_local_manifest_fields_are_validation_errors(self) -> None:
        manifest = self.valid_fields({
            "displayName": "Demo",
            "shortDescription": "Demo",
            "composerIcon": "./assets/icon.svg",
        })
        manifest["name"] = []
        manifest["interface"]["displayName"] = []
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "plugins" / "maker" / "demo"
            (bundle / ".codex-plugin").mkdir(parents=True)
            (bundle / ".codex-plugin" / "plugin.json").write_text(json.dumps(manifest))
            with patch.object(VALIDATOR, "REPO_ROOT", root):
                errors, _warnings = VALIDATOR.validate_local_bundle(bundle)
        self.assertIn("Required field 'name' must be a string", errors)
        self.assertIn("interface.displayName must be a string", errors)

    def test_null_remote_interface_is_validation_error(self) -> None:
        errors = self.remote_errors(self.valid_fields(None))
        self.assertIn("Missing or invalid 'interface' object in plugin.json", errors)

    def test_non_object_local_root_is_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "plugins" / "maker" / "demo"
            (bundle / ".codex-plugin").mkdir(parents=True)
            (bundle / ".codex-plugin" / "plugin.json").write_text("[]")
            with patch.object(VALIDATOR, "REPO_ROOT", root):
                errors, warnings = VALIDATOR.validate_local_bundle(bundle)
        self.assertIn("plugin.json must contain a JSON object", errors)
        self.assertEqual(warnings, [])

    def test_null_local_interface_is_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "plugins" / "maker" / "demo"
            (bundle / ".codex-plugin").mkdir(parents=True)
            (bundle / ".codex-plugin" / "plugin.json").write_text(
                json.dumps(self.valid_fields(None))
            )
            with patch.object(VALIDATOR, "REPO_ROOT", root):
                errors, warnings = VALIDATOR.validate_local_bundle(bundle)
        self.assertIn("Missing or invalid 'interface' object in plugin.json", errors)
        self.assertEqual(warnings, [])

if __name__ == "__main__":
    unittest.main()
