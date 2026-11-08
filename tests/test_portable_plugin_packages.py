"""Portable manifests must keep their canonical metadata and runtime files."""

import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


generator = module("portable_generator", "generate_plugins_json.py")
validator = module("portable_validator", "validate-plugin-pr.py")
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
ICON = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10v10H0z"/></svg>'


def manifest():
    return {
        "$schema": SCHEMA, "name": "demo", "version": "1.0.0",
        "description": "A portable research plugin",
        "repository": "https://github.com/maker/demo", "license": "MIT",
        "extensions": {"com.openai": {"interface": {
            "displayName": "Demo", "shortDescription": "Research tools",
            "composerIcon": "./assets/icon.svg",
        }}},
    }


def archive(root=None, legacy=None, extra=None):
    files = {
        "assets/icon.svg": ICON,
        "skills/research/SKILL.md": b"---\nname: research\ndescription: Research supplied material\n---\n# Research\n",
        "mcp.json": json.dumps({"mcpServers": {"demo": {
            "type": "streamable-http", "url": "https://example.com/mcp",
        }}}).encode(),
        "LICENSE": b"MIT\n", ".codexignore": b"", "README.md": b"# Demo\n",
    }
    if root is not None:
        files["plugin.json"] = json.dumps(root).encode()
    if legacy is not None:
        files[".codex-plugin/plugin.json"] = json.dumps(legacy).encode()
    files.update(extra or {})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as zipped:
        for name, contents in files.items():
            zipped.writestr("source/plugins/demo/" + name, contents)
    return zipfile.ZipFile(io.BytesIO(stream.getvalue()))


class PortablePluginPackagesTests(unittest.TestCase):
    def remote(self, source):
        with patch.object(validator, "fetch_repo_archive", return_value=source):
            return validator.validate_remote_repo("maker", "demo")

    def test_portable_only_source_validates_without_compatibility_manifest(self):
        with archive(manifest()) as source:
            errors, _ = self.remote(source)
        self.assertEqual(errors, [])

    def test_inline_extension_replaces_stale_overlay(self):
        stale = {"name": "stale", "interface": {"composerIcon": "./missing.png"},
                 "hooks": "./missing-hooks.json", "skills": "./missing-skills"}
        with archive(manifest(), stale) as source:
            effective = validator.load_manifest_from_archive(source, validator.find_plugin_root(source))
            errors, _ = self.remote(source)
        self.assertEqual(errors, [])
        self.assertEqual(effective["name"], "demo")
        self.assertNotIn("hooks", effective)

    def test_absent_inline_extension_uses_overlay_without_replacing_identity(self):
        root = manifest()
        overlay = root.pop("extensions")["com.openai"]
        overlay.update(name="stale", version="9", repository="https://example.com/wrong")
        with archive(root, overlay) as source:
            effective = generator.load_manifest(source, generator.resolve_plugin_root(source, set(source.namelist()), {"name": "demo"}))
            errors, _ = self.remote(source)
        self.assertEqual(errors, [])
        self.assertEqual(effective["name"], "demo")
        self.assertEqual(effective["version"], "1.0.0")

    def test_empty_inline_extension_does_not_fall_back_to_overlay(self):
        root = manifest()
        overlay = root["extensions"]["com.openai"]
        root["extensions"]["com.openai"] = {}
        with archive(root, overlay) as source:
            errors, _ = self.remote(source)
        self.assertTrue(any("interface" in error for error in errors), errors)

    def test_overlay_directory_settings_survive_portable_fallback(self):
        root = manifest()
        overlay = root.pop("extensions")["com.openai"]
        overlay["extensions"] = {"com.openai": {"review": {"instructions": "Review changes"}}}
        with archive(root, overlay) as source:
            effective = validator.load_manifest_from_archive(source, validator.find_plugin_root(source))
        self.assertEqual(effective["review"], {"instructions": "Review changes"})

    def test_portable_root_does_not_supply_legacy_openai_settings(self):
        root = manifest()
        root["interface"] = root["extensions"]["com.openai"]["interface"]
        root["hooks"] = "./unselected-hooks.json"
        root["extensions"]["com.openai"] = {}
        with archive(root) as source:
            effective = validator.load_manifest_from_archive(source, validator.find_plugin_root(source))
            errors, _ = self.remote(source)
        self.assertNotIn("hooks", effective)
        self.assertTrue(any("interface" in error for error in errors), errors)

    def test_portable_components_ignore_overlay_replacements(self):
        root = manifest()
        root["extensions"]["com.openai"].update(skills="./missing", mcpServers="./missing.json")
        with archive(root) as source:
            effective = validator.load_manifest_from_archive(source, validator.find_plugin_root(source))
            errors, _ = self.remote(source)
        self.assertEqual(errors, [])
        self.assertEqual(effective["skills"], "./skills/")
        self.assertEqual(effective["mcpServers"], "./mcp.json")

    def test_mirror_keeps_portable_manifest_mcp_skills_and_icon(self):
        root = manifest()
        with tempfile.TemporaryDirectory() as scratch, archive(root) as source:
            with patch.object(generator, "fetch_repo_archive", return_value=source), patch.object(generator, "PLUGINS_ROOT", Path(scratch) / "plugins"):
                effective, location, _ = generator.mirror_plugin_bundle({"owner": "maker", "repo": "demo", "name": "Demo"})
            package = Path(scratch) / location.removeprefix("./")
            for name in ["plugin.json", "mcp.json", "skills/research/SKILL.md", "assets/icon.svg", ".codex-plugin/plugin.json"]:
                self.assertTrue((package / name).is_file(), name)
            self.assertEqual(json.loads((package / "plugin.json").read_text()), root)
            self.assertEqual(effective["mcpServers"], "./mcp.json")
            with patch.object(validator, "REPO_ROOT", Path(scratch)), patch.object(validator, "README_PATH", Path(scratch) / "README.md"):
                errors, _ = validator.validate_local_bundle(package)
            self.assertEqual(errors, [])

    def test_mcp_and_icon_limits_still_apply(self):
        for files, expected in [({"mcp.json": b"[]"}, "JSON object"),
                                ({"assets/icon.svg": b"x" * 51201}, "exceeds")]:
            with self.subTest(expected=expected), archive(manifest(), extra=files) as source:
                errors, _ = self.remote(source)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_compatibility_manifest_keeps_directory_settings_namespaced(self):
        root = manifest()
        extra = {"onboardingSkill": "./skills/setup/SKILL.md", "review": {"instructions": "Review supplied changes"}, "publication": {"requires_local_executor": True}}
        root["extensions"]["com.openai"].update(extra)
        with tempfile.TemporaryDirectory() as scratch, archive(root, extra={"skills/setup/SKILL.md": b"# Setup\n"}) as source:
            with patch.object(generator, "fetch_repo_archive", return_value=source), patch.object(generator, "PLUGINS_ROOT", Path(scratch) / "plugins"):
                _, location, _ = generator.mirror_plugin_bundle({"owner": "maker", "repo": "demo", "name": "Demo"})
            package = Path(scratch) / location.removeprefix("./")
            compatible = json.loads((package / ".codex-plugin/plugin.json").read_text())
            self.assertEqual(compatible["extensions"]["com.openai"], extra)
            self.assertTrue(all(key not in compatible for key in extra))
            self.assertEqual(json.loads((package / "plugin.json").read_text()), root)

    def test_unrecognized_root_manifest_keeps_legacy_behavior(self):
        legacy = manifest()
        legacy.pop("$schema")
        legacy["interface"] = legacy.pop("extensions")["com.openai"]["interface"]
        with archive({"name": "unrelated-app"}, legacy) as source:
            errors, _ = self.remote(source)
        self.assertEqual(errors, [])

    def test_unrecognized_invalid_root_file_does_not_replace_legacy_manifest(self):
        legacy = manifest()
        legacy.pop("$schema")
        legacy["interface"] = legacy.pop("extensions")["com.openai"]["interface"]
        with archive(legacy=legacy, extra={"plugin.json": b"not a JSON manifest"}) as source:
            errors, _ = self.remote(source)
        self.assertEqual(errors, [])

    def test_invalid_openai_extension_is_not_replaced_by_legacy_overlay(self):
        root = manifest()
        overlay = root["extensions"]["com.openai"]
        root["extensions"]["com.openai"] = "invalid"
        with archive(root, overlay) as source:
            errors, _ = self.remote(source)
        self.assertTrue(errors)

    def test_portable_package_cannot_bypass_metadata_only_sanitization(self):
        with tempfile.TemporaryDirectory() as scratch, archive(manifest()) as source:
            with patch.object(generator, "fetch_repo_archive", return_value=source), patch.object(generator, "PLUGINS_ROOT", Path(scratch)), patch.object(generator, "is_metadata_only_mirror", return_value=True):
                with self.assertRaisesRegex(ValueError, "complete bundle"):
                    generator.mirror_plugin_bundle({"owner": "maker", "repo": "demo", "name": "Demo"})

    def test_portable_install_url_uses_root_manifest(self):
        url = generator.build_raw_manifest_url({"owner": "maker", "repo": "demo", "source_ref": "feature/portable"}, "plugins/demo", "plugin.json")
        self.assertEqual(url, "https://raw.githubusercontent.com/maker/demo/feature/portable/plugins/demo/plugin.json")


if __name__ == "__main__":
    unittest.main()
