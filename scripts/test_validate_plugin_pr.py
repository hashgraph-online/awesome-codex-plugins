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

    def test_ui_query_or_fragment_cannot_duplicate_same_source_and_name(self) -> None:
        base_entry = "- [Shared](https://github.com/Example/Plugin?tab=readme) - Old."
        new_entry = "- [Shared](https://github.com/example/plugin#readme) - New."
        old_readme = "## Community Plugins\n" + base_entry
        new_readme = "## Community Plugins\n" + new_entry
        diff = "\n".join((
            "diff --git a/README.md b/README.md",
            "-" + base_entry, "+" + new_entry,
        ))
        self.assertEqual(self.parse_new_entries(diff, old_readme, new_readme), [])

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



    def test_distinct_named_plugins_can_share_one_repo(self) -> None:
        repo_url = "https://github.com/redfox-data/redfox-agent-plugins"
        umbrella = f"- [Redfox Agent Plugins]({repo_url}) - Umbrella."
        individual = [
            f"- [account-video-downloader]({repo_url}) - Account videos.",
            f"- [image-gen]({repo_url}) - Image generation.",
        ]
        diff = "\n".join(
            ["diff --git a/README.md b/README.md", "-" + umbrella]
            + ["+" + line for line in individual]
        )
        base = "## Community Plugins\n### Development & Workflow\n" + umbrella
        head = "## Community Plugins\n### Development & Workflow\n" + "\n".join(individual)
        entries = self.parse_new_entries(diff, base, head)
        self.assertEqual(
            [entry["display_name"] for entry in entries],
            ["account-video-downloader", "image-gen"],
        )
        self.assertEqual({entry["url"] for entry in entries}, {repo_url})


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

class MultiPluginManifestTests(unittest.TestCase):
    """Select the named bundle and fail closed for ambiguous or unknown names."""

    def build_archive(self) -> zipfile.ZipFile:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as output:
            for name, suffix in (("alpha", ".png"), ("beta", ".txt")):
                manifest = {
                    "name": name,
                    "version": "1.0.0",
                    "description": "Example",
                    "repository": "https://github.com/maker/demo",
                    "license": "MIT",
                    "interface": {
                        "displayName": name.title(),
                        "shortDescription": "Example",
                        "composerIcon": f"./assets/icon{suffix}",
                    },
                }
                root = f"demo-main/plugins/{name}"
                output.writestr(f"{root}/.codex-plugin/plugin.json", json.dumps(manifest))
                if name == "alpha":
                    output.writestr(f"{root}/assets/icon{suffix}", b"test")
        return zipfile.ZipFile(io.BytesIO(buffer.getvalue()))

    def test_validation_reaches_named_nested_manifest(self) -> None:
        with self.build_archive() as archive:
            with patch.object(VALIDATOR, "fetch_repo_archive", return_value=archive):
                good, _warnings = VALIDATOR.validate_remote_repo(
                    "maker", "demo", display_name="Alpha"
                )
                bad, _warnings = VALIDATOR.validate_remote_repo(
                    "maker", "demo", display_name="beta"
                )
        self.assertEqual(good, [])
        self.assertTrue(
            any("Icon file not found" in error for error in bad), bad
        )

    def test_casefolded_name_selects_same_bundle_as_generator(self) -> None:
        # The validator and mirror generator must agree on non-ASCII
        # casefolded labels rather than selecting different nested manifests.
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as output:
            output.writestr(
                "demo-main/plugins/strasse/.codex-plugin/plugin.json",
                json.dumps({"name": "STRASSE"}),
            )
            output.writestr(
                "demo-main/plugins/other/.codex-plugin/plugin.json",
                json.dumps({"name": "other"}),
            )
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            selected = VALIDATOR.find_plugin_root(
                archive, display_name="Straße", require_named_match=True,
            )
        self.assertIsNotNone(selected)
        self.assertEqual(selected.as_posix(), "demo-main/plugins/strasse")

    def test_traversal_manifest_is_not_a_remote_named_plugin(self) -> None:
        # Source ZIP metadata is untrusted. The validator must match only
        # actual repository-contained nested manifests.
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as output:
            output.writestr(
                "demo-main/../outside/.codex-plugin/plugin.json",
                json.dumps({"name": "outside"}),
            )
            output.writestr(
                "demo-main/plugins/safe/.codex-plugin/plugin.json",
                json.dumps({"name": "safe"}),
            )
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            self.assertIsNone(VALIDATOR.find_plugin_root(
                archive, display_name="outside", require_named_match=True,
            ))
            selected = VALIDATOR.find_plugin_root(
                archive, display_name="safe", require_named_match=True,
            )
        self.assertIsNotNone(selected)
        self.assertEqual(selected.as_posix(), "demo-main/plugins/safe")

    def test_nonlatin_manifest_name_matches_generator(self) -> None:
        # A Unicode source name must select one verified nested manifest,
        # not collapse to an empty ASCII-only lookup key.
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as output:
            output.writestr(
                "demo-main/plugins/video/.codex-plugin/plugin.json",
                json.dumps({"name": "视频下载"}, ensure_ascii=False),
            )
            output.writestr(
                "demo-main/plugins/other/.codex-plugin/plugin.json",
                json.dumps({"name": "other"}),
            )
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            selected = VALIDATOR.find_plugin_root(
                archive, display_name="视频下载", require_named_match=True,
            )
        self.assertIsNotNone(selected)
        self.assertEqual(selected.as_posix(), "demo-main/plugins/video")

    def test_one_source_manifest_cannot_validate_two_distinct_names(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as output:
            root = "demo-main/plugins/alpha"
            output.writestr(f"{root}/.codex-plugin/plugin.json", json.dumps({
                "name": "alpha", "version": "1.0.0",
                "description": "Example",
                "repository": "https://github.com/maker/demo",
                "license": "MIT",
                "interface": {
                    "displayName": "Alpha", "shortDescription": "Example",
                    "composerIcon": "./assets/icon.png",
                },
            }))
            output.writestr(f"{root}/assets/icon.png", b"image")
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            with patch.object(VALIDATOR, "fetch_repo_archive", return_value=archive):
                good, _ = VALIDATOR.validate_remote_repo(
                    "maker", "demo", display_name="Alpha", require_named_match=True
                )
                bad, _ = VALIDATOR.validate_remote_repo(
                    "maker", "demo", display_name="Another Plugin", require_named_match=True
                )
                legacy, _ = VALIDATOR.validate_remote_repo(
                    "maker", "demo", display_name="Legacy Branding"
                )
        self.assertEqual(good, [])
        self.assertTrue(any("uniquely matching manifest" in x for x in bad), bad)
        self.assertEqual(legacy, [])

    def test_corrupt_unrelated_nested_manifest_does_not_crash_selection(self) -> None:
        # A named valid bundle may share its repository archive with a
        # corrupt unrelated manifest. Both ZIP integrity failures are handled.
        for failure in (zipfile.BadZipFile("bad CRC"), EOFError("truncated")):
            with self.subTest(failure=type(failure).__name__):
                with self.build_archive() as archive:
                    actual_read = archive.read

                    def guarded_read(name, *args, **kwargs):
                        if str(name).endswith(
                            "/plugins/beta/.codex-plugin/plugin.json"
                        ):
                            raise failure
                        return actual_read(name, *args, **kwargs)

                    with patch.object(
                        VALIDATOR, "fetch_repo_archive", return_value=archive
                    ), patch.object(archive, "read", side_effect=guarded_read):
                        errors, warnings = VALIDATOR.validate_remote_repo(
                            "maker", "demo", display_name="Alpha"
                        )
                self.assertEqual(errors, [])
                self.assertEqual(warnings, [])

    def test_non_ascii_only_source_labels_do_not_collide(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as output:
            output.writestr(
                "demo-main/plugins/emoji/.codex-plugin/plugin.json",
                json.dumps({"name": "🚀", "interface": {"displayName": "🔒"}}),
            )
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            self.assertIsNone(VALIDATOR.find_plugin_root(
                archive, display_name="🦊", require_named_match=True,
            ))

    def test_unknown_nested_manifest_name_fails_closed(self) -> None:
        with self.build_archive() as archive:
            with patch.object(VALIDATOR, "fetch_repo_archive", return_value=archive):
                errors, _warnings = VALIDATOR.validate_remote_repo(
                    "maker", "demo", display_name="unknown"
                )
        self.assertTrue(
            any("uniquely matching manifest" in error for error in errors), errors
        )


class ExistingMirrorSourceValidationTests(unittest.TestCase):
    def test_second_named_plugin_is_not_skipped_by_existing_umbrella_mirror(self) -> None:
        import contextlib
        import io as output_io
        import tempfile

        repo_url = "https://github.com/example/multi-plugin"
        entry = {
            "display_name": "Beta",
            "url": repo_url,
            "owner": "example",
            "repo": "multi-plugin",
            "description": "Second separately named plugin.",
            "source_ref": None,
        }
        with tempfile.TemporaryDirectory() as folder:
            plugin_root = Path(folder) / "example" / "multi-plugin"
            manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text('{"name": "alpha"}', encoding="utf-8")
            for names, expected_calls in (
                ({"Alpha", "Beta"}, 1),
                ({"Beta"}, 0),
            ):
                with self.subTest(names=sorted(names)):
                    keys = {(repo_url, name) for name in names}
                    with (
                        patch.object(VALIDATOR, "git", return_value="valid-base"),
                        patch.object(VALIDATOR, "get_changed_plugin_dirs", return_value=[]),
                        patch.object(VALIDATOR, "get_new_readme_entries", return_value=[entry]),
                        patch.object(VALIDATOR, "community_plugin_keys", return_value=keys),
                        patch.object(VALIDATOR, "PLUGINS_DIR", Path(folder)),
                        patch.object(Path, "read_text", return_value="## Community Plugins"),
                        patch.object(VALIDATOR, "validate_remote_repo", return_value=([], [])) as validate,
                        patch.object(sys, "argv", ["validate-plugin-pr.py", "--base-ref", "origin/main"]),
                        contextlib.redirect_stdout(output_io.StringIO()),
                    ):
                        with self.assertRaises(SystemExit) as finished:
                            VALIDATOR.main()
                    self.assertEqual(finished.exception.code, 0)
                    self.assertEqual(validate.call_count, expected_calls)
                    if expected_calls:
                        validate.assert_called_once_with(
                            "example", "multi-plugin", None, "Beta",
                            require_named_match=True,
                        )

if __name__ == "__main__":
    unittest.main()
