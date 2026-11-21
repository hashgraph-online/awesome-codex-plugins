import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "validate_plugin_pr", Path(__file__).resolve().parents[1] / "scripts/validate-plugin-pr.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BranchAwareValidationTests(unittest.TestCase):
    def test_readme_source_ref_link_extracts_repository_and_normalizes_identity(self):
        match = MODULE.README_ENTRY_RE.match(
            "- [WTFM](https://github.com/SupportPages-io/wtfm/tree/codex-plugin) - Published bundle."
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.group(3), "SupportPages-io")
        self.assertEqual(match.group(4), "wtfm")
        self.assertEqual(match.group(5), "codex-plugin")
        self.assertEqual(match.group(6), "Published bundle.")
        self.assertEqual(
            MODULE.normalize_github_repo_url(match.group(2)),
            "https://github.com/supportpages-io/wtfm/tree/codex-plugin",
        )

    def test_remote_validation_fetches_the_linked_branch(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"archive"

        with patch.object(MODULE, "urlopen", return_value=Response()) as urlopen, \
                patch.object(MODULE.zipfile, "ZipFile", return_value="archive"):
            self.assertEqual(
                MODULE.fetch_repo_archive("SupportPages-io", "wtfm", "codex-plugin"),
                "archive",
            )

        self.assertEqual(
            urlopen.call_args.args[0].full_url,
            "https://github.com/SupportPages-io/wtfm/archive/refs/heads/codex-plugin.zip",
        )

    def test_real_git_history_uses_common_ancestor_not_newer_main(self):
        # Reproduces a fork created before main independently listed the
        # same plugin. That name still belongs to the contributor diff.
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args], check=True,
                    capture_output=True, text=True,
                ).stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "Plugin validation test")
            git("config", "user.email", "validation-test@example.invalid")
            base = "## Community Plugins\n"
            overlap = "- [Overlap](https://github.com/sample/overlap) - Plugin.\n"
            main_only = "- [MainOnly](https://github.com/sample/main-only) - Plugin.\n"
            readme = repo / "README.md"
            readme.write_text(base, encoding="utf-8")
            git("add", "README.md")
            git("commit", "-m", "base")

            git("switch", "-c", "contributor")
            readme.write_text(base + overlap, encoding="utf-8")
            git("add", "README.md")
            git("commit", "-m", "contributor adds overlap")

            git("switch", "main")
            readme.write_text(base + overlap + main_only, encoding="utf-8")
            git("add", "README.md")
            git("commit", "-m", "main independently adds overlap and another plugin")
            git("switch", "contributor")

            with patch.object(MODULE, "REPO_ROOT", repo), patch.object(
                MODULE, "README_PATH", readme
            ):
                entries = MODULE.get_new_readme_entries("main")

        self.assertEqual([entry["repo"] for entry in entries], ["overlap"])

    def test_real_git_history_excludes_newer_main_only_bundle(self):
        # An older outside branch must validate the bundle it actually added,
        # not a different bundle committed to main after the branch diverged.
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "Plugin validation test")
            git("config", "user.email", "validation-test@example.invalid")
            (repo / "README.md").write_text("## Community Plugins\n", encoding="utf-8")
            git("add", "README.md")
            git("commit", "-m", "base")

            git("switch", "-c", "contributor")
            contributor_bundle = repo / "plugins" / "contributor" / "own-plugin"
            (contributor_bundle / ".codex-plugin").mkdir(parents=True)
            (contributor_bundle / ".codex-plugin" / "plugin.json").write_text(
                '{"name":"own-plugin"}', encoding="utf-8"
            )
            git("add", "plugins")
            git("commit", "-m", "contributor adds one bundle")

            git("switch", "main")
            newer_main_bundle = repo / "plugins" / "upstream" / "main-only"
            (newer_main_bundle / ".codex-plugin").mkdir(parents=True)
            (newer_main_bundle / ".codex-plugin" / "plugin.json").write_text(
                '{"name":"main-only"}', encoding="utf-8"
            )
            git("add", "plugins")
            git("commit", "-m", "main adds a different bundle")
            git("switch", "contributor")

            with patch.object(MODULE, "REPO_ROOT", repo), patch.object(
                MODULE, "PLUGINS_DIR", repo / "plugins"
            ):
                changed = MODULE.get_changed_plugin_dirs("main")

        self.assertEqual(
            [bundle.relative_to(repo).as_posix() for bundle in changed],
            ["plugins/contributor/own-plugin"],
        )

    def test_deleted_manifest_is_not_silently_skipped(self):
        # Deleting only plugin.json must be treated as a changed bundle
        # and reach the existing missing-manifest failure.
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "Plugin validation test")
            git("config", "user.email", "validation-test@example.invalid")
            bundle = repo / "plugins" / "contributor" / "bundle"
            manifest = bundle / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"name":"bundle"}', encoding="utf-8")
            git("add", "plugins")
            git("commit", "-m", "original bundle")
            git("switch", "-c", "remove-manifest")
            manifest.unlink()
            git("add", "-u")
            git("commit", "-m", "remove manifest")

            with patch.object(MODULE, "REPO_ROOT", repo), patch.object(
                MODULE, "PLUGINS_DIR", repo / "plugins"
            ):
                changed = MODULE.get_changed_plugin_dirs("main")
                errors, _ = MODULE.validate_local_bundle(bundle)

        self.assertEqual(changed, [bundle])
        self.assertTrue(any("Missing .codex-plugin/plugin.json" in e for e in errors))

    def test_deleted_entire_bundle_cannot_escape_validation(self):
        # An external PR must not evade validation by removing its
        # complete committed bundle instead of just the manifest.
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "Plugin validation test")
            git("config", "user.email", "validation-test@example.invalid")
            bundle = repo / "plugins" / "contributor" / "bundle"
            manifest = bundle / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"name":"bundle"}', encoding="utf-8")
            git("add", "plugins")
            git("commit", "-m", "original bundle")
            git("switch", "-c", "remove-bundle")
            git("rm", "-r", "plugins/contributor/bundle")
            git("commit", "-m", "remove bundle")

            with patch.object(MODULE, "REPO_ROOT", repo), patch.object(
                MODULE, "PLUGINS_DIR", repo / "plugins"
            ):
                changed = MODULE.get_changed_plugin_dirs("main")
                errors, _ = MODULE.validate_local_bundle(bundle)

        self.assertEqual(changed, [bundle])
        self.assertTrue(any("Plugin directory does not exist" in e for e in errors))

    def test_renamed_manifest_still_fails_closed(self):
        # Git normally reports a move as R with only the destination path.
        # --no-renames must expose the old manifest as a deletion.
        with tempfile.TemporaryDirectory() as scratch:
            repo = Path(scratch) / "repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "Plugin validation test")
            git("config", "user.email", "validation-test@example.invalid")
            bundle = repo / "plugins" / "contributor" / "bundle"
            manifest = bundle / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"name":"bundle"}', encoding="utf-8")
            git("add", "plugins")
            git("commit", "-m", "original bundle")
            git("switch", "-c", "rename-manifest")
            git("mv", "plugins/contributor/bundle/.codex-plugin/plugin.json",
                "plugins/contributor/bundle/renamed.json")
            git("commit", "-m", "rename manifest")

            with patch.object(MODULE, "REPO_ROOT", repo), patch.object(
                MODULE, "PLUGINS_DIR", repo / "plugins"
            ):
                changed = MODULE.get_changed_plugin_dirs("main")
                errors, _ = MODULE.validate_local_bundle(bundle)

        self.assertEqual(changed, [bundle])
        self.assertTrue(any("Missing .codex-plugin/plugin.json" in e for e in errors))

    def test_new_readme_entry_preserves_source_ref_for_validation(self):
        entry_line = (
            "- [WTFM](https://github.com/SupportPages-io/wtfm/tree/codex-plugin) "
            "- Published installable bundle."
        )
        with tempfile.TemporaryDirectory() as scratch:
            readme = Path(scratch) / "README.md"
            readme.write_text(f"## Community Plugins\n{entry_line}\n")
            with patch.object(MODULE, "README_PATH", readme), patch.object(
                MODULE,
                "git",
                side_effect=[f"diff --git a/README.md b/README.md\n+{entry_line}", "abc123mergebase", "## Community Plugins\n"],
            ):
                entries = MODULE.get_new_readme_entries("origin/main")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["owner"], "SupportPages-io")
        self.assertEqual(entries[0]["repo"], "wtfm")
        self.assertEqual(entries[0]["source_ref"], "codex-plugin")
        self.assertEqual(entries[0]["description"], "Published installable bundle.")


if __name__ == "__main__":
    unittest.main()
