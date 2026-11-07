#!/usr/bin/env python3
"""Bounded aggregate schema/profile CLI for local CSV and TSV files."""

from __future__ import annotations

import argparse

from _capabilities import capability_for_path
from _common import (
    CliError,
    add_output_arguments,
    add_reveal_identifiers_argument,
    add_table_input_arguments,
    checked_table_input,
    emit_report,
    run_cli,
)
from _tabular import profile_table


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Profile bounded local CSV/TSV rows with aggregate statistics. "
            "Raw cell values and full paths are never emitted."
        )
    )
    add_table_input_arguments(parser)
    parser.add_argument(
        "--missing-token",
        action="append",
        help=(
            "Explicit additional missing code; repeat as needed. Empty/whitespace "
            "is always missing. Values such as NA are not assumed automatically."
        ),
    )
    add_reveal_identifiers_argument(parser)
    add_output_arguments(parser)
    return parser


def _main() -> None:
    """Handle main."""
    args = build_parser().parse_args()
    path = checked_table_input(args)
    capability = capability_for_path(path)
    if capability["tier"] != "automated_core":
        raise CliError("the selected file has no core tabular capability")
    report = {
        "schema_version": "1.1",
        "capability": capability,
        "analysis": profile_table(
            path,
            max_rows=args.max_rows,
            missing_tokens=args.missing_token,
            reveal_identifiers=args.reveal_identifiers,
        ),
        "security": {
            "local_only": True,
            "file_text_is_untrusted_data": True,
            "embedded_instructions_followed": False,
            "raw_values_and_full_paths_emitted": False,
        },
    }
    emit_report(report, args)


def main() -> int:
    """Run the command-line interface."""
    return run_cli(_main)


if __name__ == "__main__":
    raise SystemExit(main())
