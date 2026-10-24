"""Check that every distribution channel exposes the same single skill."""

import json
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text())


class PackagingTests(unittest.TestCase):
    def test_native_manifests_export_the_existing_skill_and_version(self):
        skill = (ROOT / "SKILL.md").read_text()
        name = re.search(r"^name:\s*(.+)$", skill, re.MULTILINE).group(1)
        version = re.search(r'^\s+version:\s*"([^"]+)"$', skill, re.MULTILINE).group(1)
        for platform in (".claude-plugin", ".codex-plugin"):
            with self.subTest(platform=platform):
                manifest = read_json(f"{platform}/plugin.json")
                self.assertEqual(manifest["name"], name)
                self.assertEqual(manifest["version"], version)
                skill_root = (ROOT / manifest["skills"]).resolve()
                self.assertEqual(skill_root, ROOT)
                self.assertTrue((skill_root / "SKILL.md").is_file())
                self.assertTrue((skill_root / "references").is_dir())
                self.assertTrue((skill_root / "scripts" / "split_coverage.py").is_file())

    def test_marketplaces_resolve_the_native_plugin(self):
        claude = read_json(".claude-plugin/marketplace.json")
        codex = read_json(".agents/plugins/marketplace.json")
        self.assertEqual(claude["name"], codex["name"])
        for platform, marketplace in ((".claude-plugin", claude), (".codex-plugin", codex)):
            with self.subTest(platform=platform):
                self.assertEqual(len(marketplace["plugins"]), 1)
                entry = marketplace["plugins"][0]
                source = entry["source"]
                relative = source if isinstance(source, str) else source["path"]
                plugin_root = (ROOT / relative).resolve()
                self.assertEqual(plugin_root, ROOT)
                manifest = json.loads((plugin_root / platform / "plugin.json").read_text())
                self.assertEqual(entry["name"], manifest["name"])

    def test_distribution_has_only_one_skill_entrypoint(self):
        paths = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
        ).decode().split("\0")
        entrypoints = {path for path in paths if Path(path).name == "SKILL.md"}
        self.assertEqual(entrypoints, {"SKILL.md"})

    def test_readme_install_is_unpinned_and_archive_matches_the_skill_version(self):
        skill = (ROOT / "SKILL.md").read_text()
        version = re.search(r'^\s+version:\s*"([^"]+)"$', skill, re.MULTILINE).group(1)
        readme = (ROOT / "README.md").read_text()
        install_sources = re.findall(r"^npx skills add (\S+) --skill stacked-prs$", readme, re.MULTILINE)
        archive_tags = re.findall(r"stacked-prs-skill/archive/refs/tags/(v[\d.]+)\.zip", readme)
        self.assertEqual(install_sources, ["https://github.com/Qabbout/stacked-prs-skill"])
        self.assertEqual(archive_tags, [f"v{version}"])


if __name__ == "__main__":
    unittest.main()
