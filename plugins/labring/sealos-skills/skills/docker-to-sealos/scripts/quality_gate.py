#!/usr/bin/env python3
"""Single-entry quality gate for docker-to-sealos skill checks."""

from __future__ import annotations

import os
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List, Sequence, Tuple


def _truthy_env(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _artifact_search_roots(root: Path) -> List[Path]:
    roots: List[Path] = []
    for candidate in (Path.cwd(), root):
        if candidate in roots:
            continue
        roots.append(candidate)
    return roots


def _is_evidence_file(path: Path) -> bool:
    name = path.name.lower()
    if "runtime-bundle-evidence" in name or "topology-evidence" in name:
        return True
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:32_768]
    except OSError:
        return False
    return "kind: RuntimeBundleEvidence" in text or "kind: TopologyEvidence" in text


def _discover_artifact_files(root: Path) -> List[Path]:
    discovered: set[Path] = set()
    for search_root in _artifact_search_roots(root):
        template_dir = search_root / "template"
        if template_dir.is_dir():
            discovered.update(
                path
                for path in template_dir.rglob("index.*")
                if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
            )

        sealos_dir = search_root / ".sealos"
        if not sealos_dir.is_dir():
            continue
        topology_dir = sealos_dir / "topology-evidence"
        if topology_dir.is_dir():
            discovered.update(
                path
                for path in topology_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
            )
        discovered.update(
            path
            for path in sealos_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".yaml", ".yml"}
            and _is_evidence_file(path)
        )
    return sorted(discovered, key=str)


def _resolve_artifact_targets(root: Path, cli_artifacts: str = "") -> str:
    if cli_artifacts.strip():
        return cli_artifacts.strip()

    configured = os.environ.get("DOCKER_TO_SEALOS_ARTIFACTS", "").strip()
    if configured:
        return configured

    return ",".join(str(path) for path in _discover_artifact_files(root))


def _allow_empty_artifacts() -> bool:
    return _truthy_env("DOCKER_TO_SEALOS_ALLOW_EMPTY_ARTIFACTS")


def _strict_artifacts() -> bool:
    return (
        _truthy_env("DOCKER_TO_SEALOS_STRICT_ARTIFACTS")
        or _truthy_env("DOCKER_TO_SEALOS_STRICT")
        or _truthy_env("DOCKER_TO_SEALOS_REQUIRE_TOPOLOGY_EVIDENCE")
    )


def _contains_topology_evidence(artifacts: str) -> bool:
    for raw_path in (item.strip() for item in artifacts.split(",")):
        if not raw_path:
            continue
        path = Path(raw_path)
        normalized = str(path).lower()
        if "topology-evidence" in normalized or "runtime-bundle-evidence" in normalized:
            return True
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:32_768]
            except OSError:
                continue
            if "kind: TopologyEvidence" in text or "kind: RuntimeBundleEvidence" in text:
                return True
    return False


def parse_args(argv: Sequence[str] | None = None):
    parser = ArgumentParser(description="Run docker-to-sealos quality checks.")
    parser.add_argument(
        "--artifacts",
        default="",
        help="Comma-separated template artifact paths. Overrides DOCKER_TO_SEALOS_ARTIFACTS.",
    )
    parser.add_argument(
        "--strict",
        "--strict-artifacts",
        "--require-topology-evidence",
        dest="strict",
        action="store_true",
        help="Require auto-discovered or explicitly supplied artifacts even when empty-artifact mode is enabled.",
    )
    return parser.parse_args(argv)


def validate_artifact_targets(artifacts: str, allow_empty: bool, strict: bool = False) -> Tuple[bool, str]:
    if artifacts:
        if strict and not _contains_topology_evidence(artifacts):
            return (
                False,
                "[FAIL] strict topology mode requires a matching TopologyEvidence or RuntimeBundleEvidence artifact",
            )
        return True, ""
    if strict:
        return (
            False,
            "[FAIL] strict artifact mode requires template or evidence artifacts; "
            "expected template/*/index.yaml, .sealos/*evidence*.yaml, or DOCKER_TO_SEALOS_ARTIFACTS",
        )
    if allow_empty:
        return (
            True,
            "[WARN] no template artifacts found; skipping artifact checks due to DOCKER_TO_SEALOS_ALLOW_EMPTY_ARTIFACTS",
        )
    return (
        False,
        "[FAIL] no template artifacts found; expected template/*/index.yaml, .sealos/*evidence*.yaml, "
        "or DOCKER_TO_SEALOS_ARTIFACTS",
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


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    artifacts = _resolve_artifact_targets(root, args.artifacts)
    strict = args.strict or _strict_artifacts()
    ok, message = validate_artifact_targets(artifacts, _allow_empty_artifacts() and not strict, strict=strict)
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
