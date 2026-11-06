import importlib.util
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "generate_plugins_json", Path(__file__).resolve().parents[1] / "scripts/generate_plugins_json.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GeneratedBundleCleanupTests(unittest.TestCase):
    def test_brewpage_root_relative_mcp_config_is_materialized(self):
        for reference in ("/.mcp.json", "/./.mcp.json"):
            with self.subTest(reference=reference), tempfile.TemporaryDirectory() as scratch:
                raw = io.BytesIO()
                with MODULE.zipfile.ZipFile(raw, "w") as archive:
                    archive.writestr("archive/.codex-plugin/plugin.json", json.dumps({
                        "name": "brewpage", "version": "1.0.0", "mcpServers": reference
                    }))
                with MODULE.zipfile.ZipFile(io.BytesIO(raw.getvalue())) as archive, patch.object(
                    MODULE, "fetch_repo_archive", return_value=archive
                ), patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)):
                    MODULE.mirror_plugin_bundle({"owner": "kochetkov-ma", "repo": "brewpage-codex-plugin"})
                self.assertTrue((Path(scratch) / "kochetkov-ma/brewpage-codex-plugin/.mcp.json").is_file())

    def test_brewpage_missing_mcp_config_uses_documented_server_without_overwriting_source(self):
        manifest = {"name": "brewpage", "version": "1.0.0", "mcpServers": "./.mcp.json"}
        for source_config in (None, {"mcpServers": {"custom": {"url": "https://example.com/mcp"}}}):
            with self.subTest(source_config=source_config), tempfile.TemporaryDirectory() as scratch:
                buffer = io.BytesIO()
                with MODULE.zipfile.ZipFile(buffer, "w") as archive:
                    archive.writestr("archive/.codex-plugin/plugin.json", json.dumps(manifest))
                    if source_config is not None:
                        archive.writestr("archive/.mcp.json", json.dumps(source_config))
                with MODULE.zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive, patch.object(
                    MODULE, "fetch_repo_archive", return_value=archive
                ), patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)):
                    MODULE.mirror_plugin_bundle({"owner": "kochetkov-ma", "repo": "brewpage-codex-plugin"})
                config_path = Path(scratch) / "kochetkov-ma/brewpage-codex-plugin/.mcp.json"
                self.assertTrue(config_path.is_file())
                config = json.loads(config_path.read_text())
                self.assertEqual(config, source_config or {
                    "mcpServers": {"brewpage": {"type": "http", "url": "https://brewpage.app/mcp"}}
                })

    def test_agent_harness_mirror_preserves_shared_resources_and_validation(self):
        manifest = {
            "name": "agent-harness-skills", "version": "0.2.0",
            "skills": "./skills/",
            "interface": {"composerIcon": "./assets/icon.svg"},
        }
        resources = {
            "skills/validation-harness-design/SKILL.md":
                b"Read `../../references/harness-patterns.md`.\n",
            "references/harness-patterns.md": b"# Shared patterns\n",
            "references/harness-profiles.json": b'{"templateDirectory": "templates"}\n',
            "templates/validation-matrix.md": b"# Validation matrix\n",
            "scripts/check_skill_closure.py": b"print('passed')\n",
            "scripts/test_check_skill_closure.py": b"# Validator tests\n",
            ".opencode/plugins/agent-harness-skills.js": b"export default async () => ({});\n",
            ".claude-plugin/plugin.json": b'{"name": "agent-harness-skills"}\n',
            ".cursor-plugin/plugin.json": b'{"name": "agent-harness-skills"}\n',
            "gemini-extension.json": b'{"contextFileName": "GEMINI.md"}\n',
            "AGENTS.md": b"# Repository instructions\n",
            "INDEX.md": b"# Skill routing\n",
            "GEMINI.md": b"Read INDEX.md.\n",
            "README.zh-CN.md": b"# Translated README\n",
            "CONTRIBUTING.md": b"# Contributing\n",
            "CODE_OF_CONDUCT.md": b"# Code of conduct\n",
            "docs/scenario-tests.md": b"# Scenario evidence\n",
            "assets/icon.svg": b"<svg/>\n",
            "package.json": b'{"scripts": {"validate": "python3 scripts/check_skill_closure.py"}}\n',
        }
        with tempfile.TemporaryDirectory() as scratch:
            buffer = io.BytesIO()
            with MODULE.zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("archive/.codex-plugin/plugin.json", json.dumps(manifest))
                for path, content in resources.items():
                    archive.writestr("archive/" + path, content)
                archive.writestr("archive/unrelated/data.txt", b"not part of the plugin")
            with MODULE.zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive, patch.object(
                MODULE, "fetch_repo_archive", return_value=archive
            ), patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)):
                MODULE.mirror_plugin_bundle({"owner": "yfge", "repo": "agent-harness-skills"})
            output = Path(scratch) / "yfge/agent-harness-skills"
            for path, content in resources.items():
                self.assertTrue((output / path).is_file(), path)
                self.assertEqual((output / path).read_bytes(), content)
            self.assertFalse((output / "unrelated/data.txt").exists())

    def test_complete_metis_bundle_is_mirrored_verbatim(self):
        files = {
            ".codex-plugin/plugin.json": b'{"name":"metis-check","version":"1.0.3","skills":"./skills/","mcpServers":"./.mcp.json"}\n',
            ".claude-plugin/plugin.json": b'{"name":"metis-check"}\n',
            ".mcp.json": b'{"mcpServers":{}}\n',
            "mcp.json": b'{"servers":{}}\n',
            "plugin.json": b'{"name":"metis-check"}\n',
            "LICENSE": b"complete unmodified bundle mirroring permitted\n",
            "README.md": b"installation instructions\n",
            "assets/README.txt": b"asset attribution\n",
            "assets/icon-codex.png": b"codex icon",
            "assets/icon.png": b"other client icon",
            "assets/logo.png": b"logo",
            "skills/metis-check/SKILL.md": b"check citations\n",
            "skills/setup/SKILL.md": b"configure the service\n",
            "future/new.json": b'{"keep":"new bundle files too"}\n',
        }
        with tempfile.TemporaryDirectory() as scratch:
            buffer = io.BytesIO()
            with MODULE.zipfile.ZipFile(buffer, "w") as archive:
                for path, content in files.items():
                    archive.writestr("archive/plugins/metis-check/" + path, content)
                archive.writestr("archive/dist/music.mp3", b"not licensed for mirroring")
            with MODULE.zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive, patch.object(
                MODULE, "fetch_repo_archive", return_value=archive
            ), patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)):
                MODULE.mirror_plugin_bundle({"owner": "MetisFoundry", "repo": "metis-plugins"})
            output = Path(scratch) / "MetisFoundry/metis-plugins"
            actual = {p.relative_to(output).as_posix(): p.read_bytes()
                      for p in output.rglob("*") if p.is_file()}
            self.assertEqual(actual, files)

    def test_deja_hook_mirror_keeps_executable_wrapper_and_dark_logo(self):
        manifest = {
            "name": "deja-vu", "version": "1.0.0",
            "hooks": "./hooks/hooks.json",
            "interface": {"logoDark": "./assets/logo-dark.svg"},
        }
        with tempfile.TemporaryDirectory() as scratch:
            buffer = io.BytesIO()
            with MODULE.zipfile.ZipFile(buffer, "w") as archive:
                prefix = "archive/codex-plugin/"
                archive.writestr(prefix + ".codex-plugin/plugin.json", json.dumps(manifest))
                archive.writestr(prefix + "hooks/hooks.json", '{"hooks": {}}')
                wrapper = MODULE.zipfile.ZipInfo(prefix + "hooks/deja.sh")
                wrapper.external_attr = 0o100755 << 16
                archive.writestr(wrapper, b'#!/bin/sh\nexec deja "$@"\n')
                archive.writestr(prefix + "assets/logo-dark.svg", b"<svg/>\n")
                archive.writestr("archive/unrelated.txt", b"not bundled")
            with MODULE.zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive, patch.object(
                MODULE, "fetch_repo_archive", return_value=archive
            ), patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)):
                MODULE.mirror_plugin_bundle({"owner": "vshulcz", "repo": "deja-vu"})
            output = Path(scratch) / "vshulcz/deja-vu"
            self.assertEqual((output / "hooks/deja.sh").read_bytes(), b'#!/bin/sh\nexec deja "$@"\n')
            self.assertEqual((output / "hooks/deja.sh").stat().st_mode & 0o777, 0o755)
            self.assertEqual((output / "assets/logo-dark.svg").read_bytes(), b"<svg/>\n")
            self.assertFalse((output / "unrelated.txt").exists())

    def test_metadata_only_mirror_keeps_dark_logo(self):
        root = MODULE.PurePosixPath("archive")
        selected = MODULE.collect_metadata_only_paths(
            {"interface": {"logoDark": "./assets/logo-dark.svg"}},
            {"archive/assets/logo-dark.svg", "archive/unrelated.txt"}, root,
        )
        self.assertEqual(selected, {".codex-plugin/plugin.json", "assets/logo-dark.svg"})

    def test_suede_inline_mcp_keeps_runtime_and_sibling_dependencies(self):
        runtime = {
            "mcp/suede-skills-mcp.mjs": b"import './copy-check.mjs';\n",
            "mcp/copy-check.mjs": b"export const check = true;\n",
            "mcp/catalog.json": b'{"skills": []}\n',
        }
        manifest = {
            "name": "suede-skills",
            "version": "1.0.0",
            "mcpServers": {
                "local": {"command": "node", "args": ["./mcp/suede-skills-mcp.mjs"]}
            },
        }
        with tempfile.TemporaryDirectory() as scratch:
            buffer = io.BytesIO()
            with MODULE.zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("archive/.codex-plugin/plugin.json", json.dumps(manifest))
                for path, content in runtime.items():
                    archive.writestr("archive/" + path, content)
                archive.writestr("archive/unrelated/data.txt", b"not part of the plugin")
            with MODULE.zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive, patch.object(
                MODULE, "fetch_repo_archive", return_value=archive
            ), patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)):
                MODULE.mirror_plugin_bundle({"owner": "JasonColapietro", "repo": "suede-creator-skills"})
            output = Path(scratch) / "JasonColapietro/suede-creator-skills"
            for path, content in runtime.items():
                self.assertEqual((output / path).read_bytes(), content)
            self.assertFalse((output / "unrelated/data.txt").exists())

    def test_nested_mirror_retains_nearest_license_without_overwriting_bundle_license(self):
        cases = (
            ({"LICENSE": b"repository license\n"}, {"LICENSE": b"repository license\n"}),
            ({"LICENSE": b"repository license\n", "plugins/LICENSE.txt": b"plugin collection license\n"},
             {"LICENSE.txt": b"plugin collection license\n"}),
            ({"LICENSE": b"repository license\n", "plugins/example/LICENSE.md": b"bundle license\n"},
             {"LICENSE.md": b"bundle license\n"}),
            ({"LICENSE": b"repository license\n", "plugins/example/COPYING": b"bundle copying terms\n"},
             {"COPYING": b"bundle copying terms\n"}),
            ({"license.md": b"lowercase repository license\n"}, {"license.md": b"lowercase repository license\n"}),
            ({}, {}),
        )
        for files, expected in cases:
            with self.subTest(files=files), tempfile.TemporaryDirectory() as scratch:
                buffer = io.BytesIO()
                with MODULE.zipfile.ZipFile(buffer, "w") as archive:
                    archive.writestr("archive/plugins/example/.codex-plugin/plugin.json",
                                     json.dumps({"name": "example", "version": "1.0.0"}))
                    for path, content in files.items():
                        archive.writestr("archive/" + path, content)
                with MODULE.zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive, patch.object(
                    MODULE, "fetch_repo_archive", return_value=archive
                ), patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)):
                    MODULE.mirror_plugin_bundle({"owner": "example", "repo": "example"})
                output = Path(scratch) / "example/example"
                self.assertEqual({path.name: path.read_bytes() for path in output.iterdir() if path.is_file()}, expected)

    def test_root_skill_collection_keeps_skills_and_helpers_only(self):
        root = MODULE.PurePosixPath("archive")
        for value in (".", "./"):
            with self.subTest(value=value):
                selected = MODULE.collect_selected_paths(
                    {"skills": value},
                    {f"archive/{path}" for path in (
                        "alpha/SKILL.md", "alpha/scripts/run.py",
                        "beta/SKILL.md", "beta/references/guide.md",
                        "unrelated/data.txt", "alpha/../../outside.txt",
                    )}, root, {"owner": "example", "repo": "skills"},
                )
                self.assertEqual(selected, {
                    ".codex-plugin/plugin.json", "alpha/SKILL.md",
                    "alpha/scripts/run.py", "beta/SKILL.md",
                    "beta/references/guide.md",
                })

    def test_multi_llm_mirror_retains_mcp_server_and_helpers(self):
        root = MODULE.PurePosixPath("archive/packaging/codex/multi-llm")
        paths = {
            ".codex-plugin/plugin.json", ".mcp.json", "mcp/server.py",
            "mcp/helpers/dispatch.py", "skills/multi-llm/SKILL.md",
        }
        selected = MODULE.collect_selected_paths(
            {"skills": "./skills/", "mcpServers": "./.mcp.json"},
            {f"{root}/{path}" for path in paths}, root,
            {"owner": "beastlabai", "repo": "multi-llm-plugin"},
        )
        self.assertEqual(selected, paths)

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


if __name__ == "__main__":
    unittest.main()
