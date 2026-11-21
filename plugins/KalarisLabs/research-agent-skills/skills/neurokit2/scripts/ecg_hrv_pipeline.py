#!/usr/bin/env python3
"""Run a bounded ECG processing and duration-aware HRV workflow."""

from __future__ import annotations

import argparse
from typing import Any

from _common import (
    MAX_CSV_BYTES,
    MAX_ROWS,
    CliError,
    add_pipeline_arguments,
    checked_input_file,
    emit_pipeline_report,
    finite_float,
    json_number,
    parse_name_list,
    read_numeric_columns,
    require_deidentified,
    require_pinned_neurokit2,
    run_cli,
)

ECG_METHODS = (
    "neurokit",
    "pantompkins1985",
    "hamilton2002",
    "elgendi2010",
    "engzeemod2012",
)
HRV_DOMAINS = {"time", "frequency", "nonlinear"}
HRV_ERRORS = (TypeError, ValueError, RuntimeError, ZeroDivisionError)
HRV_LABELS = {
    "time": "time-domain HRV",
    "frequency": "frequency-domain HRV",
    "nonlinear": "nonlinear HRV",
}


def _row_to_json(frame: Any) -> dict[str, float | int | None]:
    """Handle row to json."""
    if len(frame) != 1:
        raise CliError("expected one-row HRV output")
    return {str(column): json_number(frame.iloc[0][column]) for column in frame.columns}


def _summary(values: Any) -> dict[str, float | int | None]:
    """Handle summary."""
    finite = values[values.notna()] if hasattr(values, "notna") else values
    if len(finite) == 0:
        return {"count": 0, "maximum": None, "mean": None, "minimum": None}
    return {
        "count": len(finite),
        "maximum": json_number(finite.max()),
        "mean": json_number(finite.mean()),
        "minimum": json_number(finite.min()),
    }


def _artifact_counts(info: dict[str, Any]) -> dict[str, int]:
    """Handle artifact counts."""
    result: dict[str, int] = {}
    for name in ("ectopic", "missed", "extra", "longshort"):
        value = info.get(f"ECG_fixpeaks_{name}", [])
        try:
            result[name] = len(value)
        except TypeError:
            result[name] = 0
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Process a bounded deidentified ECG CSV or a reproducible synthetic "
            "signal with NeuroKit2 0.2.13, report peak correction and quality, "
            "and gate HRV domains by duration and beat count."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="local .csv input")
    source.add_argument("--synthetic", action="store_true")
    parser.add_argument("--column", default="ECG")
    parser.add_argument("--sampling-rate", type=float, required=True, help="Hz")
    parser.add_argument("--method", choices=ECG_METHODS, default="neurokit")
    parser.add_argument(
        "--domains",
        default="time",
        help="comma-separated subset of time,frequency,nonlinear",
    )
    parser.add_argument(
        "--duration", type=float, default=60.0, help="synthetic seconds"
    )
    parser.add_argument("--heart-rate", type=float, default=70.0, help="synthetic BPM")
    add_pipeline_arguments(parser)
    return parser


def _check_options(args: argparse.Namespace) -> tuple[float, set[str]]:
    """Validate the numeric and domain options; return the sampling rate and domains."""
    sampling_rate = finite_float(
        args.sampling_rate,
        name="--sampling-rate",
        minimum=20.0,
        maximum=20_000.0,
    )
    domains = set(parse_name_list(args.domains, name="--domains"))
    unknown = sorted(domains - HRV_DOMAINS)
    if unknown:
        raise CliError(f"unknown HRV domains: {', '.join(unknown)}")
    if not domains:
        raise CliError("select at least one HRV domain")
    if not 1 <= args.max_rows <= MAX_ROWS:
        raise CliError(f"--max-rows must be between 1 and {MAX_ROWS}")
    if not -(2**31) <= args.seed < 2**31:
        raise CliError("--seed must be a signed 32-bit integer")
    return sampling_rate, domains


def _synthetic_ecg(args: argparse.Namespace, nk: Any, sampling_rate: float) -> Any:
    """Generate the reproducible synthetic ECG requested on the command line."""
    duration = finite_float(
        args.duration,
        name="--duration",
        minimum=5.0,
        maximum=3600.0,
    )
    heart_rate = finite_float(
        args.heart_rate,
        name="--heart-rate",
        minimum=20.0,
        maximum=240.0,
    )
    if not sampling_rate.is_integer():
        raise CliError(
            "--sampling-rate must be an integer for NeuroKit2 synthetic ECG"
        )
    row_count = round(duration * sampling_rate)
    if not 1 <= row_count <= args.max_rows:
        raise CliError(f"synthetic row count must be between 1 and {args.max_rows}")
    try:
        return nk.ecg_simulate(
            duration=duration,
            sampling_rate=int(sampling_rate),
            heart_rate=heart_rate,
            random_state=args.seed,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        raise CliError(f"synthetic ECG generation failed: {exc}") from exc


def _load_ecg(
    args: argparse.Namespace, nk: Any, np: Any, sampling_rate: float
) -> tuple[Any, int, str]:
    """Load the ECG from a CSV or simulate it; return samples, row count and source."""
    if args.input:
        require_deidentified(args.deidentified)
        path = checked_input_file(
            args.input,
            root=args.root,
            suffixes={".csv"},
            max_bytes=MAX_CSV_BYTES,
        )
        selected, _, row_count = read_numeric_columns(
            path,
            [args.column],
            max_rows=args.max_rows,
        )
        return np.asarray(selected[args.column], dtype=float), row_count, "deidentified_local_csv"
    ecg = _synthetic_ecg(args, nk, sampling_rate)
    return ecg, len(ecg), "neurokit2_synthetic"


def _hrv_domain(
    nk: Any,
    name: str,
    info: dict[str, Any],
    sampling_rate: float,
    hrv: dict[str, dict[str, float | int | None]],
    warnings: list[str],
) -> None:
    """Compute one HRV domain, recording the result or a failure warning."""
    function = getattr(nk, f"hrv_{name}")
    try:
        hrv[name] = _row_to_json(function(info, sampling_rate=sampling_rate))
    except HRV_ERRORS as exc:
        warnings.append(f"{HRV_LABELS[name]} failed: {exc}")


def _time_domain(
    nk: Any, info: dict[str, Any], sampling_rate: float, duration_s: float,
    beat_count: int, hrv: dict[str, dict[str, float | int | None]], warnings: list[str],
) -> None:
    """Run time-domain HRV when enough beats were detected and note short recordings."""
    if beat_count < 20:
        warnings.append("time-domain HRV skipped: fewer than 20 detected beats")
    else:
        _hrv_domain(nk, "time", info, sampling_rate, hrv, warnings)
    if duration_s < 300:
        warnings.append(
            "time-domain HRV is shorter than the conventional 5-minute "
            "short-term recording; metric-specific validation is required"
        )


def _frequency_domain(
    nk: Any, info: dict[str, Any], sampling_rate: float, duration_s: float,
    beat_count: int, hrv: dict[str, dict[str, float | int | None]], warnings: list[str],
) -> None:
    """Run frequency-domain HRV when duration and beats allow it, noting short windows."""
    if duration_s < 120 or beat_count < 50:
        warnings.append(
            "frequency-domain HRV skipped: require at least 120 seconds and "
            "50 detected beats in this conservative CLI"
        )
        return
    _hrv_domain(nk, "frequency", info, sampling_rate, hrv, warnings)
    if duration_s < 300:
        warnings.append(
            "frequency-domain HRV is below the conventional 5-minute "
            "short-term window; do not interpret VLF/ULF and justify bands"
        )


def _nonlinear_domain(
    nk: Any, info: dict[str, Any], sampling_rate: float, beat_count: int,
    hrv: dict[str, dict[str, float | int | None]], warnings: list[str],
) -> None:
    """Run nonlinear HRV only when enough beats were detected."""
    if beat_count < 100:
        warnings.append(
            "nonlinear HRV skipped: fewer than 100 detected beats; many "
            "entropy/fractal metrics need substantially more"
        )
    else:
        _hrv_domain(nk, "nonlinear", info, sampling_rate, hrv, warnings)


def _compute_hrv(
    nk: Any,
    domains: set[str],
    info: dict[str, Any],
    sampling_rate: float,
    duration_s: float,
    beat_count: int,
    warnings: list[str],
) -> dict[str, dict[str, float | int | None]]:
    """Run the requested HRV domains subject to duration and beat-count gates."""
    hrv: dict[str, dict[str, float | int | None]] = {}
    if "time" in domains:
        _time_domain(nk, info, sampling_rate, duration_s, beat_count, hrv, warnings)
    if "frequency" in domains:
        _frequency_domain(nk, info, sampling_rate, duration_s, beat_count, hrv, warnings)
    if "nonlinear" in domains:
        _nonlinear_domain(nk, info, sampling_rate, beat_count, hrv, warnings)
    return hrv


def main() -> None:
    """Run the command-line interface."""
    args = build_parser().parse_args()
    sampling_rate, domains = _check_options(args)

    import neurokit2 as nk
    import numpy as np

    installed = require_pinned_neurokit2(nk)
    ecg, row_count, source = _load_ecg(args, nk, np, sampling_rate)

    duration_s = len(ecg) / sampling_rate
    if duration_s < 5:
        raise CliError("ECG must contain at least 5 seconds for this pipeline")
    try:
        signals, info = nk.ecg_process(
            ecg,
            sampling_rate=sampling_rate,
            method=args.method,
        )
    except (TypeError, ValueError, RuntimeError, IndexError) as exc:
        raise CliError(f"ECG processing failed: {exc}") from exc
    peaks = info.get("ECG_R_Peaks")
    if peaks is None or len(peaks) < 3:
        raise CliError("fewer than three R-peaks were detected")
    beat_count = len(peaks)

    warnings: list[str] = []
    hrv = _compute_hrv(nk, domains, info, sampling_rate, duration_s, beat_count, warnings)

    artifact_counts = _artifact_counts(info)
    corrected_total = sum(artifact_counts.values())
    if corrected_total:
        warnings.append(
            "R-peak corrections were applied by ecg_process(); inspect the raw "
            "trace, uncorrected peaks, and correction categories"
        )
    if source == "deidentified_local_csv":
        warnings.append(
            "input amplitude units are not inferred; record sensor units, lead, "
            "gain, filters, and clock metadata separately"
        )

    report: dict[str, Any] = {
        "artifact_correction": {
            "algorithm": "Lipponen-Tarvainen via ecg_process(correct_artifacts=True)",
            "category_counts": artifact_counts,
            "corrected_event_count_sum": corrected_total,
            "uncorrected_peak_count": len(info.get("ECG_R_Peaks_Uncorrected", peaks)),
        },
        "detected_r_peaks": beat_count,
        "duration_s": duration_s,
        "hrv": hrv,
        "hrv_requested_domains": sorted(domains),
        "neurokit2_version": installed,
        "output_schema_observed": {
            "info_keys": sorted(str(key) for key in info),
            "signal_columns": [str(column) for column in signals.columns],
        },
        "path_redacted": True,
        "quality": _summary(signals["ECG_Quality"]),
        "research_use_only": True,
        "row_count": row_count,
        "sampling_rate_hz": sampling_rate,
        "source": source,
        "warning": (
            "This output is for research and education, not diagnosis, patient "
            "monitoring, or medical-device validation. Validate the detector, "
            "sensor, population, protocol, and artifact policy for the intended use."
        ),
        "warnings": warnings,
    }
    emit_pipeline_report(report, signals, args)


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
