import importlib.util
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path, PurePosixPath

SPEC = importlib.util.spec_from_file_location(
    "generate_plugins_json", Path(__file__).resolve().parents[1] / "scripts/generate_plugins_json.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GeneratedBundleCleanupTests(unittest.TestCase):
    def test_context_guard_mirror_includes_undeclared_hook_runtime(self):
        root = PurePosixPath("codex-context-guard-main")
        names = {
            "codex-context-guard-main/.codex-plugin/plugin.json",
            "codex-context-guard-main/hooks/hooks.json",
            "codex-context-guard-main/scripts/context_guard.py",
            "codex-context-guard-main/scripts/manage_plugin.py",
            "codex-context-guard-main/scripts/smoke_installed.py",
            "codex-context-guard-main/scripts/cg_instruction.py",
            "codex-context-guard-main/scripts/run_context_guard.sh",
            "codex-context-guard-main/scripts/run-context-guard.ps1",
            "codex-context-guard-main/scripts/__pycache__/context_guard.cpython-314.pyc",
            "codex-context-guard-main/scripts/build/temp.json",
            "codex-context-guard-main/hooks/.pytest_cache/state",
            "codex-context-guard-main/scripts/dist/bundle.js",
            "codex-context-guard-main/scripts/.venv/pyvenv.cfg",
            "codex-context-guard-main/hooks/.ruff_cache/index",
            "codex-context-guard-main/hooks/.codex/session.json",
            "codex-context-guard-main/scripts/.git/config",
            "codex-context-guard-main/scripts/compiled.pyc",
            "codex-context-guard-main/assets/icon.svg",
            "codex-context-guard-main/assets/state.schema.json",
            "codex-context-guard-main/assets/core-intent-v2.json",
            "codex-context-guard-main/assets/core-observation-v2.schema.json",
            "codex-context-guard-main/internal/not-for-distribution.txt",
        }
        manifest = {
            "name": "context-guard",
            "skills": "./skills/",
            "interface": {"composerIcon": "./assets/icon.svg"},
        }
        plugin = {"owner": "GreenLv", "repo": "codex-context-guard"}

        paths = MODULE.collect_selected_paths(manifest, names, root, plugin)

        self.assertTrue({
            ".codex-plugin/plugin.json",
            "hooks/hooks.json",
            "scripts/context_guard.py",
            "scripts/manage_plugin.py",
            "scripts/smoke_installed.py",
            "scripts/cg_instruction.py",
            "scripts/run_context_guard.sh",
            "scripts/run-context-guard.ps1",
            "assets/icon.svg",
            "assets/state.schema.json",
            "assets/core-intent-v2.json",
            "assets/core-observation-v2.schema.json",
        }.issubset(paths))
        self.assertNotIn("internal/not-for-distribution.txt", paths)
        self.assertTrue(all(
            name not in paths for name in (
                "scripts/__pycache__/context_guard.cpython-314.pyc",
                "scripts/build/temp.json",
                "hooks/.pytest_cache/state",
                "scripts/dist/bundle.js",
                "scripts/.venv/pyvenv.cfg",
                "hooks/.ruff_cache/index",
                "hooks/.codex/session.json",
                "scripts/.git/config",
                "scripts/compiled.pyc",
            )
        ))

    def test_manifest_dot_scripts_does_not_mirror_entire_source(self):
        # A source manifest naming "." as its scripts directory is not a
        # license to copy the entire upstream repository into the catalog.
        root = PurePosixPath("source-main")
        names = {
            "source-main/.codex-plugin/plugin.json",
            "source-main/private/secret.txt",
            "source-main/scripts/launch.py",
        }
        paths = MODULE.collect_selected_paths(
            {"name": "demo", "scripts": "."},
            names, root, {"owner": "example", "repo": "demo"},
        )
        self.assertEqual(paths, {".codex-plugin/plugin.json"})

    def test_context_guard_runtime_mirror_accepts_github_link_case_variations(self):
        # GitHub resolves owner/repository names case-insensitively. A README
        # link with alternate casing must not omit the published hook runtime.
        root = PurePosixPath("codex-context-guard-main")
        names = {
            "codex-context-guard-main/.codex-plugin/plugin.json",
            "codex-context-guard-main/hooks/hooks.json",
            "codex-context-guard-main/scripts/context_guard.py",
            "codex-context-guard-main/scripts/compiled.pyc",
            "codex-context-guard-main/assets/state.schema.json",
            "codex-context-guard-main/assets/core-intent-v2.json",
            "codex-context-guard-main/assets/core-observation-v2.schema.json",
        }
        manifest = {"name": "context-guard", "skills": "./skills/"}
        paths = MODULE.collect_selected_paths(
            manifest, names, root,
            {"owner": "greenlv", "repo": "CODEX-CONTEXT-GUARD"},
        )
        self.assertTrue({
            ".codex-plugin/plugin.json",
            "hooks/hooks.json",
            "scripts/context_guard.py",
            "assets/state.schema.json",
            "assets/core-intent-v2.json",
            "assets/core-observation-v2.schema.json",
        }.issubset(paths))
        self.assertNotIn("scripts/compiled.pyc", paths)

    def test_context_guard_runtime_mirror_does_not_apply_to_unrelated_owner(self):
        # A repository with the same basename must not inherit GreenLv's
        # source-specific runtime paths or copy unrelated scripts/hooks.
        root = PurePosixPath("codex-context-guard-main")
        names = {
            "codex-context-guard-main/.codex-plugin/plugin.json",
            "codex-context-guard-main/hooks/hooks.json",
            "codex-context-guard-main/scripts/context_guard.py",
            "codex-context-guard-main/assets/state.schema.json",
        }
        manifest = {"name": "context-guard", "skills": "./skills/"}

        paths = MODULE.collect_selected_paths(
            manifest, names, root,
            {"owner": "unrelated-owner", "repo": "codex-context-guard"},
        )

        self.assertEqual(paths, {".codex-plugin/plugin.json"})

    def test_context_guard_symlinked_owner_cannot_overwrite_external_bundle(self):
        import io
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            root.mkdir()
            outside = Path(scratch) / "outside"
            bundle = outside / "codex-context-guard"
            bundle.mkdir(parents=True)
            sentinel = bundle / "keep.txt"
            sentinel.write_text("external bundle untouched", encoding="utf-8")
            (root / "GreenLv").symlink_to(outside, target_is_directory=True)

            source_bytes = io.BytesIO()
            with zipfile.ZipFile(source_bytes, "w") as generated:
                generated.writestr(
                    "codex-context-guard-main/.codex-plugin/plugin.json",
                    '{"name":"context-guard"}',
                )
            source_bytes.seek(0)
            with zipfile.ZipFile(source_bytes) as archive, \\
                    patch.object(MODULE, "fetch_repo_archive", return_value=archive), \\
                    patch.object(MODULE, "PLUGINS_ROOT", root):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    MODULE.mirror_plugin_bundle(
                        {"owner": "GreenLv", "repo": "codex-context-guard"}
                    )

            self.assertEqual(
                sentinel.read_text(encoding="utf-8"), "external bundle untouched"
            )

    def test_mirror_destination_rejects_symlinked_plugins_root(self):
        with tempfile.TemporaryDirectory() as scratch:
            root_target = Path(scratch) / "real-root"
            root_target.mkdir()
            symlinked_root = Path(scratch) / "plugins"
            symlinked_root.symlink_to(root_target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "root must not be a symlink"):
                MODULE.require_real_mirror_parents(
                    symlinked_root, symlinked_root / "GreenLv" / "codex-context-guard"
                )

    def test_context_guard_symlinked_destination_preserves_external_bundle(self):
        import io
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            owner = root / "GreenLv"
            owner.mkdir(parents=True)
            outside = Path(scratch) / "outside"
            outside.mkdir()
            sentinel = outside / "keep.txt"
            sentinel.write_text("unchanged", encoding="utf-8")
            (owner / "codex-context-guard").symlink_to(
                outside, target_is_directory=True
            )

            source_bytes = io.BytesIO()
            with zipfile.ZipFile(source_bytes, "w") as generated:
                generated.writestr(
                    "codex-context-guard-main/.codex-plugin/plugin.json",
                    '{"name":"context-guard"}',
                )
            source_bytes.seek(0)
            with zipfile.ZipFile(source_bytes) as archive, \\
                    patch.object(MODULE, "fetch_repo_archive", return_value=archive), \\
                    patch.object(MODULE, "PLUGINS_ROOT", root):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    MODULE.mirror_plugin_bundle(
                        {"owner": "GreenLv", "repo": "codex-context-guard"}
                    )

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "unchanged")

    def test_mirror_destination_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            root.mkdir()
            candidate = root / "GreenLv" / ".." / ".." / "outside"
            with self.assertRaisesRegex(ValueError, "traversal"):
                MODULE.require_real_mirror_parents(root, candidate)

    def test_context_guard_rejects_archive_traversal_before_replacing_bundle(self):
        import io
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            bundle = root / "GreenLv" / "codex-context-guard"
            bundle.mkdir(parents=True)
            sentinel = bundle / "keep.txt"
            sentinel.write_text("preserve-existing-bundle", encoding="utf-8")

            archive_bytes = io.BytesIO()
            with zipfile.ZipFile(archive_bytes, "w") as source:
                source.writestr(
                    "codex-context-guard-main/.codex-plugin/plugin.json",
                    '{"name":"context-guard","skills":"./skills/"}',
                )
                source.writestr("codex-context-guard-main/hooks/../../escape.txt", "unsafe")

            archive_bytes.seek(0)
            with zipfile.ZipFile(archive_bytes) as source, \
                    patch.object(MODULE, "fetch_repo_archive", return_value=source), \
                    patch.object(MODULE, "PLUGINS_ROOT", root):
                with self.assertRaisesRegex(ValueError, "Unsafe mirrored archive path"):
                    MODULE.mirror_plugin_bundle(
                        {"owner": "GreenLv", "repo": "codex-context-guard"}
                    )

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve-existing-bundle")
            self.assertFalse((root / "escape.txt").exists())

    def test_colon_archive_member_cannot_replace_existing_bundle(self):
        # A colon can designate a Windows alternate data stream; untrusted
        # archive paths must fail before an existing plugin is removed.
        import io
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            bundle = root / "GreenLv" / "codex-context-guard"
            bundle.mkdir(parents=True)
            sentinel = bundle / "keep.txt"
            sentinel.write_text("previous working plugin", encoding="utf-8")

            data = io.BytesIO()
            with zipfile.ZipFile(data, "w") as writer:
                writer.writestr(
                    "codex-context-guard-main/.codex-plugin/plugin.json",
                    '{"name":"context-guard","skills":"./scripts"}',
                )
                writer.writestr(
                    "codex-context-guard-main/scripts/hook:alternate.py", "payload"
                )
            data.seek(0)
            with (
                zipfile.ZipFile(data) as archive,
                patch.object(MODULE, "fetch_repo_archive", return_value=archive),
                patch.object(MODULE, "PLUGINS_ROOT", root),
            ):
                with self.assertRaisesRegex(ValueError, "Unsafe mirrored archive path"):
                    MODULE.mirror_plugin_bundle(
                        {"owner": "GreenLv", "repo": "codex-context-guard"}
                    )
            self.assertEqual(
                sentinel.read_text(encoding="utf-8"), "previous working plugin"
            )

    def test_duplicate_selected_zip_member_preserves_existing_mirror(self):
        # Duplicate ZIP entries have order-dependent contents. Fail before
        # replacing an installed runtime instead of choosing one silently.
        import io
        import warnings
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            mirror = root / "GreenLv" / "codex-context-guard"
            mirror.mkdir(parents=True)
            sentinel = mirror / "existing-install.txt"
            sentinel.write_text("working bundle", encoding="utf-8")
            data = io.BytesIO()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(data, "w") as writer:
                    writer.writestr(
                        "codex-context-guard-main/.codex-plugin/plugin.json",
                        '{"name":"context-guard"}',
                    )
                    writer.writestr(
                        "codex-context-guard-main/hooks/hooks.json", '{"hooks":[]}'
                    )
                    writer.writestr(
                        "codex-context-guard-main/hooks/hooks.json", "other payload"
                    )
            data.seek(0)
            with (
                zipfile.ZipFile(data) as archive,
                patch.object(MODULE, "fetch_repo_archive", return_value=archive),
                patch.object(MODULE, "PLUGINS_ROOT", root),
            ):
                with self.assertRaisesRegex(ValueError, "Duplicate selected ZIP member"):
                    MODULE.mirror_plugin_bundle(
                        {"owner": "GreenLv", "repo": "codex-context-guard"}
                    )
            self.assertEqual(
                sentinel.read_text(encoding="utf-8"), "working bundle"
            )

    def test_case_insensitive_zip_paths_preserve_existing_mirror(self):
        # A case-sensitive ZIP can contain files that overwrite one another
        # when users install the generated plugin on Windows or macOS.
        import io
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            mirror = root / "GreenLv" / "codex-context-guard"
            mirror.mkdir(parents=True)
            sentinel = mirror / "existing-install.txt"
            sentinel.write_text("working bundle", encoding="utf-8")
            data = io.BytesIO()
            with zipfile.ZipFile(data, "w") as writer:
                writer.writestr(
                    "codex-context-guard-main/.codex-plugin/plugin.json",
                    '{"name":"context-guard"}',
                )
                writer.writestr("codex-context-guard-main/hooks/Hooks.json", "first")
                writer.writestr("codex-context-guard-main/hooks/hooks.json", "second")
            data.seek(0)
            with (
                zipfile.ZipFile(data) as archive,
                patch.object(MODULE, "fetch_repo_archive", return_value=archive),
                patch.object(MODULE, "PLUGINS_ROOT", root),
            ):
                with self.assertRaisesRegex(
                    ValueError, "Case-insensitive selected archive path collision"
                ):
                    MODULE.mirror_plugin_bundle(
                        {"owner": "GreenLv", "repo": "codex-context-guard"}
                    )
            self.assertEqual(
                sentinel.read_text(encoding="utf-8"), "working bundle"
            )

    def test_unicode_normalization_zip_paths_preserve_existing_mirror(self):
        # Canonically equivalent spellings can overwrite on macOS even when
        # archive member spellings have distinct byte sequences.
        import io
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            mirror = root / "GreenLv" / "codex-context-guard"
            mirror.mkdir(parents=True)
            sentinel = mirror / "existing-install.txt"
            sentinel.write_text("working bundle", encoding="utf-8")
            data = io.BytesIO()
            with zipfile.ZipFile(data, "w") as writer:
                writer.writestr(
                    "codex-context-guard-main/.codex-plugin/plugin.json",
                    '{"name":"context-guard"}',
                )
                writer.writestr("codex-context-guard-main/hooks/caf\u00e9.json", "first")
                writer.writestr("codex-context-guard-main/hooks/cafe\u0301.json", "second")
            data.seek(0)
            with (
                zipfile.ZipFile(data) as archive,
                patch.object(MODULE, "fetch_repo_archive", return_value=archive),
                patch.object(MODULE, "PLUGINS_ROOT", root),
            ):
                with self.assertRaisesRegex(
                    ValueError, "Case-insensitive selected archive path collision"
                ):
                    MODULE.mirror_plugin_bundle(
                        {"owner": "GreenLv", "repo": "codex-context-guard"}
                    )
            self.assertEqual(
                sentinel.read_text(encoding="utf-8"), "working bundle"
            )

    def test_selected_source_symlink_preserves_existing_mirror(self):
        import io
        import stat
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            mirror = root / "GreenLv" / "codex-context-guard"
            mirror.mkdir(parents=True)
            sentinel = mirror / "previous-working-bundle.txt"
            sentinel.write_text("keep existing install", encoding="utf-8")
            contents = io.BytesIO()
            with zipfile.ZipFile(contents, "w") as generated:
                generated.writestr(
                    "codex-context-guard-main/.codex-plugin/plugin.json",
                    '{"name":"context-guard","skills":"./skills/"}',
                )
                hook = zipfile.ZipInfo("codex-context-guard-main/hooks/hooks.json")
                hook.create_system = 3
                hook.external_attr = (stat.S_IFLNK | 0o777) << 16
                generated.writestr(hook, "../../outside.json")
            contents.seek(0)

            with zipfile.ZipFile(contents) as archive, \
                    patch.object(MODULE, "fetch_repo_archive", return_value=archive), \
                    patch.object(MODULE, "PLUGINS_ROOT", root):
                with self.assertRaisesRegex(ValueError, "Selected source file is a symlink"):
                    MODULE.mirror_plugin_bundle(
                        {"owner": "GreenLv", "repo": "codex-context-guard"}
                    )

            self.assertEqual(
                sentinel.read_text(encoding="utf-8"), "keep existing install"
            )

    def test_corrupt_selected_zip_member_preserves_existing_mirror(self):
        import io
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            mirror = root / "GreenLv" / "codex-context-guard"
            mirror.mkdir(parents=True)
            sentinel = mirror / "previous-working-bundle.txt"
            sentinel.write_text("keep existing install", encoding="utf-8")
            contents = io.BytesIO()
            with zipfile.ZipFile(contents, "w") as generated:
                generated.writestr(
                    "codex-context-guard-main/.codex-plugin/plugin.json",
                    '{"name":"context-guard","skills":"./skills/"}',
                )
                generated.writestr(
                    "codex-context-guard-main/hooks/hooks.json", '{"hooks":[]}'
                )
            contents.seek(0)

            with zipfile.ZipFile(contents) as archive:
                real_open = archive.open

                def corrupt_hook_member(name, *args, **kwargs):
                    if str(name).endswith("/hooks/hooks.json"):
                        raise zipfile.BadZipFile("corrupt selected hook payload")
                    return real_open(name, *args, **kwargs)

                with patch.object(MODULE, "fetch_repo_archive", return_value=archive), \
                     patch.object(MODULE, "PLUGINS_ROOT", root), \
                     patch.object(archive, "open", side_effect=corrupt_hook_member):
                    with self.assertRaisesRegex(zipfile.BadZipFile, "corrupt selected hook payload"):
                        MODULE.mirror_plugin_bundle(
                            {"owner": "GreenLv", "repo": "codex-context-guard"}
                        )

            self.assertEqual(
                sentinel.read_text(encoding="utf-8"), "keep existing install"
            )

    def test_context_guard_mirror_writes_install_runtime_from_archive(self):
        import io
        import json
        import zipfile

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            source_bytes = io.BytesIO()
            upstream_files = {
                ".codex-plugin/plugin.json": json.dumps({
                    "name": "context-guard",
                    "skills": "./skills/",
                    "interface": {"composerIcon": "./assets/icon.svg"},
                }),
                "skills/guard/SKILL.md": "# Guard",
                "hooks/hooks.json": '{"hooks":[]}',
                "scripts/context_guard.py": "print('runtime')",
                "scripts/manage_plugin.py": "print('manager')",
                "scripts/smoke_installed.py": "print('smoke')",
                # Required by the source-owned installed lifecycle smoke and
                # hook launchers; missing siblings break installed Stop paths.
                "scripts/cg_hook.py": "# hook router",
                "scripts/cg_instruction.py": "# instruction helper",
                "scripts/cg_stop3.py": "# Stop lifecycle",
                "scripts/cg_delivery.py": "# response delivery",
                "scripts/cg_authority.py": "# authority layer",
                "scripts/cg_release_adapter.py": "# release profile",
                "scripts/run_context_guard.sh": "#!/bin/sh",
                "scripts/run-context-guard.ps1": "# hook launcher",
                "assets/state.schema.json": "{}",
                "assets/core-intent-v2.json": '{"schema":"core-intent-rules/v1","patterns":{}}',
                "assets/core-observation-v2.schema.json": '{"$id":"urn:context-guard:core-observation:v2"}',
                "assets/icon.svg": "<svg/>",
                "scripts/__pycache__/cached.pyc": "not-a-bundle",
            }
            with zipfile.ZipFile(source_bytes, "w") as archive:
                for path, value in upstream_files.items():
                    archive.writestr(f"codex-context-guard-main/{path}", value)

            source_bytes.seek(0)
            with zipfile.ZipFile(source_bytes) as archive, \
                    patch.object(MODULE, "fetch_repo_archive", return_value=archive), \
                    patch.object(MODULE, "PLUGINS_ROOT", root):
                manifest, marketplace_path, relative_root = MODULE.mirror_plugin_bundle({
                    "owner": "GreenLv", "repo": "codex-context-guard"
                })

            mirrored = root / "GreenLv" / "codex-context-guard"
            self.assertEqual(manifest["name"], "context-guard")
            self.assertEqual(marketplace_path, "./plugins/GreenLv/codex-context-guard")
            self.assertEqual(relative_root, "")
            for required in (
                ".codex-plugin/plugin.json", "skills/guard/SKILL.md",
                "hooks/hooks.json", "scripts/context_guard.py",
                "scripts/manage_plugin.py", "scripts/smoke_installed.py",
                "scripts/cg_hook.py", "scripts/cg_instruction.py",
                "scripts/cg_stop3.py", "scripts/cg_delivery.py",
                "scripts/cg_authority.py", "scripts/cg_release_adapter.py",
                "scripts/run_context_guard.sh", "scripts/run-context-guard.ps1",
                "assets/state.schema.json", "assets/icon.svg",
                "assets/core-intent-v2.json",
                "assets/core-observation-v2.schema.json",
            ):
                with self.subTest(path=required):
                    self.assertTrue((mirrored / required).is_file())
            self.assertFalse((mirrored / "scripts/__pycache__/cached.pyc").exists())
            # Bundle-level startup inputs are installed and parse as JSON.
            intent = json.loads((mirrored / "assets/core-intent-v2.json").read_text())
            observation = json.loads(
                (mirrored / "assets/core-observation-v2.schema.json").read_text()
            )
            self.assertEqual(intent["schema"], "core-intent-rules/v1")
            self.assertEqual(observation["$id"], "urn:context-guard:core-observation:v2")

    def test_branch_qualified_readme_entry_uses_source_branch_metadata(self):
        with tempfile.TemporaryDirectory() as scratch:
            readme = Path(scratch) / "README.md"
            readme.write_text(
                "## Community Plugins\n"
                "- [WTFM](https://github.com/SupportPages-io/wtfm/tree/codex-plugin) "
                "- A plugin from a non-default source branch.\n",
                encoding="utf-8",
            )

            plugins = MODULE.parse_plugins(readme)

        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0]["owner"], "SupportPages-io")
        self.assertEqual(plugins[0]["repo"], "wtfm")
        self.assertEqual(plugins[0]["source_ref"], "codex-plugin")
        self.assertEqual(
            plugins[0]["install_url"],
            "https://raw.githubusercontent.com/SupportPages-io/wtfm/"
            "codex-plugin/.codex-plugin/plugin.json",
        )

    def test_branch_archive_and_manifest_urls_use_the_linked_ref(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return b"archive"

        with (
            patch.object(MODULE.urllib.request, "urlopen", return_value=Response()) as urlopen,
            patch.object(MODULE.zipfile, "ZipFile", return_value=object()),
        ):
            MODULE.fetch_repo_archive("SupportPages-io", "wtfm", "feat+plugin")

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://github.com/SupportPages-io/wtfm/archive/refs/heads/feat%2Bplugin.zip",
        )
        self.assertEqual(
            MODULE.build_raw_manifest_url(
                {"owner": "SupportPages-io", "repo": "wtfm", "source_ref": "feat+plugin"},
                "",
            ),
            "https://raw.githubusercontent.com/SupportPages-io/wtfm/feat%2Bplugin/"
            ".codex-plugin/plugin.json",
        )

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

    def test_unlisted_and_local_link_bundles_are_preserved(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            identities = ("samuelbushi/uizze", "uizze/uizze", "mturac/changelog-forge", "other/unlisted")
            for identity in identities:
                bundle = root / identity
                bundle.mkdir(parents=True)
                (bundle / "SKILL.md").write_text(identity)
            readme = Path(scratch) / "README.md"
            readme.write_text("## Community Plugins\n"
                              "- [UIZZE](https://github.com/uizze/uizze) - Canonical.\n"
                              "- [Changelog Forge](./plugins/mturac/changelog-forge) - Local.\n")
            listed = MODULE.parse_plugins(readme)
            self.assertEqual(MODULE.prune_unlisted_bundles(root, listed), ["samuelbushi/uizze"])
            for identity in identities[1:]:
                self.assertEqual((root / identity / "SKILL.md").read_text(), identity)

    def test_local_link_retains_even_an_explicit_retirement(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            legacy = root / "samuelbushi/uizze"
            legacy.mkdir(parents=True)
            readme = Path(scratch) / "README.md"
            readme.write_text("## Community Plugins\n"
                              "- [Legacy](./plugins/SamuelBushi/UIZZE) - Still listed.\n")
            self.assertEqual(MODULE.prune_unlisted_bundles(root, MODULE.parse_plugins(readme)), [])
            self.assertTrue(legacy.is_dir())

    def test_local_link_is_never_sent_to_upstream_mirroring(self):
        with tempfile.TemporaryDirectory() as scratch:
            base = Path(scratch)
            readme = base / "README.md"
            readme.write_text("## Community Plugins\n"
                              "- [Local](./plugins/local/bundle) - Retain only.\n")
            with patch.multiple(MODULE, README=readme, PLUGINS_ROOT=base / "plugins",
                                OUTPUT=base / "plugins.json", MARKETPLACE_OUTPUT=base / "marketplace.json"), \
                    patch.object(MODULE, "mirror_plugin_bundle") as mirror:
                MODULE.main()
                mirror.assert_not_called()

    def test_partial_parse_aborts_before_any_deletion(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins"
            legacy = root / "samuelbushi/uizze"
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text("keep")
            readme = Path(scratch) / "README.md"
            readme.write_text("## Community Plugins\n"
                              "- [UIZZE](https://github.com/uizze/uizze) - Canonical.\n"
                              "- [Unknown](https://example.com/plugin) - Unsupported.\n")
            with self.assertRaisesRegex(ValueError, "Unrecognized Community Plugins entry"):
                MODULE.prune_unlisted_bundles(root, MODULE.parse_plugins(readme))
            self.assertEqual((legacy / "SKILL.md").read_text(), "keep")

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
                retired = root / "samuelbushi/uizze"
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


class BranchAwareSourceTests(unittest.TestCase):
    def test_parse_plugins_uses_source_ref_from_repository_link(self):
        with tempfile.TemporaryDirectory() as scratch:
            readme = Path(scratch) / "README.md"
            readme.write_text(
                "## Community Plugins\n"
                "- [WTFM](https://github.com/SupportPages-io/wtfm/tree/codex-plugin) - Published bundle.\n"
            )

            plugin = MODULE.parse_plugins(readme)[0]

            self.assertEqual(plugin["owner"], "SupportPages-io")
            self.assertEqual(plugin["repo"], "wtfm")
            self.assertEqual(plugin["source_ref"], "codex-plugin")
            self.assertEqual(
                plugin["install_url"],
                "https://raw.githubusercontent.com/SupportPages-io/wtfm/codex-plugin/.codex-plugin/plugin.json",
            )

    def test_fetch_and_manifest_urls_keep_the_selected_branch(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"archive"

        with patch.object(MODULE.urllib.request, "urlopen", return_value=Response()) as urlopen, \
                patch.object(MODULE.zipfile, "ZipFile", return_value="archive"):
            self.assertEqual(MODULE.fetch_repo_archive("SupportPages-io", "wtfm", "codex-plugin"), "archive")

        self.assertEqual(
            urlopen.call_args.args[0].full_url,
            "https://github.com/SupportPages-io/wtfm/archive/refs/heads/codex-plugin.zip",
        )
        self.assertEqual(
            MODULE.build_raw_manifest_url(
                {"owner": "SupportPages-io", "repo": "wtfm", "source_ref": "codex-plugin"},
                "",
            ),
            "https://raw.githubusercontent.com/SupportPages-io/wtfm/codex-plugin/.codex-plugin/plugin.json",
        )


    def test_marketplace_icon_path_stays_within_bundle(self):
        """A source manifest must not point the catalog icon outside its mirror."""
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "plugins" / "maker" / "bundle"
            (root / "assets").mkdir(parents=True)
            (root / "assets" / "icon.svg").write_text("<svg/>", encoding="utf-8")
            outside = Path(scratch) / "outside.svg"
            outside.write_text("<svg/>", encoding="utf-8")

            self.assertEqual(
                MODULE.safe_mirrored_icon_path(root, "./assets/icon.svg"),
                "assets/icon.svg",
            )
            self.assertEqual(
                MODULE.safe_mirrored_icon_path(root, "/assets/icon.svg"),
                "assets/icon.svg",
            )
            for unsafe in (
                "", ".", "../outside.svg", "../../../../outside.svg",
                "//other/share/icon.svg", "/etc/passwd", "C:/Windows/system.ini",
                "assets/../icon.svg", "assets\\icon.svg",
                "./assets/icon.svg\\extra", "assets/missing.svg",
                "assets/icon.svg\x00",
            ):
                with self.subTest(icon=repr(unsafe)):
                    self.assertIsNone(MODULE.safe_mirrored_icon_path(root, unsafe))

            (root / "assets" / "linked.svg").symlink_to(outside)
            self.assertIsNone(
                MODULE.safe_mirrored_icon_path(root, "assets/linked.svg")
            )


if __name__ == "__main__":
    unittest.main()
