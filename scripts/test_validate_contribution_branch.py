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

    def test_branch_refs_accept_plus_and_slash_characters(self) -> None:
        for ref in ("feat+plugin", "release@v1", "release/v1"):
            with self.subTest(ref=ref):
                entry = self.parse_added_entry(
                    f"https://github.com/SupportPages-io/wtfm/tree/{ref}"
                )
                self.assertEqual(entry.source_ref, ref)

    def test_branch_ref_comparison_preserves_case(self) -> None:
        base = (
            "## Community Plugins\n"
            "- [WTFM](https://github.com/SupportPages-io/wtfm/tree/Main) - Existing.\n"
        )
        head = base.replace("/tree/Main", "/tree/main")
        diff = "".join(
            difflib.unified_diff(
                base.splitlines(keepends=True),
                head.splitlines(keepends=True),
                fromfile="README.md",
                tofile="README.md",
                n=0,
            )
        )

        entries = VALIDATOR.get_new_readme_entries_from_diff(diff, base, head)

        self.assertEqual([entry.source_ref for entry in entries], ["main"])

    def test_unresolvable_source_ref_fails_before_scanning(self) -> None:
        entry = self.parse_added_entry(
            "https://github.com/SupportPages-io/wtfm/tree/codex-plugin"
        )
        with patch.object(
            VALIDATOR,
            "github_json",
            side_effect=VALIDATOR.ValidationError("source repository or workflow directory was not found"),
        ):
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "branch.*does not exist"):
                VALIDATOR.ensure_source_ref_exists(entry)

    def test_source_ref_lookup_rejects_case_mismatches(self) -> None:
        entry = self.parse_added_entry(
            "https://github.com/SupportPages-io/wtfm/tree/main"
        )
        with patch.object(
            VALIDATOR,
            "github_json",
            return_value={"name": "Main"},
        ):
            with self.assertRaisesRegex(VALIDATOR.ValidationError, "exact ref"):
                VALIDATOR.ensure_source_ref_exists(entry)

    def test_source_ref_lookup_encodes_slash_branch_names(self) -> None:
        entry = self.parse_added_entry(
            "https://github.com/SupportPages-io/wtfm/tree/release/v1"
        )
        with patch.object(
            VALIDATOR,
            "github_json",
            return_value={"name": "release/v1"},
        ) as github_json:
            VALIDATOR.ensure_source_ref_exists(entry)

        self.assertEqual(
            github_json.call_args.args[0],
            "https://api.github.com/repos/SupportPages-io/wtfm/branches/release%2Fv1",
        )

    def test_branch_scanner_workflows_are_read_at_the_linked_ref(self) -> None:
        workflow = "name: Scan\non:\n  push: {}\njobs: {}\n"
        with (
            patch.object(
                VALIDATOR,
                "request_bytes",
                return_value=b'[{"name":"scan.yml","type":"file"}]',
            ) as request,
            patch.object(VALIDATOR, "content_file", return_value=workflow) as content,
        ):
            files = VALIDATOR.workflow_files("example", "plugin", "feat+plugin")

        self.assertEqual(files, [("scan.yml", workflow)])
        self.assertIn("ref=feat%2Bplugin", request.call_args.args[0])
        content.assert_called_once_with(
            "example/plugin", ".github/workflows/scan.yml", "feat+plugin"
        )

    def test_standalone_open_pr_matrix_does_not_require_source_scanner_ci(self) -> None:
        entry = self.parse_added_entry(
            "https://github.com/SupportPages-io/wtfm/tree/codex-plugin"
        )
        pull_request = VALIDATOR.OpenPullRequest(
            number=558,
            title="Add WTFM",
            head_repository="contributor/awesome-codex-plugins",
            head_ref="add-wtfm",
            head_sha="a" * 40,
            base_ref="main",
            base_sha="b" * 40,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.json"
            report_path = Path(temp_dir) / "report.md"
            status_path = Path(temp_dir) / "status.json"
            with (
                patch.object(VALIDATOR, "list_open_pull_requests", return_value=[pull_request]),
                patch.object(VALIDATOR, "entries_for_open_pull_request", return_value=[entry]),
                patch.object(VALIDATOR, "ensure_public_repository"),
                patch.object(VALIDATOR, "ensure_source_ref_exists"),
                patch.object(VALIDATOR, "validate_scanner_ci", side_effect=AssertionError("scanner CI is optional")),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = VALIDATOR.scan_open_pull_requests(
                    "hashgraph-online/awesome-codex-plugins",
                    558,
                    matrix_path,
                    report_path,
                    status_path,
                )

            self.assertEqual(result, 0)
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
            self.assertEqual(
                matrix,
                [{"pr_number": 558, "owner": "SupportPages-io", "repo": "wtfm", "ref": "codex-plugin"}],
            )
            self.assertIn("centralized score scan", report_path.read_text(encoding="utf-8"))

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
                patch.object(CENTRAL.VALIDATOR, "ensure_source_ref_exists"),
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
