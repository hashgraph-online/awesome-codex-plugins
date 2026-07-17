#!/usr/bin/env python3
"""Pure subject identity, scope, and verdict.v2 persistence helpers.

The module intentionally has no Git, tracker, queue, network, release, or
delivery integration. It operates only on explicit files and directories.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
from typing import Any, Iterable


HEX64 = set("0123456789abcdef")


class ContractError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def normalize_rel(raw: str) -> str:
    raw = raw.replace("\\", "/")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"path escapes subject root: {raw}")
    normalized = path.as_posix()
    if normalized in ("", "."):
        return "."
    return normalized.removeprefix("./")


def path_matches(path: str, pattern: str) -> bool:
    pattern = normalize_rel(pattern)
    if pattern == ".":
        return True
    if any(ch in pattern for ch in "*?["):
        return fnmatch.fnmatchcase(path, pattern)
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


def is_excluded(path: str, exclusions: Iterable[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in exclusions)


def entry_for(root: Path, rel: str) -> dict[str, Any]:
    full = root if rel == "." else root / rel
    info = full.lstat()
    executable = bool(info.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    if full.is_symlink():
        target = os.readlink(full).encode("utf-8")
        return {"path": rel, "kind": "symlink", "executable": executable, "digest": hashlib.sha256(target).hexdigest()}
    if full.is_file():
        return {"path": rel, "kind": "file", "executable": executable, "digest": hashlib.sha256(full.read_bytes()).hexdigest()}
    raise ContractError(f"unsupported subject kind: {rel}")


def walk_declared(root: Path, declared: str, exclusions: list[str]) -> list[dict[str, Any]]:
    full = root if declared == "." else root / declared
    if not full.exists() and not full.is_symlink():
        return []
    if full.is_file() or full.is_symlink():
        return [] if is_excluded(declared, exclusions) else [entry_for(root, declared)]
    entries: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(full, followlinks=False):
        current = Path(dirpath)
        kept_dirs: list[str] = []
        for name in sorted(dirnames):
            child = current / name
            rel = normalize_rel(child.relative_to(root).as_posix())
            if is_excluded(rel, exclusions):
                continue
            if child.is_symlink():
                entries.append(entry_for(root, rel))
            else:
                kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            rel = normalize_rel((current / name).relative_to(root).as_posix())
            if not is_excluded(rel, exclusions):
                entries.append(entry_for(root, rel))
    return entries


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"expected JSON object: {path}")
    return value


def build_manifest(
    root: Path,
    declared_roots: list[str],
    exclusions: list[str],
    base_manifest: dict[str, Any] | None = None,
    git_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ContractError(f"subject root is not a directory: {root}")
    declared = sorted(set(normalize_rel(item) for item in declared_roots))
    if not declared:
        raise ContractError("at least one declared root is required")
    excluded = sorted(set(normalize_rel(item) for item in exclusions))
    by_path: dict[str, dict[str, Any]] = {}
    for item in declared:
        for entry in walk_declared(root, item, excluded):
            by_path[entry["path"]] = entry

    manifest: dict[str, Any] = {
        "schema_version": "subject-manifest.v1",
        "declared_roots": declared,
        "exclusions": excluded,
        "entries": sorted(by_path.values(), key=lambda item: item["path"]),
    }
    if base_manifest is not None:
        base_digest = base_manifest.get("canonical_manifest_digest")
        if not valid_digest(base_digest):
            raise ContractError("base manifest has no valid canonical_manifest_digest")
        manifest["base_manifest_digest"] = base_digest
        current = set(by_path)
        deletions = []
        for prior in base_manifest.get("entries", []):
            path = normalize_rel(str(prior.get("path", "")))
            declared_here = any(path_matches(path, item) for item in declared)
            if declared_here and path not in current and not is_excluded(path, excluded):
                deletions.append({"path": path, "kind": "deletion", "executable": bool(prior.get("executable", False))})
        manifest["entries"] = sorted(manifest["entries"] + deletions, key=lambda item: item["path"])
    if git_metadata:
        manifest["git_metadata"] = git_metadata
    manifest["canonical_manifest_digest"] = digest_value(manifest_identity(manifest))
    return manifest


def valid_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in HEX64 for ch in value)


def manifest_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return only the fields that identify subject content.

    ``git_metadata`` is intentionally descriptive.  Supplying or changing it
    must never change the identity of otherwise identical content.
    """
    return {
        key: value
        for key, value in manifest.items()
        if key not in {"canonical_manifest_digest", "git_metadata"}
    }


def verify_manifest(manifest: dict[str, Any], root: Path, base_manifest: dict[str, Any] | None) -> tuple[bool, str]:
    claimed = manifest.get("canonical_manifest_digest")
    if not valid_digest(claimed) or digest_value(manifest_identity(manifest)) != claimed:
        return False, "manifest canonical digest is invalid"
    rebuilt = build_manifest(
        root,
        list(manifest.get("declared_roots", [])),
        list(manifest.get("exclusions", [])),
        base_manifest,
        manifest.get("git_metadata"),
    )
    if canonical_bytes(rebuilt) != canonical_bytes(manifest):
        return False, "subject content no longer matches manifest"
    return True, "manifest matches subject"


def add_integrity_finding(draft: dict[str, Any], summary: str) -> dict[str, Any]:
    changed = dict(draft)
    changed["verdict"] = "NOT_PROVEN"
    findings = list(changed.get("findings") or [])
    findings.append({"id": "validate.integrity", "summary": summary, "evidence_refs": ["verdict-store"]})
    changed["findings"] = findings
    return changed


def bind_runtime_facts(
    draft: dict[str, Any],
    intent_bytes: bytes | None,
    manifest: dict[str, Any] | None,
    author_context_id: str | None,
    scope_status: str | None,
) -> dict[str, Any]:
    """Inject runtime-owned intent, subject, author, and scope facts."""
    changed = dict(draft)
    problems: list[str] = []
    if intent_bytes is None:
        problems.append("runtime intent source is missing")
    else:
        changed["acceptance_digest"] = hashlib.sha256(intent_bytes).hexdigest()
    if not isinstance(manifest, dict):
        problems.append("runtime subject manifest is missing")
    else:
        claimed = manifest.get("canonical_manifest_digest")
        if not valid_digest(claimed) or digest_value(manifest_identity(manifest)) != claimed:
            problems.append("runtime subject manifest digest is invalid")
        else:
            changed["subject_manifest_digest"] = claimed
    if not isinstance(author_context_id, str) or not author_context_id.strip():
        problems.append("runtime author context ID is missing")
    else:
        changed["author_context_id"] = author_context_id
    if scope_status == "FAIL":
        changed["verdict"] = "FAIL"
        findings = list(changed.get("findings") or [])
        findings.append({"id": "validate.scope", "summary": "runtime-derived changed paths are outside intent scope", "evidence_refs": ["runtime-scope"]})
        changed["findings"] = findings
    elif scope_status != "PASS":
        problems.append("runtime changed-path scope is not proven")
    if problems:
        return add_integrity_finding(changed, "; ".join(problems))
    return changed


def enforce_identity(draft: dict[str, Any]) -> dict[str, Any]:
    draft = dict(draft)
    draft.setdefault("author_context_id", None)
    draft.setdefault("validator_context_id", None)
    draft.setdefault("freshness_attestation", None)
    author = draft.get("author_context_id")
    validator = draft.get("validator_context_id")
    freshness = draft.get("freshness_attestation")
    problems = []
    if not isinstance(author, str) or not author.strip():
        problems.append("author context ID is missing")
    if not isinstance(validator, str) or not validator.strip():
        problems.append("validator context ID is missing")
    if author and validator and author == validator:
        problems.append("author and validator context IDs collide")
    if not isinstance(freshness, dict) or freshness.get("source") not in ("runtime", "caller") or not freshness.get("attester_identity"):
        problems.append("freshness attestation is missing or invalid")
    if draft.get("verdict") == "PASS" and (draft.get("not_checked") or []):
        problems.append("PASS cannot contain not_checked items")
    criteria = draft.get("criteria")
    if draft.get("verdict") == "PASS" and (
        not isinstance(criteria, list)
        or not criteria
        or any(not isinstance(item, dict) or item.get("result") != "PASS" for item in criteria)
    ):
        problems.append("PASS requires at least one criterion and every criterion must PASS")
    if draft.get("verdict") == "PASS" and (
        any(
            not isinstance(item, dict)
            or not isinstance(item.get("evidence_refs"), list)
            or not item["evidence_refs"]
            for item in criteria or []
        )
        or not draft.get("evidence_refs")
        or not draft.get("checked")
    ):
        problems.append("PASS requires evidence for every criterion plus nonempty evidence_refs and checked")
    if problems:
        return add_integrity_finding(draft, "; ".join(problems))
    return draft


VERDICT_KEYS = {
    "schema_version",
    "acceptance_digest",
    "subject_manifest_digest",
    "author_context_id",
    "validator_context_id",
    "freshness_attestation",
    "verdict",
    "criteria",
    "findings",
    "evidence_refs",
    "checked",
    "not_checked",
    "validated_at",
    "artifact_digest",
}


def require_string_list(value: Any, field: str, *, nonempty: bool = False) -> None:
    if not isinstance(value, list) or (nonempty and not value):
        raise ContractError(f"verdict.v2 {field} must be a{' nonempty' if nonempty else ''} array")
    if any(not isinstance(item, str) or not item for item in value):
        raise ContractError(f"verdict.v2 {field} entries must be nonempty strings")


def validate_verdict_v2(artifact: dict[str, Any]) -> None:
    """Enforce the complete bundled verdict.v2 contract before persistence."""
    missing = sorted(VERDICT_KEYS - artifact.keys())
    extra = sorted(artifact.keys() - VERDICT_KEYS)
    if missing:
        raise ContractError(f"verdict.v2 missing required fields: {', '.join(missing)}")
    if extra:
        raise ContractError(f"verdict.v2 contains unknown fields: {', '.join(extra)}")
    if artifact["schema_version"] != "verdict.v2":
        raise ContractError("verdict.v2 schema_version must be verdict.v2")
    for field in ("acceptance_digest", "subject_manifest_digest", "artifact_digest"):
        if not valid_digest(artifact[field]):
            raise ContractError(f"verdict.v2 {field} must be a lowercase SHA-256 digest")
    expected_digest = digest_value({key: value for key, value in artifact.items() if key != "artifact_digest"})
    if artifact["artifact_digest"] != expected_digest:
        raise ContractError("verdict.v2 artifact_digest does not match canonical JSON")
    for field in ("author_context_id", "validator_context_id"):
        if artifact[field] is not None and (not isinstance(artifact[field], str) or not artifact[field]):
            raise ContractError(f"verdict.v2 {field} must be null or a nonempty string")
    freshness = artifact["freshness_attestation"]
    if freshness is not None:
        if not isinstance(freshness, dict) or set(freshness) != {"source", "attester_identity"}:
            raise ContractError("verdict.v2 freshness_attestation has invalid fields")
        if freshness["source"] not in {"runtime", "caller"}:
            raise ContractError("verdict.v2 freshness source must be runtime or caller")
        if not isinstance(freshness["attester_identity"], str) or not freshness["attester_identity"]:
            raise ContractError("verdict.v2 freshness attester_identity must be nonempty")
    if artifact["verdict"] not in {"PASS", "FAIL", "NOT_PROVEN"}:
        raise ContractError("verdict.v2 verdict must be PASS, FAIL, or NOT_PROVEN")
    criteria = artifact["criteria"]
    if not isinstance(criteria, list) or not criteria:
        raise ContractError("verdict.v2 criteria must be a nonempty array")
    for index, criterion in enumerate(criteria):
        allowed = {"id", "result", "evidence_refs", "reason"}
        if not isinstance(criterion, dict) or not {"id", "result", "evidence_refs"}.issubset(criterion) or not set(criterion).issubset(allowed):
            raise ContractError(f"verdict.v2 criteria[{index}] has invalid fields")
        if not isinstance(criterion["id"], str) or not criterion["id"]:
            raise ContractError(f"verdict.v2 criteria[{index}].id must be nonempty")
        if criterion["result"] not in {"PASS", "FAIL", "NOT_PROVEN"}:
            raise ContractError(f"verdict.v2 criteria[{index}].result is invalid")
        require_string_list(criterion["evidence_refs"], f"criteria[{index}].evidence_refs")
        if "reason" in criterion and not isinstance(criterion["reason"], str):
            raise ContractError(f"verdict.v2 criteria[{index}].reason must be a string")
    findings = artifact["findings"]
    if not isinstance(findings, list):
        raise ContractError("verdict.v2 findings must be an array")
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict) or set(finding) != {"id", "summary", "evidence_refs"}:
            raise ContractError(f"verdict.v2 findings[{index}] has invalid fields")
        if not isinstance(finding["id"], str) or not finding["id"]:
            raise ContractError(f"verdict.v2 findings[{index}].id must be nonempty")
        if not isinstance(finding["summary"], str) or not finding["summary"]:
            raise ContractError(f"verdict.v2 findings[{index}].summary must be nonempty")
        require_string_list(finding["evidence_refs"], f"findings[{index}].evidence_refs", nonempty=True)
    for field in ("evidence_refs", "checked", "not_checked"):
        require_string_list(artifact[field], field)
    if not isinstance(artifact["validated_at"], str):
        raise ContractError("verdict.v2 validated_at must be an RFC3339 date-time")
    try:
        timestamp = datetime.fromisoformat(artifact["validated_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("verdict.v2 validated_at must be an RFC3339 date-time") from exc
    if timestamp.tzinfo is None:
        raise ContractError("verdict.v2 validated_at must include a timezone")
    if artifact["verdict"] == "PASS":
        author = artifact["author_context_id"]
        validator = artifact["validator_context_id"]
        if not author or not validator or author == validator or freshness is None:
            raise ContractError("verdict.v2 PASS requires distinct identities and freshness attestation")
        if any(criterion["result"] != "PASS" for criterion in criteria):
            raise ContractError("verdict.v2 PASS requires every criterion to PASS")
        if any(not criterion["evidence_refs"] for criterion in criteria) or not artifact["evidence_refs"] or not artifact["checked"]:
            raise ContractError("verdict.v2 PASS requires criterion evidence plus nonempty evidence_refs and checked")
        if artifact["not_checked"]:
            raise ContractError("verdict.v2 PASS cannot contain not_checked items")


def artifact_bytes(draft: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    unsigned = {key: value for key, value in draft.items() if key != "artifact_digest"}
    digest = digest_value(unsigned)
    artifact = dict(unsigned)
    artifact["artifact_digest"] = digest
    return artifact, canonical_bytes(artifact) + b"\n"


def atomic_store(artifact: dict[str, Any], payload: bytes, destination: Path) -> tuple[Path, bool]:
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"{artifact['artifact_digest']}.json"
    if target.exists():
        if target.read_bytes() == payload:
            return target, True
        raise ContractError(f"integrity collision at {target}")
    fd, temporary = tempfile.mkstemp(prefix=".verdict-", suffix=".tmp", dir=destination)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        dir_fd = os.open(destination, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target, False


def snapshot_intent(payload: bytes, destination: Path) -> tuple[Path, bool]:
    """Persist exact resolved intent bytes under their SHA-256 identity."""
    destination.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(payload).hexdigest()
    target = destination / f"{digest}.intent"
    if target.exists():
        if target.read_bytes() == payload:
            return target, True
        raise ContractError(f"intent snapshot integrity collision at {target}")
    fd, temporary = tempfile.mkstemp(prefix=".intent-", suffix=".tmp", dir=destination)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        dir_fd = os.open(destination, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return target, False


def store_verdict(
    draft: dict[str, Any],
    destination: Path,
    intent_bytes: bytes | None = None,
    manifest: dict[str, Any] | None = None,
    author_context_id: str | None = None,
    scope_status: str | None = None,
) -> tuple[dict[str, Any], Path, bool]:
    draft = bind_runtime_facts(draft, intent_bytes, manifest, author_context_id, scope_status)
    draft = enforce_identity(draft)
    draft["schema_version"] = "verdict.v2"
    artifact, payload = artifact_bytes(draft)
    validate_verdict_v2(artifact)
    try:
        path, existed = atomic_store(artifact, payload, destination)
    except ContractError as exc:
        artifact, payload = artifact_bytes(add_integrity_finding(draft, str(exc)))
        validate_verdict_v2(artifact)
        path, existed = atomic_store(artifact, payload, destination)
    return artifact, path, existed


def write_json(value: dict[str, Any], output: str | None) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    manifest = sub.add_parser("manifest", help="compute subject-manifest.v1 without Git")
    manifest.add_argument("--root", required=True)
    manifest.add_argument("--include", action="append", required=True)
    manifest.add_argument("--exclude", action="append", default=[])
    manifest.add_argument("--base-manifest")
    manifest.add_argument("--git-metadata-json")
    manifest.add_argument("--output")
    verify = sub.add_parser("verify-manifest", help="recompute and compare a manifest")
    verify.add_argument("--root", required=True)
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--base-manifest")
    snapshot = sub.add_parser("snapshot-intent", help="persist exact intent bytes under their SHA-256 identity")
    snapshot.add_argument("--source", required=True, help="intent file path, or - for stdin")
    snapshot.add_argument("--workspace", default=".")
    snapshot.add_argument("--intent-dir")
    digest = sub.add_parser("digest", help="print a canonical JSON digest")
    digest.add_argument("json_file")
    store = sub.add_parser("store-verdict", help="atomically persist verdict.v2")
    store.add_argument("--draft", required=True)
    store.add_argument("--intent-source", required=True)
    store.add_argument("--subject-manifest", required=True)
    store.add_argument("--author-context-id", required=True)
    store.add_argument("--scope-result", required=True, choices=("PASS", "FAIL", "NOT_PROVEN"))
    store.add_argument("--workspace", default=".")
    store.add_argument("--verdict-dir")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "manifest":
            base = load_json(Path(args.base_manifest)) if args.base_manifest else None
            metadata = json.loads(args.git_metadata_json) if args.git_metadata_json else None
            write_json(build_manifest(Path(args.root), args.include, args.exclude, base, metadata), args.output)
        elif args.command == "verify-manifest":
            manifest = load_json(Path(args.manifest))
            base = load_json(Path(args.base_manifest)) if args.base_manifest else None
            ok, reason = verify_manifest(manifest, Path(args.root), base)
            write_json({"result": "PASS" if ok else "NOT_PROVEN", "reason": reason}, None)
            return 0 if ok else 1
        elif args.command == "snapshot-intent":
            intent_bytes = sys.stdin.buffer.read() if args.source == "-" else Path(args.source).read_bytes()
            destination = Path(args.intent_dir) if args.intent_dir else Path(args.workspace) / ".agents" / "ao" / "intents" / "sha256"
            intent_path, existed = snapshot_intent(intent_bytes, destination)
            write_json({
                "acceptance_digest": hashlib.sha256(intent_bytes).hexdigest(),
                "idempotent": existed,
                "intent_ref": str(intent_path),
            }, None)
        elif args.command == "digest":
            print(digest_value(load_json(Path(args.json_file))))
        elif args.command == "store-verdict":
            destination = Path(args.verdict_dir) if args.verdict_dir else Path(args.workspace) / ".agents" / "ao" / "verdicts" / "sha256"
            intent_bytes = Path(args.intent_source).read_bytes()
            intent_path, intent_existed = snapshot_intent(
                intent_bytes,
                Path(args.workspace) / ".agents" / "ao" / "intents" / "sha256",
            )
            artifact, path, existed = store_verdict(
                load_json(Path(args.draft)),
                destination,
                intent_bytes,
                load_json(Path(args.subject_manifest)),
                args.author_context_id,
                args.scope_result,
            )
            write_json({
                "acceptance_digest": hashlib.sha256(intent_bytes).hexdigest(),
                "artifact_digest": artifact["artifact_digest"],
                "idempotent": existed,
                "intent_ref": str(intent_path),
                "intent_snapshot_idempotent": intent_existed,
                "path": str(path),
                "verdict": artifact["verdict"],
            }, None)
        return 0
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"validate: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
