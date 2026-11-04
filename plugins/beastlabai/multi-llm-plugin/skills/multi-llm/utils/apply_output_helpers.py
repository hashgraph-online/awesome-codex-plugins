"""Output assembly utilities for apply orchestrators.

Provides shared functions for writing orchestrator output JSON files,
emitting output markers, and printing JSON to stdout. Extracted from
the three apply orchestrators.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


def write_and_emit_output(
    output: Dict[str, Any],
    phase_dir: str,
    filename: str = "orchestrator_output.json",
) -> Path:
    """Write orchestrator output to a JSON file and emit the [OUTPUT_FILE] marker.

    This is the shared pattern used by all three apply orchestrators:
    1. Ensure the phase directory exists
    2. Write the output dict as JSON to ``phase_dir/filename``
    3. Print ``[OUTPUT_FILE] <path>`` to stderr

    Args:
        output: The orchestrator output dictionary to serialize.
        phase_dir: Directory for the phase (e.g., ``out_dir/apply-suggestions``).
        filename: Name of the output file (default: ``orchestrator_output.json``).

    Returns:
        The Path to the written output file.
    """
    os.makedirs(phase_dir, exist_ok=True)
    output_file = Path(phase_dir) / filename
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"[OUTPUT_FILE] {output_file}", file=sys.stderr)
    return output_file


def emit_json_output(output: Dict[str, Any]) -> None:
    """Print orchestrator output as formatted JSON to stdout.

    This is the standard way all three apply orchestrators emit their
    JSON output for Claude Code to consume.
    """
    print(json.dumps(output, indent=2))


def build_skipped_output(
    phase: str,
    message: str,
) -> Dict[str, Any]:
    """Build a standard skipped-phase output dictionary.

    Used when an apply phase has no actionable findings and should be
    skipped cleanly. All three orchestrators produce the same shape.

    Args:
        phase: The phase name (e.g., ``apply-task-suggestions``).
        message: Human-readable skip reason.

    Returns:
        Output dict with status='skipped', the message, phase, and empty batches.
    """
    return {
        "status": "skipped",
        "message": message,
        "phase": phase,
        "batches": [],
    }


def build_confirmation_needed_output(
    phase: str,
    message: str,
    item_count: int,
) -> Dict[str, Any]:
    """Build a standard confirmation-needed output dictionary.

    Used when no user selections are found and the orchestrator needs
    the user to confirm before proceeding. All three orchestrators
    produce the same shape.

    Args:
        phase: The phase name.
        message: Human-readable message explaining what will happen.
        item_count: Number of items that would be applied.

    Returns:
        Output dict with status='confirmation_needed'.
    """
    return {
        "status": "confirmation_needed",
        "message": message,
        "phase": phase,
        "item_count": item_count,
    }
