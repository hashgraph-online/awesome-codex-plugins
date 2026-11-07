#!/usr/bin/env python3
"""Bounded distribution, transformation, and outlier sensitivity CLI."""

from __future__ import annotations

import argparse

from _capabilities import capability_for_path
from _common import (
    add_output_arguments,
    add_reveal_identifiers_argument,
    add_table_input_arguments,
    checked_table_input,
    emit_report,
    run_cli,
)
from _tabular import audit_distributions


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare classical and robust summaries on bounded CSV/TSV data. "
            "The command never deletes, winsorizes, transforms, or imputes source data."
        )
    )
    add_table_input_arguments(parser)
    parser.add_argument(
        "--column",
        action="append",
        help=(
            "Exact numeric column identifier; repeat as needed. Without this flag, "
            "the first 64 columns are screened."
        ),
    )
    parser.add_argument(
        "--missing-token",
        action="append",
        help="Explicit additional missing code; repeat as needed",
    )
    add_reveal_identifiers_argument(parser)
    add_output_arguments(parser)
    return parser


def _main() -> None:
    """Handle main."""
    args = build_parser().parse_args()
    path = checked_table_input(args)
    report = {
        "schema_version": "1.1",
        "capability": capability_for_path(path),
        "analysis": audit_distributions(
            path,
            columns=args.column,
            max_rows=args.max_rows,
            missing_tokens=args.missing_token,
            reveal_identifiers=args.reveal_identifiers,
        ),
        "security": {
            "local_only": True,
            "file_text_is_untrusted_data": True,
            "embedded_instructions_followed": False,
            "raw_values_and_paths_emitted": False,
        },
        "decisions": {
            "automatic_outlier_deletion": False,
            "automatic_transformation": False,
            "automatic_imputation": False,
            "hypothesis_tests_run": 0,
        },
    }
    emit_report(report, args)


def main() -> int:
    """Run the command-line interface."""
    return run_cli(_main)


if __name__ == "__main__":
    raise SystemExit(main())
