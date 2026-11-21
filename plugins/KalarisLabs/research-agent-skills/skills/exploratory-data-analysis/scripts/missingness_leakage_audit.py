#!/usr/bin/env python3
"""Bounded missingness, group structure, and split leakage audit for CSV/TSV."""

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
from _tabular import audit_missingness_and_leakage


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Audit bounded CSV/TSV missingness and common group/entity/time split "
            "leakage. Identifiers and cell values are tokenized or omitted."
        )
    )
    add_table_input_arguments(parser)
    parser.add_argument(
        "--missing-token",
        action="append",
        help=(
            "Explicit additional missing code; repeat as needed. Empty/whitespace "
            "is always missing."
        ),
    )
    parser.add_argument(
        "--group-column",
        help="Exact column identifier for biological/experimental grouping",
    )
    parser.add_argument(
        "--entity-column",
        help="Exact subject/sample/entity identifier used to detect split overlap",
    )
    parser.add_argument(
        "--split-column",
        help="Exact train/validation/test or analysis split column identifier",
    )
    parser.add_argument(
        "--time-column",
        help="Exact ISO-8601 time column used for split interval overlap checks",
    )
    add_reveal_identifiers_argument(
        parser,
        "Emit sanitized column identifiers; values and group/entity IDs stay tokenized",
    )
    add_output_arguments(parser)
    return parser


def _main() -> None:
    """Handle main."""
    args = build_parser().parse_args()
    path = checked_table_input(args)
    report = {
        "schema_version": "1.1",
        "capability": capability_for_path(path),
        "analysis": audit_missingness_and_leakage(
            path,
            max_rows=args.max_rows,
            missing_tokens=args.missing_token,
            group_column=args.group_column,
            entity_column=args.entity_column,
            split_column=args.split_column,
            time_column=args.time_column,
            reveal_identifiers=args.reveal_identifiers,
        ),
        "security": {
            "local_only": True,
            "file_text_is_untrusted_data": True,
            "embedded_instructions_followed": False,
            "raw_values_paths_and_entity_ids_emitted": False,
        },
        "interpretation": {
            "potential_overlap_is_not_proof_of_model_leakage": True,
            "no_overlap_found_is_not_proof_of_independence": True,
            "domain_design_review_required": True,
        },
    }
    emit_report(report, args)


def main() -> int:
    """Run the command-line interface."""
    return run_cli(_main)


if __name__ == "__main__":
    raise SystemExit(main())
