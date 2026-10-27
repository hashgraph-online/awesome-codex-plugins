#!/usr/bin/env python3
"""Check FluidSim restart metadata against a validated target configuration."""

from __future__ import annotations

import argparse
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

try:
    from ._common import (
        GIB,
        ToolError,
        bounded_int,
        checked_input,
        checked_root,
        emit_json,
        fail_json,
        iter_local_files,
        load_json,
        relative_display,
        sha256_file,
        validate_keys,
    )
    from ._schema import FLUIDSIM_VERSION, SOLVER_IMPORTS, normalized_copy
except ImportError:  # Direct script execution.
    from _common import (
        GIB,
        ToolError,
        bounded_int,
        checked_input,
        checked_root,
        emit_json,
        fail_json,
        iter_local_files,
        load_json,
        relative_display,
        sha256_file,
        validate_keys,
    )
    from _schema import FLUIDSIM_VERSION, SOLVER_IMPORTS, normalized_copy


TOOL = "fluidsim-restart-compatibility"
_MODULE_TO_SOLVER = {module: key for key, module in SOLVER_IMPORTS.items()}
_STATE_SUFFIXES = (".nc", ".h5", ".hdf5")
_COMPATIBLE_OPER_KEYS = ("nx", "ny", "nz", "Lx", "Ly", "Lz")
_PHYSICS_KEYS = ("N", "beta", "c2", "f", "nu_2", "nu_4", "nu_8", "nu_m4")


def _safe_scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (TypeError, ValueError):
            return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[:500]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value if not isinstance(value, str) else value[:500]
    return None


def _attrs(group: Any, names: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in names:
        if name not in group.attrs:
            continue
        identifier = group.attrs.get_id(name)
        if identifier.shape != ():
            continue
        value = _safe_scalar(group.attrs[name])
        if value is not None:
            result[name] = value
    return result


def _find_state_file(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = [
        item
        for item in iter_local_files(
            path, suffixes=_STATE_SUFFIXES, max_files=10_000, recursive=True
        )
        if item.name.casefold().startswith("state_phys")
    ]
    if not candidates:
        raise ToolError("no state_phys .nc/.h5 file found in restart directory")
    return sorted(candidates, key=lambda item: item.name)[-1]


def load_hdf5_state(path: Path, *, digest_limit: int) -> dict[str, Any]:
    """Read restart metadata and dataset names without reading field arrays."""

    try:
        import h5py  # Lazy optional dependency.
    except ImportError as exc:
        raise ToolError(
            "restart HDF5 inspection requires optional h5py from the pinned environment"
        ) from exc

    try:
        with h5py.File(path, "r") as handle:
            if "state_phys" not in handle or not isinstance(
                handle["state_phys"], h5py.Group
            ):
                raise ToolError("restart file has no /state_phys group")
            state_group = handle["state_phys"]
            state = {
                "datasets": sorted(
                    name
                    for name in state_group
                    if isinstance(state_group.get(name, getlink=False), h5py.Dataset)
                ),
                "iteration": _attrs(state_group, ("it",)).get("it"),
                "state_parameters_present": any(
                    name in handle
                    for name in ("state_params", "info_state", "state_parameters")
                ),
                "time": _attrs(state_group, ("time",)).get("time"),
            }
            parameters: dict[str, Any] = {}
            solver = None
            source_version = None
            if "info_simul" in handle:
                info = handle["info_simul"]
                if "params" in info:
                    params_group = info["params"]
                    parameters.update(_attrs(params_group, _PHYSICS_KEYS))
                    for child, keys in (
                        ("oper", _COMPATIBLE_OPER_KEYS + ("coef_dealiasing", "type_fft")),
                        (
                            "time_stepping",
                            ("t_end", "it_end", "type_time_scheme"),
                        ),
                        ("forcing", ("enable", "type", "forcing_rate")),
                    ):
                        if child in params_group:
                            parameters[child] = _attrs(params_group[child], keys)
                if "solver" in info:
                    solver_attrs = _attrs(
                        info["solver"],
                        ("module_name", "short_name", "version", "fluidsim"),
                    )
                    module_name = solver_attrs.get("module_name")
                    solver = _MODULE_TO_SOLVER.get(str(module_name), None)
                    source_version = solver_attrs.get(
                        "fluidsim", solver_attrs.get("version")
                    )
            # FluidSim 0.9 stores forcing state parameters in restart files. Their
            # exact group path can vary with extensions, so inspect object names only.
            names: list[str] = []
            handle.visit(names.append)
            state["state_parameters_present"] = state[
                "state_parameters_present"
            ] or any("state_params" in name for name in names)
    except OSError as exc:
        raise ToolError("restart file is not readable HDF5/netCDF4") from exc

    return {
        "parameters": parameters,
        "provenance": {
            "fluidfft": None,
            "fluidsim": source_version,
            "state_sha256": sha256_file(path, max_bytes=digest_limit),
        },
        "solver": solver,
        "state": state,
    }


def load_manifest(path: Path) -> dict[str, Any]:
    document = load_json(path)
    if not isinstance(document, Mapping):
        raise ToolError("restart manifest must be a JSON object")
    validate_keys(
        document,
        allowed={"schema_version", "solver", "parameters", "state", "provenance"},
        required={"schema_version", "solver", "parameters", "state", "provenance"},
        context="restart manifest",
    )
    if document["schema_version"] != "1.1":
        raise ToolError("restart manifest schema_version must be '1.1'")
    if document["solver"] not in SOLVER_IMPORTS:
        raise ToolError("restart manifest solver is unknown")
    parameters = document["parameters"]
    state = document["state"]
    provenance = document["provenance"]
    if not all(isinstance(item, Mapping) for item in (parameters, state, provenance)):
        raise ToolError("restart manifest parameters/state/provenance must be objects")
    validate_keys(
        state,
        allowed={"datasets", "iteration", "state_parameters_present", "time"},
        required={"datasets", "iteration", "state_parameters_present", "time"},
        context="restart manifest state",
    )
    validate_keys(
        provenance,
        allowed={"fluidfft", "fluidsim", "state_sha256"},
        required={"fluidfft", "fluidsim", "state_sha256"},
        context="restart manifest provenance",
    )
    if not isinstance(state["datasets"], list) or not all(
        isinstance(item, str) and 0 < len(item) <= 128 for item in state["datasets"]
    ):
        raise ToolError("restart manifest datasets must be bounded strings")
    digest = provenance["state_sha256"]
    if digest is not None and not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
        raise ToolError("restart manifest state_sha256 must be lowercase SHA-256")
    return {
        "parameters": dict(parameters),
        "provenance": dict(provenance),
        "solver": document["solver"],
        "state": dict(state),
    }


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        scale = max(1.0, abs(float(left)), abs(float(right)))
        return abs(float(left) - float(right)) <= 1e-12 * scale
    return left == right


def compare(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def add(target_list: list[dict[str, str]], code: str, message: str) -> None:
        target_list.append({"code": code, "message": message})

    if source.get("solver") is None:
        add(blockers, "missing_solver", "source solver metadata is unavailable")
    elif source["solver"] != target["solver"]:
        add(blockers, "solver_mismatch", "source and target solver keys differ")

    source_params = source.get("parameters", {})
    target_params = target["parameters"]
    source_oper = source_params.get("oper", {})
    target_oper = target_params.get("oper", {})
    for key in _COMPATIBLE_OPER_KEYS:
        if key not in target_oper:
            continue
        if key not in source_oper:
            add(warnings, "missing_grid_metadata", f"source oper.{key} is unavailable")
        elif not _same(source_oper[key], target_oper[key]):
            add(
                blockers,
                "grid_or_domain_mismatch",
                f"oper.{key} differs; use the reviewed resolution-change workflow",
            )
    for key in ("coef_dealiasing", "type_fft"):
        if key in source_oper and key in target_oper and not _same(
            source_oper[key], target_oper[key]
        ):
            add(
                warnings,
                "operator_change",
                f"oper.{key} changes across restart and requires justification",
            )

    for key in _PHYSICS_KEYS:
        if key in source_params and key in target_params and not _same(
            source_params[key], target_params[key]
        ):
            add(
                warnings,
                "physics_parameter_change",
                f"{key} changes across restart; reassess equations and budgets",
            )

    source_state = source.get("state", {})
    if not source_state.get("datasets"):
        add(blockers, "empty_state", "source contains no state datasets")
    source_time = source_state.get("time")
    target_end = target_params["time_stepping"].get("t_end")
    if isinstance(source_time, (int, float)) and isinstance(target_end, (int, float)):
        if float(target_end) <= float(source_time):
            add(blockers, "nonadvancing_end_time", "target t_end does not exceed state time")
    else:
        add(warnings, "missing_time", "source time or target t_end is unavailable")

    init = target_params.get("init_fields", {})
    if init.get("type") != "from_file":
        add(
            blockers,
            "target_not_from_file",
            "target init_fields.type must be 'from_file' for this restart plan",
        )

    source_provenance = source.get("provenance", {})
    source_version = source_provenance.get("fluidsim")
    if source_version is None:
        add(
            warnings,
            "missing_source_version",
            "source FluidSim version is unavailable; do not assume migration compatibility",
        )
    elif source_version != FLUIDSIM_VERSION:
        add(
            warnings,
            "version_migration",
            "source version differs from 0.9.0; review release notes and merge_missing_params",
        )

    target_restart = target["provenance"].get("restart")
    if not isinstance(target_restart, Mapping):
        add(blockers, "missing_restart_provenance", "target provenance.restart is required")
    else:
        expected_digest = target_restart.get("sha256")
        observed_digest = source_provenance.get("state_sha256")
        if observed_digest is None:
            add(
                blockers,
                "digest_not_checked",
                "source state exceeded the hash bound or lacks a manifest digest",
            )
        elif expected_digest != observed_digest:
            add(blockers, "digest_mismatch", "restart SHA-256 does not match target provenance")

    forcing = target_params.get("forcing", {})
    if (
        forcing.get("enable")
        and forcing.get("type") == "tcrandom"
        and not source_state.get("state_parameters_present")
    ):
        add(
            blockers,
            "forcing_state_missing",
            "time-correlated forcing restart lacks saved state parameters",
        )

    return {
        "blockers": blockers,
        "compatible_for_mechanical_restart": not blockers,
        "numerical_convergence_established": False,
        "ok": not blockers,
        "physical_validity_established": False,
        "source": {
            "dataset_count": len(source_state.get("datasets", [])),
            "fluidfft": source_provenance.get("fluidfft"),
            "fluidsim": source_version,
            "iteration": source_state.get("iteration"),
            "sha256_checked": source_provenance.get("state_sha256") is not None,
            "solver": source.get("solver"),
            "state_parameters_present": source_state.get(
                "state_parameters_present"
            ),
            "time": source_time,
        },
        "target": {
            "fluidfft": target["provenance"]["fluidfft"],
            "fluidsim": target["provenance"]["fluidsim"],
            "solver": target["solver"],
            "t_end": target_end,
        },
        "tool": TOOL,
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare local restart metadata with validated target JSON. Field arrays "
            "are never loaded; no restart, MPI launch, or job submission occurs."
        )
    )
    parser.add_argument("--source", required=True, help="State file, run directory, or manifest.")
    parser.add_argument("--target-config", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--hash-max-gib",
        type=int,
        default=1,
        help="Hash source state only up to this many GiB, 0..8 (default: 1).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        hash_gib = bounded_int(
            args.hash_max_gib, name="hash_max_gib", minimum=0, maximum=8
        )
        root = checked_root(args.root)
        source_path = checked_input(args.source, root=root, kind="any")
        target_path = checked_input(
            args.target_config,
            root=root,
            kind="file",
            suffixes={".json"},
        )
        target = normalized_copy(load_json(target_path))
        if source_path.is_file() and source_path.name.casefold().endswith(".json"):
            source = load_manifest(source_path)
            selected = source_path
        else:
            selected = _find_state_file(source_path)
            source = load_hdf5_state(
                selected,
                digest_limit=hash_gib * GIB,
            )
        report = compare(source, target)
        report.update(
            {
                "arrays_loaded": False,
                "commands_executed": False,
                "network_used": False,
                "selected_source": relative_display(selected, root),
            }
        )
        emit_json(report)
        return 0 if report["ok"] else 2
    except (OSError, ToolError, UnicodeError) as exc:
        return fail_json(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
