"""Build the ``inputs`` block for analyzer output envelopes.

Thin helper that centralizes SHA-256 computation, run_id generation, and
config-hash resolution so every analyzer builds its ``inputs`` block the
same way.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_id import generate_run_id  # noqa: E402


def _sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of the file at ``path``."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_inputs(
    source_files: Iterable[Path | str],
    *,
    config_path: Path | str | None = None,
    upstream_artifacts: dict | None = None,
    run_id: str | None = None,
) -> dict:
    """Build a dict matching the ``InputsBlock`` envelope shape.

    Parameters
    ----------
    source_files : Iterable[Path | str]
        Paths of every file read from disk for this run. Hashed
        individually.
    config_path : Path | str | None, optional
        Path to the resolved .kicad-happy.json config file, if any.
    upstream_artifacts : dict | None, optional
        Pre-built mapping of stage name -> UpstreamArtifact dict. Passed
        through as-is; callers are responsible for correct shape.
    run_id : str | None, optional
        Explicit run_id. **In production every analyzer call site passes
        this explicitly from `capability_mode_ref["run_id"]`** so the
        envelope's `inputs.run_id` is byte-identical to the canonical
        capability_mode record (audit A1/A2, locked harness-side by
        `validate/validate_run_id.py`). The auto-gen fallback below
        only triggers for test fixtures and synthetic harness cases
        that intentionally bypass capability_mode (see
        `tests/contract/test_inputs_builder.py::test_run_id_auto_generated_when_omitted`).
        Calling this without a run_id from product code would produce a
        non-canonical envelope that fails `validate_run_id.py` — don't.
    """
    paths = [Path(f) for f in source_files]
    source_hashes = {str(p): _sha256_file(p) for p in paths}
    config_hash = _sha256_file(Path(config_path)) if config_path else None
    return {
        "source_files": [str(p) for p in paths],
        "source_hashes": source_hashes,
        # Auto-gen fallback is for test fixtures only. Production callers
        # pass capability_mode_ref["run_id"] — see docstring above.
        "run_id": run_id or generate_run_id(),
        "config_hash": config_hash,
        "upstream_artifacts": upstream_artifacts or {},
    }


def build_upstream_artifact(path: Path | str, parsed: dict) -> dict:
    """Build one UpstreamArtifact dict from a parsed analyzer JSON.

    ``path`` is the filesystem path the analyzer read the JSON from.
    ``parsed`` is the JSON's decoded Python dict — we read its
    ``schema_version`` and ``inputs.run_id`` fields for the artifact
    metadata.
    """
    path = Path(path)
    sha = _sha256_file(path)
    return {
        "path": str(path),
        "sha256": sha,
        "schema_version": parsed.get("schema_version", ""),
        "run_id": parsed.get("inputs", {}).get("run_id", ""),
    }


def build_compat(
    minimum_consumer_version: str = "1.4.0",
    deprecated_fields: list[str] | None = None,
    experimental_fields: list[str] | None = None,
) -> dict:
    """Build a dict matching the ``CompatBlock`` envelope shape.

    Defaults reflect v1.4 state: the clean break removed prior residue so
    both lists start empty. Bump ``minimum_consumer_version`` when the
    envelope shape breaks in ways a consumer needs to detect.
    """
    return {
        "minimum_consumer_version": minimum_consumer_version,
        "deprecated_fields": list(deprecated_fields) if deprecated_fields else [],
        "experimental_fields": list(experimental_fields) if experimental_fields else [],
    }
