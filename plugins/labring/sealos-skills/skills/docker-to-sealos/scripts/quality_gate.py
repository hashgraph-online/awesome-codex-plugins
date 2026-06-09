#!/usr/bin/env python3
"""Single-entry quality gate for docker-to-sealos skill checks."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Sequence, Tuple


def _resolve_artifact_targets(root: Path) -> str:
    configured = os.environ.get("DOCKER_TO_SEALOS_ARTIFACTS", "").strip()
    if configured:
        return configured

    template_dir = root / "template"
    if not template_dir.exists():
        return ""

    index_files = sorted(template_dir.rglob("index.yaml"))
    if index_files:
        return ",".join(str(path) for path in index_files)
    return str(template_dir)


def _allow_empty_artifacts() -> bool:
    value = os.environ.get("DOCKER_TO_SEALOS_ALLOW_EMPTY_ARTIFACTS", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def validate_artifact_targets(artifacts: str, allow_empty: bool) -> Tuple[bool, str]:
    if artifacts:
        return True, ""
    if allow_empty:
        return (
            True,
            "[WARN] no template artifacts found; skipping artifact checks due to DOCKER_TO_SEALOS_ALLOW_EMPTY_ARTIFACTS",
        )
    return (
        False,
        "[FAIL] no template artifacts found; expected template/*/index.yaml or DOCKER_TO_SEALOS_ARTIFACTS",
    )


def build_commands(root: Path, artifacts: str) -> List[Tuple[str, Sequence[str]]]:
    scripts_dir = root / "scripts"
    python = sys.executable
    consistency_command = [
        python,
        str(scripts_dir / "check_consistency.py"),
        "--skill",
        str(root / "SKILL.md"),
        "--references",
        str(root / "references"),
        "--rules-file",
        str(root / "references" / "rules-registry.yaml"),
    ]
    if artifacts:
        consistency_command.extend(["--artifacts", artifacts])

    return [
        (
            "path converter self-test",
            (python, str(scripts_dir / "path_converter.py"), "--self-test"),
        ),
        (
            "consistency validator tests",
            (python, str(scripts_dir / "test_check_consistency.py")),
        ),
        (
            "compose converter tests",
            (python, str(scripts_dir / "test_compose_to_template.py")),
        ),
        (
            "must coverage validator tests",
            (python, str(scripts_dir / "test_check_must_coverage.py")),
        ),
        (
            "rules consistency check",
            tuple(consistency_command),
        ),
        (
            "must coverage check",
            (
                python,
                str(scripts_dir / "check_must_coverage.py"),
                "--skill",
                str(root / "SKILL.md"),
                "--mapping",
                str(root / "references" / "must-rules-map.yaml"),
                "--rules-file",
                str(root / "references" / "rules-registry.yaml"),
            ),
        ),
    ]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    artifacts = _resolve_artifact_targets(root)
    ok, message = validate_artifact_targets(artifacts, _allow_empty_artifacts())
    if message:
        print(message)
    if not ok:
        return 2

    for title, command in build_commands(root, artifacts):
        print(f"[RUN] {title}")
        result = subprocess.run(command, cwd=root)
        if result.returncode != 0:
            print(f"[FAIL] {title}")
            return result.returncode

    print("[PASS] quality gate complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
