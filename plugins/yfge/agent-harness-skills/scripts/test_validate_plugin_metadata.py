#!/usr/bin/env python3
"""Tests for plugin metadata validation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "validate_plugin_metadata", SCRIPT_DIR / "validate_plugin_metadata.py"
)
assert SPEC is not None
assert SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def make_repo(root: Path) -> None:
    (root / "skills" / "sample-skill").mkdir(parents=True)
    (root / "skills" / "sample-skill" / "SKILL.md").write_text(
        "# Sample\n",
        encoding="utf-8",
    )
    (root / "GEMINI.md").write_text("# Gemini\n", encoding="utf-8")
    (root / ".opencode" / "plugins").mkdir(parents=True)
    (root / ".opencode" / "plugins" / "agent-harness-skills.js").write_text(
        "export default async () => ({});\n",
        encoding="utf-8",
    )

    base = {
        "name": "agent-harness-skills",
        "version": "0.1.0",
        "description": "Reusable skills for building agent-ready repository harnesses.",
        "license": "MIT",
    }
    write_json(
        root / ".codex-plugin" / "plugin.json",
        {
            "id": "agent-harness-skills",
            **base,
            "author": {"name": "Agent Harness Skills contributors"},
            "homepage": "https://example.com/agent-harness-skills",
            "repository": "https://example.com/agent-harness-skills.git",
            "skills": "./skills/",
            "interface": {
                "displayName": "Agent Harness Skills",
                "shortDescription": "Repo harness practices for agent-ready engineering work",
                "longDescription": "Use Agent Harness Skills to assess and design repositories.",
                "developerName": "Agent Harness Skills contributors",
                "category": "Coding",
                "capabilities": ["Interactive", "Read", "Write"],
                "defaultPrompt": "Assess this repository's agent harness maturity.",
            },
        },
    )
    write_json(root / ".claude-plugin" / "plugin.json", base)
    write_json(
        root / ".cursor-plugin" / "plugin.json",
        {**base, "displayName": "Agent Harness Skills", "skills": "./skills/"},
    )
    write_json(root / "gemini-extension.json", {**base, "contextFileName": "GEMINI.md"})
    write_json(root / "package.json", {**base, "main": ".opencode/plugins/agent-harness-skills.js"})


class ValidatePluginMetadataTest(unittest.TestCase):
    def test_valid_metadata_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)

            self.assertEqual([], validator.validate_metadata(root))

    def test_missing_codex_skills_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            payload = json.loads(
                (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            payload["skills"] = "./missing-skills/"
            write_json(root / ".codex-plugin" / "plugin.json", payload)

            issues = validator.validate_metadata(root)

            self.assertTrue(any("skills" in issue.message for issue in issues), issues)

    def test_package_main_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_repo(root)
            payload = json.loads((root / "package.json").read_text(encoding="utf-8"))
            payload["main"] = ".opencode/plugins/missing.js"
            write_json(root / "package.json", payload)

            issues = validator.validate_metadata(root)

            self.assertTrue(any("main" in issue.message for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
