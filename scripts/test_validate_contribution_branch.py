"""Branch-qualified GitHub source links stay attached to scanner jobs."""

from __future__ import annotations

import difflib
import contextlib
import io
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location(
    "awesome_codex_contribution_validator",
    SCRIPTS / "validate-contribution.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load contribution validator")
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)

CENTRAL_SPEC = importlib.util.spec_from_file_location(
    "awesome_codex_centralized_validator",
    SCRIPTS / "validate-contribution-centralized.py",
)
if CENTRAL_SPEC is None or CENTRAL_SPEC.loader is None:
    raise RuntimeError("could not load centralized contribution validator")
CENTRAL = importlib.util.module_from_spec(CENTRAL_SPEC)
sys.modules[CENTRAL_SPEC.name] = CENTRAL
CENTRAL_SPEC.loader.exec_module(CENTRAL)


class BranchQualifiedContributionTests(unittest.TestCase):
    def parse_added_entry(self, url: str):
        base = "## Community Plugins\n"
        head = f"{base}\n- [WTFM]({url}) - Example plugin.\n"
        diff = "".join(
            difflib.unified_diff(
                base.splitlines(keepends=True),
                head.splitlines(keepends=True),
                fromfile="README.md",
                tofile="README.md",
                n=0,
            )
        )
        return VALIDATOR.get_new_readme_entries_from_diff(diff, base, head)[0]

    def test_repository_root_entry_has_no_explicit_source_ref(self) -> None:
        entry = self.parse_added_entry("https://github.com/SupportPages-io/wtfm")
        self.assertEqual(entry.owner, "SupportPages-io")
        self.assertEqual(entry.repo, "wtfm")
        self.assertIsNone(entry.source_ref)

    def test_branch_qualified_entry_preserves_source_ref(self) -> None:
        entry = self.parse_added_entry(
            "https://github.com/SupportPages-io/wtfm/tree/codex-plugin"
        )
        self.assertEqual(
            entry.url,
            "https://github.com/SupportPages-io/wtfm/tree/codex-plugin",
        )
        self.assertEqual(entry.source_ref, "codex-plugin")

    def test_scanner_matrix_uses_explicit_branch_only_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.json"
            branch_entry = self.parse_added_entry(
                "https://github.com/SupportPages-io/wtfm/tree/codex-plugin"
            )
            default_entry = self.parse_added_entry(
                "https://github.com/example/default-plugin"
            )
            VALIDATOR.write_matrix(matrix_path, [branch_entry, default_entry])
            self.assertEqual(
                json.loads(matrix_path.read_text(encoding="utf-8")),
                [
                    {"owner": "SupportPages-io", "repo": "wtfm", "ref": "codex-plugin"},
                    {"owner": "example", "repo": "default-plugin"},
                ],
            )

    def test_open_pr_scanner_matrix_carries_the_branch_ref(self) -> None:
        entry = CENTRAL.VALIDATOR.Contribution(
            display_name="WTFM",
            url="https://github.com/SupportPages-io/wtfm/tree/codex-plugin",
            owner="SupportPages-io",
            repo="wtfm",
            description="Example plugin.",
            source_ref="codex-plugin",
        )
        pull_request = CENTRAL.VALIDATOR.OpenPullRequest(
            number=558,
            title="Add WTFM",
            head_repository="contributor/awesome-codex-plugins",
            head_ref="add-wtfm",
            head_sha="a" * 40,
            base_ref="main",
            base_sha="b" * 40,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            matrix_path = temp_path / "matrix.json"
            report_path = temp_path / "report.md"
            status_path = temp_path / "status.json"
            with (
                patch.object(
                    CENTRAL.VALIDATOR,
                    "list_open_pull_requests",
                    return_value=[pull_request],
                ),
                patch.object(
                    CENTRAL.VALIDATOR,
                    "entries_for_open_pull_request",
                    return_value=[entry],
                ),
                patch.object(CENTRAL, "ensure_public_repository"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = CENTRAL.scan_open_pull_requests(
                    "hashgraph-online/awesome-codex-plugins",
                    558,
                    matrix_path,
                    report_path,
                    status_path,
                )
            self.assertEqual(result, 0)
            self.assertEqual(
                json.loads(matrix_path.read_text(encoding="utf-8")),
                [
                    {
                        "pr_number": 558,
                        "owner": "SupportPages-io",
                        "repo": "wtfm",
                        "ref": "codex-plugin",
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()
