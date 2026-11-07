#!/usr/bin/env python3
"""Validate or deterministically diff resource snapshots."""

from __future__ import annotations

import argparse
import copy
from typing import Any, Mapping, Sequence

from _common import (
    MAX_BYTES,
    SCHEMA_VERSION,
    ResourceToolError,
    bounded_number,
    cli_error,
    emit_json,
    read_json_file,
)

MAX_DIFFS = 512
_PATH_CPU = "$.cpu"
_PATH_MEMORY = "$.memory"


def _is_optional_nonnegative_number(value: Any) -> bool:
    """Return whether optional nonnegative number."""
    return value is None or bounded_number(value, maximum=float(MAX_BYTES)) is not None


def _expect_mapping(
    parent: Mapping[str, Any],
    key: str,
    path: str,
    errors: list[dict[str, str]],
) -> Mapping[str, Any]:
    """Handle expect mapping."""
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(
            {
                "code": "TYPE",
                "message": "must be an object",
                "path": f"{path}.{key}",
            }
        )
        return {}
    return value


def _check_optional_number(
    parent: Mapping[str, Any],
    key: str,
    path: str,
    errors: list[dict[str, str]],
) -> None:
    """Check optional number."""
    if not _is_optional_nonnegative_number(parent.get(key)):
        errors.append(
            {
                "code": "NUMBER",
                "message": "must be null or a finite nonnegative bounded number",
                "path": f"{path}.{key}",
            }
        )


def _issue(code: str, message: str, path: str) -> dict[str, str]:
    """Build a validation issue record."""
    return {"code": code, "message": message, "path": path}


def _is_number(value: Any) -> bool:
    """Return whether ``value`` is an int or float that is not a bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_header(snapshot: Mapping[str, Any], errors: list[dict[str, str]]) -> None:
    """Validate schema version, snapshot kind, timestamp and platform fields."""
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            _issue("SCHEMA_VERSION", f"must equal {SCHEMA_VERSION}", "$.schema_version")
        )
    if snapshot.get("snapshot_kind") != "effective_resource_snapshot":
        errors.append(
            _issue(
                "SNAPSHOT_KIND",
                "must equal effective_resource_snapshot",
                "$.snapshot_kind",
            )
        )
    observed_at = snapshot.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at.endswith("Z"):
        errors.append(
            _issue("TIMESTAMP", "must be a UTC string ending in Z", "$.observed_at")
        )

    platform = _expect_mapping(snapshot, "platform", "$", errors)
    for key in ("system", "machine", "python_version"):
        if not isinstance(platform.get(key), str) or not platform.get(key):
            errors.append(
                _issue("PLATFORM", "must be a nonempty string", f"$.platform.{key}")
            )


def _validate_cpu(snapshot: Mapping[str, Any], errors: list[dict[str, str]]) -> None:
    """Validate the cpu section of a snapshot."""
    cpu = _expect_mapping(snapshot, "cpu", "$", errors)
    host_cpu = _expect_mapping(cpu, "host", _PATH_CPU, errors)
    process_cpu = _expect_mapping(cpu, "process", _PATH_CPU, errors)
    cpu_cgroup = _expect_mapping(cpu, "cgroup_v2", _PATH_CPU, errors)
    effective_cpu = _expect_mapping(cpu, "effective", _PATH_CPU, errors)
    for key in ("logical", "physical"):
        _check_optional_number(host_cpu, key, "$.cpu.host", errors)
    for key in ("affinity_logical", "python_available_logical"):
        _check_optional_number(process_cpu, key, "$.cpu.process", errors)
    for key in ("cpuset_logical", "quota_cores"):
        _check_optional_number(cpu_cgroup, key, "$.cpu.cgroup_v2", errors)
    _check_optional_number(
        effective_cpu, "capacity_cores", "$.cpu.effective", errors
    )
    worker_ceiling = effective_cpu.get("worker_ceiling")
    if (
        isinstance(worker_ceiling, bool)
        or not isinstance(worker_ceiling, int)
        or not 1 <= worker_ceiling <= 1024
    ):
        errors.append(
            _issue(
                "WORKER_CEILING",
                "must be an integer between 1 and 1024",
                "$.cpu.effective.worker_ceiling",
            )
        )
    if not isinstance(effective_cpu.get("limiting_sources"), list):
        errors.append(
            _issue("LIMIT_SOURCES", "must be an array", "$.cpu.effective.limiting_sources")
        )


def _validate_memory(snapshot: Mapping[str, Any], errors: list[dict[str, str]]) -> None:
    """Validate the memory section of a snapshot."""
    memory = _expect_mapping(snapshot, "memory", "$", errors)
    host_memory = _expect_mapping(memory, "host", _PATH_MEMORY, errors)
    effective_memory = _expect_mapping(memory, "effective", _PATH_MEMORY, errors)
    memory_cgroup = _expect_mapping(memory, "cgroup_v2", _PATH_MEMORY, errors)
    swap = _expect_mapping(memory, "swap", _PATH_MEMORY, errors)
    for key in ("available_bytes", "total_bytes"):
        _check_optional_number(host_memory, key, "$.memory.host", errors)
    for key in (
        "available_bytes",
        "hard_limit_bytes",
        "pressure_threshold_bytes",
    ):
        _check_optional_number(effective_memory, key, "$.memory.effective", errors)
    for key in ("available_bytes", "current_bytes", "high_bytes", "max_bytes"):
        _check_optional_number(memory_cgroup, key, "$.memory.cgroup_v2", errors)
    for key in ("free_bytes", "total_bytes"):
        _check_optional_number(swap, key, "$.memory.swap", errors)
    available = effective_memory.get("available_bytes")
    hard_limit = effective_memory.get("hard_limit_bytes")
    if _is_number(available) and _is_number(hard_limit) and available > hard_limit:
        errors.append(
            _issue(
                "MEMORY_ORDER",
                "available memory cannot exceed the effective hard limit",
                "$.memory.effective.available_bytes",
            )
        )


def _validate_disk(snapshot: Mapping[str, Any], errors: list[dict[str, str]]) -> None:
    """Validate the disk section of a snapshot."""
    disk = _expect_mapping(snapshot, "disk", "$", errors)
    for key in ("capacity_bytes", "free_bytes", "user_available_bytes"):
        _check_optional_number(disk, key, "$.disk", errors)
    if disk.get("writable") is not None and not isinstance(
        disk.get("writable"), bool
    ):
        errors.append(_issue("DISK_WRITABLE", "must be boolean or null", "$.disk.writable"))
    free = disk.get("free_bytes")
    user_available = disk.get("user_available_bytes")
    capacity = disk.get("capacity_bytes")
    all_numbers = all(_is_number(value) for value in (free, user_available, capacity))
    if all_numbers and not 0 <= user_available <= free <= capacity:
        errors.append(
            _issue(
                "DISK_ORDER",
                "expected user_available <= free <= capacity",
                "$.disk",
            )
        )


def _validate_device(
    index: int,
    device: Any,
    errors: list[dict[str, str]],
    notes: list[dict[str, str]],
) -> None:
    """Validate one accelerator device entry, recording errors and assertion notes."""
    device_path = f"$.accelerators.devices[{index}]"
    if not isinstance(device, dict):
        errors.append(_issue("ACCELERATOR_DEVICE", "must be an object", device_path))
        return
    if device.get("backend_candidate") not in {"cuda", "metal", "rocm"}:
        errors.append(
            _issue(
                "ACCELERATOR_BACKEND",
                "must be cuda, metal, or rocm",
                f"{device_path}.backend_candidate",
            )
        )
    if device.get("device_permission") != "not_tested":
        notes.append(
            _issue(
                "PERMISSION_ASSERTION",
                "device permission differs from the detector's "
                "conservative not_tested default",
                f"{device_path}.device_permission",
            )
        )
    if device.get("runtime_compatibility") != "not_tested":
        notes.append(
            _issue(
                "RUNTIME_ASSERTION",
                "runtime compatibility differs from the detector's "
                "conservative not_tested default",
                f"{device_path}.runtime_compatibility",
            )
        )


def _validate_accelerators(
    snapshot: Mapping[str, Any],
    errors: list[dict[str, str]],
    notes: list[dict[str, str]],
) -> None:
    """Validate the accelerators section of a snapshot."""
    accelerators = _expect_mapping(snapshot, "accelerators", "$", errors)
    devices = accelerators.get("devices")
    if not isinstance(devices, list) or len(devices) > 256:
        errors.append(
            _issue(
                "ACCELERATOR_DEVICES",
                "must be an array with at most 256 entries",
                "$.accelerators.devices",
            )
        )
        return
    for index, device in enumerate(devices):
        _validate_device(index, device, errors, notes)


def _validate_scheduler_privacy(
    snapshot: Mapping[str, Any],
    errors: list[dict[str, str]],
    notes: list[dict[str, str]],
) -> None:
    """Validate the scheduler and privacy sections of a snapshot."""
    scheduler = _expect_mapping(snapshot, "scheduler", "$", errors)
    if not isinstance(scheduler.get("fields_read"), list):
        errors.append(
            _issue("SCHEDULER_FIELDS", "must be an array", "$.scheduler.fields_read")
        )
    privacy = _expect_mapping(snapshot, "privacy", "$", errors)
    for key in (
        "absolute_paths_included",
        "environment_values_included",
        "hostnames_included",
        "identifiers_redacted_by_default",
    ):
        if not isinstance(privacy.get(key), bool):
            errors.append(_issue("PRIVACY", "must be boolean", f"$.privacy.{key}"))
    if any(
        privacy.get(key) is True
        for key in (
            "absolute_paths_included",
            "environment_values_included",
            "hostnames_included",
        )
    ):
        notes.append(
            _issue(
                "PRIVACY_EXPANDED",
                "snapshot includes fields normally redacted",
                "$.privacy",
            )
        )


def _validate_bounded_lists(
    snapshot: Mapping[str, Any], errors: list[dict[str, str]]
) -> None:
    """Validate that the warnings and provenance arrays exist and stay bounded."""
    for key, code in (("warnings", "WARNINGS"), ("provenance", "PROVENANCE")):
        items = snapshot.get(key)
        if not isinstance(items, list) or len(items) > 512:
            errors.append(
                _issue(code, "must be an array with at most 512 entries", f"$.{key}")
            )


def validate_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the stable 1.1 resource snapshot contract."""
    errors: list[dict[str, str]] = []
    notes: list[dict[str, str]] = []
    _validate_header(snapshot, errors)
    _validate_cpu(snapshot, errors)
    _validate_memory(snapshot, errors)
    _validate_disk(snapshot, errors)
    _validate_accelerators(snapshot, errors, notes)
    _validate_scheduler_privacy(snapshot, errors, notes)
    _validate_bounded_lists(snapshot, errors)

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    notes.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    return {
        "errors": errors,
        "kind": "snapshot_validation",
        "notes": notes,
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
    }


def _strip_volatile(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Handle strip volatile."""
    cleaned = copy.deepcopy(dict(snapshot))
    cleaned.pop("observed_at", None)
    return cleaned


def _diff_values(
    before: Any,
    after: Any,
    path: str,
    changes: list[dict[str, Any]],
) -> None:
    """Handle diff values."""
    if len(changes) >= MAX_DIFFS:
        return
    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            child_path = f"{path}.{key}"
            if key not in before:
                changes.append(
                    {
                        "after": after[key],
                        "before": None,
                        "change": "added",
                        "path": child_path,
                    }
                )
            elif key not in after:
                changes.append(
                    {
                        "after": None,
                        "before": before[key],
                        "change": "removed",
                        "path": child_path,
                    }
                )
            else:
                _diff_values(before[key], after[key], child_path, changes)
            if len(changes) >= MAX_DIFFS:
                return
        return
    if isinstance(before, list) and isinstance(after, list):
        maximum = max(len(before), len(after))
        for index in range(maximum):
            child_path = f"{path}[{index}]"
            if index >= len(before):
                changes.append(
                    {
                        "after": after[index],
                        "before": None,
                        "change": "added",
                        "path": child_path,
                    }
                )
            elif index >= len(after):
                changes.append(
                    {
                        "after": None,
                        "before": before[index],
                        "change": "removed",
                        "path": child_path,
                    }
                )
            else:
                _diff_values(before[index], after[index], child_path, changes)
            if len(changes) >= MAX_DIFFS:
                return
        return
    if before != after:
        changes.append(
            {
                "after": after,
                "before": before,
                "change": "changed",
                "path": path,
            }
        )


def diff_snapshots(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    include_volatile: bool = False,
) -> dict[str, Any]:
    """Return a bounded, stable structural diff."""
    before_validation = validate_snapshot(before)
    after_validation = validate_snapshot(after)
    if not before_validation["valid"] or not after_validation["valid"]:
        raise ResourceToolError("both snapshots must validate before diffing")
    try:
        left = dict(before) if include_volatile else _strip_volatile(before)
        right = dict(after) if include_volatile else _strip_volatile(after)
        changes: list[dict[str, Any]] = []
        _diff_values(left, right, "$", changes)
    except RecursionError as exc:
        raise ResourceToolError("snapshot nesting exceeds the diff safety bound") from exc
    return {
        "change_count": len(changes),
        "changes": changes,
        "ignored_paths": [] if include_volatile else ["$.observed_at"],
        "kind": "snapshot_diff",
        "schema_version": SCHEMA_VERSION,
        "truncated": len(changes) >= MAX_DIFFS,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description="Validate or structurally diff resource snapshot JSON"
    )
    parser.add_argument(
        "--output",
        metavar="FILE.json",
        help="write a private local JSON file instead of stdout",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing explicit output file",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one snapshot")
    validate.add_argument("snapshot", help="snapshot JSON file")
    diff = commands.add_parser("diff", help="diff two valid snapshots")
    diff.add_argument("before", help="earlier snapshot JSON file")
    diff.add_argument("after", help="later snapshot JSON file")
    diff.add_argument(
        "--include-volatile",
        action="store_true",
        help="include observed_at in the diff",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.force and not args.output:
        parser.error("--force requires --output")
    try:
        if args.command == "validate":
            report = validate_snapshot(read_json_file(args.snapshot))
            emit_json(report, args.output, force=args.force)
            return 0 if report["valid"] else 1
        report = diff_snapshots(
            read_json_file(args.before),
            read_json_file(args.after),
            include_volatile=args.include_volatile,
        )
        emit_json(report, args.output, force=args.force)
        return 0
    except ResourceToolError as exc:
        return cli_error(parser, exc)


if __name__ == "__main__":
    raise SystemExit(main())
