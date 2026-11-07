#!/usr/bin/env python3
"""Compare RMS spectral levels with a user-supplied limit profile."""

import argparse
import io
import json
import math
import os
from pathlib import Path
import secrets
import sys


SPECTRUM_SCHEMA = "harmonic-lines/1"
PROFILE_SCHEMA = "emc-limit-profile/1"
RESULT_SCHEMA = "harmonic-limit-screen/1"
DETECTORS = ("peak", "quasi_peak", "average")
LEVEL_UNITS = ("dbuv", "dbuv_per_m", "dbua")
MARGIN_DECIMALS = 6
MAX_INPUT_BYTES = 16_000_000
CLAIM_BOUNDARY = "This comparison is not a compliance determination."


class ValidationError(ValueError):
    """Raised when an input does not match the screening format."""


def _mapping(value, path):
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must be an object")
    return value


def _list(value, path):
    if not isinstance(value, list):
        raise ValidationError(f"{path} must be an array")
    return value


def _text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{path} must be a non-empty string")
    return value


def _number(value, path):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{path} must be a finite number")
    try:
        number = float(value)
    except OverflowError:
        raise ValidationError(f"{path} must be a finite number") from None
    if not math.isfinite(number):
        raise ValidationError(f"{path} must be a finite number")
    return number


def validate_spectrum(data: object) -> dict:
    """Return a normalized spectrum with points sorted by frequency."""
    root = _mapping(data, "spectrum")
    if root.get("schema_version") != SPECTRUM_SCHEMA:
        raise ValidationError(
            f"spectrum.schema_version must equal {SPECTRUM_SCHEMA!r}"
        )
    level_unit = root.get("level_unit")
    if level_unit not in LEVEL_UNITS:
        raise ValidationError(
            f"spectrum.level_unit must be one of {', '.join(LEVEL_UNITS)}"
        )

    normalized_points = []
    seen_frequencies = set()
    for index, raw_point in enumerate(
        _list(root.get("points"), "spectrum.points")
    ):
        point = _mapping(raw_point, f"spectrum.points[{index}]")
        frequency = _number(
            point.get("frequency_hz"),
            f"spectrum.points[{index}].frequency_hz",
        )
        level = _number(
            point.get("level"),
            f"spectrum.points[{index}].level",
        )
        if frequency <= 0:
            raise ValidationError(
                f"spectrum.points[{index}].frequency_hz must be greater "
                "than zero"
            )
        if frequency in seen_frequencies:
            raise ValidationError(
                f"spectrum.points contains duplicate frequency_hz {frequency}"
            )
        seen_frequencies.add(frequency)
        normalized_points.append(
            {"frequency_hz": frequency, "level": level}
        )

    normalized_points.sort(key=lambda point: point["frequency_hz"])
    normalized = {
        "schema_version": SPECTRUM_SCHEMA,
        "level_unit": level_unit,
        "points": normalized_points,
    }
    if "source" in root:
        normalized["source"] = _mapping(root["source"], "spectrum.source")
    return normalized


def _limit(value, path, single_frequency):
    """Return a flat limit number or a {"start", "stop"} sloped limit."""
    if not isinstance(value, dict):
        return _number(value, path)
    if set(value) != {"start", "stop"}:
        raise ValidationError(
            f"{path} must be a number or an object with exactly "
            "'start' and 'stop'"
        )
    sloped = {
        "start": _number(value["start"], f"{path}.start"),
        "stop": _number(value["stop"], f"{path}.stop"),
    }
    if single_frequency and sloped["start"] != sloped["stop"]:
        raise ValidationError(
            f"{path}.start must equal {path}.stop when start_hz equals "
            "stop_hz"
        )
    return sloped


def _limit_at(limit, band, frequency):
    """Return the limit at a frequency, interpolating linearly in log10(f)."""
    if not isinstance(limit, dict):
        return limit
    start_hz, stop_hz = band["start_hz"], band["stop_hz"]
    if frequency <= start_hz:
        return limit["start"]
    if frequency >= stop_hz:
        return limit["stop"]
    ratio = stop_hz / start_hz
    if math.isfinite(ratio):
        span = math.log(ratio)
        offset = math.log(frequency / start_hz)
    else:
        span = math.log10(stop_hz) - math.log10(start_hz)
        offset = math.log10(frequency) - math.log10(start_hz)
    fraction = offset / span if span > 0 else 0.0
    fraction = min(max(fraction, 0.0), 1.0)
    value = limit["start"] * (1.0 - fraction) + limit["stop"] * fraction
    return round(value, MARGIN_DECIMALS) + 0.0


def validate_limit_profile(data: object) -> dict:
    """Return a normalized, provenance-preserving limit profile."""
    root = _mapping(data, "profile")
    if root.get("schema_version") != PROFILE_SCHEMA:
        raise ValidationError(
            f"profile.schema_version must equal {PROFILE_SCHEMA!r}"
        )

    profile_id = _text(root.get("profile_id"), "profile.profile_id")
    limit_unit = root.get("limit_unit")
    if limit_unit not in LEVEL_UNITS:
        raise ValidationError(
            f"profile.limit_unit must be one of {', '.join(LEVEL_UNITS)}"
        )
    raw_source = _mapping(root.get("source"), "profile.source")
    _text(raw_source.get("kind"), "profile.source.kind")
    _text(raw_source.get("citation"), "profile.source.citation")

    raw_bands = _list(root.get("bands"), "profile.bands")
    if not raw_bands:
        raise ValidationError("profile.bands must contain at least one band")

    normalized_bands = []
    band_names = set()
    for index, raw_band in enumerate(raw_bands):
        band = _mapping(raw_band, f"profile.bands[{index}]")
        name = _text(band.get("name"), f"profile.bands[{index}].name")
        if name in band_names:
            raise ValidationError(
                f"profile.bands contains duplicate band name {name!r}"
            )
        band_names.add(name)

        start = _number(
            band.get("start_hz"), f"profile.bands[{index}].start_hz"
        )
        stop = _number(
            band.get("stop_hz"), f"profile.bands[{index}].stop_hz"
        )
        if start <= 0 or start > stop:
            raise ValidationError(
                f"profile.bands[{index}].start_hz must be positive and "
                "less than or equal to stop_hz"
            )

        raw_limits = _mapping(
            band.get("limits"),
            f"profile.bands[{index}].limits",
        )
        if not raw_limits:
            raise ValidationError(
                f"profile.bands[{index}].limits must contain at "
                "least one detector"
            )
        unsupported = sorted(set(raw_limits) - set(DETECTORS))
        if unsupported:
            raise ValidationError(
                f"profile.bands[{index}].limits has unsupported "
                f"detector {unsupported[0]!r}"
            )
        limits = {
            detector: _limit(
                value,
                f"profile.bands[{index}].limits.{detector}",
                start == stop,
            )
            for detector, value in raw_limits.items()
        }
        normalized_bands.append(
            {
                "name": name,
                "start_hz": start,
                "stop_hz": stop,
                "limits": limits,
            }
        )

    return {
        "schema_version": PROFILE_SCHEMA,
        "profile_id": profile_id,
        "limit_unit": limit_unit,
        "source": dict(raw_source),
        "bands": normalized_bands,
    }


def screen_harmonics(
    spectrum: dict,
    profile: dict,
    limit_column: str,
    design_margin_db: float = 0.0,
) -> dict:
    """Return a harmonic-limit-screen/1 result from validated inputs."""
    if limit_column not in DETECTORS:
        raise ValidationError(
            f"limit_column must be one of {', '.join(DETECTORS)}"
        )
    design_margin = _number(design_margin_db, "design_margin_db")
    if design_margin < 0:
        raise ValidationError(
            "design_margin_db must be greater than or equal to zero"
        )
    if profile["limit_unit"] != spectrum["level_unit"]:
        raise ValidationError(
            f"profile.limit_unit {profile['limit_unit']!r} does not match "
            f"spectrum.level_unit {spectrum['level_unit']!r}"
        )

    results = []
    for index, band in enumerate(profile["bands"]):
        in_band = [
            point
            for point in spectrum["points"]
            if band["start_hz"]
            <= point["frequency_hz"]
            <= band["stop_hz"]
        ]
        limit_spec = band["limits"].get(limit_column)
        if isinstance(limit_spec, dict) and in_band:
            # The worst point has the smallest margin; with a sloped limit
            # that need not be the highest level in the band.
            worst, limit = min(
                (
                    (point, _limit_at(limit_spec, band, point["frequency_hz"]))
                    for point in in_band
                ),
                key=lambda pair: (
                    round(pair[1] - pair[0]["level"], MARGIN_DECIMALS),
                    pair[0]["frequency_hz"],
                ),
            )
        else:
            worst = max(
                in_band,
                key=lambda point: (
                    point["level"],
                    -point["frequency_hz"],
                ),
                default=None,
            )
            limit = None if isinstance(limit_spec, dict) else limit_spec

        if worst is None or limit is None:
            margin = None
            status = "not_assessed"
        else:
            # Adding 0.0 turns a rounded -0.0 into 0.0 for clean output.
            margin = round(limit - worst["level"], MARGIN_DECIMALS) + 0.0
            if not math.isfinite(margin):
                raise ValidationError(
                    f"bands[{index}].margin_db is not a finite number"
                )
            if margin < 0:
                status = "above_limit_screen"
            elif margin < design_margin:
                status = "near_limit"
            else:
                status = "at_or_below_limit_screen"

        if limit_spec is None:
            lines_above = lines_near = None
        else:
            line_margins = [
                round(
                    _limit_at(limit_spec, band, point["frequency_hz"])
                    - point["level"],
                    MARGIN_DECIMALS,
                )
                for point in in_band
            ]
            lines_above = sum(1 for value in line_margins if value < 0)
            lines_near = sum(
                1 for value in line_margins if 0 <= value < design_margin
            )

        results.append(
            {
                "name": band["name"],
                "worst_frequency_hz": (
                    worst["frequency_hz"] if worst else None
                ),
                "level": worst["level"] if worst else None,
                "limit": limit,
                "margin_db": margin,
                "status": status,
                "lines_above_limit": lines_above,
                "lines_near_limit": lines_near,
            }
        )

    return {
        "schema_version": RESULT_SCHEMA,
        "result_class": "screening_only",
        "limit_column": limit_column,
        "design_margin_db": design_margin,
        "level_unit": spectrum["level_unit"],
        "spectrum_source": spectrum.get("source"),
        "profile": {
            "profile_id": profile["profile_id"],
            "source": profile["source"],
        },
        "bands": results,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _reject_duplicate_keys(pairs):
    parsed = {}
    for key, value in pairs:
        if key in parsed:
            raise ValidationError(f"duplicate key {key!r}")
        parsed[key] = value
    return parsed


def _reject_constant(name):
    raise ValidationError(f"non-finite number {name} is not allowed")


def _finite_float(text):
    number = float(text)
    if not math.isfinite(number):
        raise ValidationError(f"number {text} is not finite")
    return number


def _load_json(path: Path):
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValidationError(
                f"input exceeds the {MAX_INPUT_BYTES} byte size limit"
            )
        # Decode through a text wrapper so newline handling (and therefore
        # JSON error line/column numbers) matches a text-mode read.
        return json.load(
            io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8-sig"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except ValidationError as exc:
        raise ValidationError(f"{path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ValidationError(
            f"{path} is not valid UTF-8 text: {exc}"
        ) from exc
    except ValueError as exc:
        raise ValidationError(f"{path} is not valid JSON: {exc}") from exc
    except RecursionError as exc:
        raise ValidationError(f"{path} is nested too deeply") from exc
    except OSError as exc:
        raise ValidationError(f"could not read {path}: {exc}") from exc


def _nonnegative_finite(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "must be a finite number greater than or equal to zero"
        ) from exc
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError(
            "must be a finite number greater than or equal to zero"
        )
    return number


def _write_json(payload: dict, output: Path | None):
    try:
        text = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    except (ValueError, RecursionError) as exc:
        raise ValidationError(f"result is not valid JSON: {exc}") from exc
    if output is None:
        sys.stdout.write(text)
        return
    # Write beside the target, then rename, so a failure never leaves a
    # truncated or partially written result at the requested path.
    if not output.name:
        raise ValidationError(f"could not write {output}: not a file path")
    temp = output.with_name(f".{output.name}.{secrets.token_hex(8)}.tmp")
    created = False
    try:
        descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
        created = True
        with os.fdopen(
            descriptor, "w", encoding="utf-8", newline="\n"
        ) as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, output)
    except OSError as exc:
        if created:
            temp.unlink(missing_ok=True)
        raise ValidationError(f"could not write {output}: {exc}") from exc


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Screen supplied RMS spectral levels against a "
            "user-supplied limit profile"
        )
    )
    parser.add_argument(
        "--spectrum",
        type=Path,
        required=True,
        help=f"{SPECTRUM_SCHEMA} JSON input",
    )
    parser.add_argument(
        "--limits",
        type=Path,
        required=True,
        help=f"{PROFILE_SCHEMA} JSON input",
    )
    parser.add_argument(
        "--limit-column",
        choices=DETECTORS,
        required=True,
        help="Which profile limit to compare (does not emulate a detector)",
    )
    parser.add_argument(
        "--design-margin-db",
        type=_nonnegative_finite,
        default=0.0,
        help="Nonnegative engineering margin in dB (default: 0)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON here instead of stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line tool and return a process exit code."""
    args = _build_parser().parse_args(argv)
    try:
        if args.output is not None:
            for source in (args.spectrum, args.limits):
                if args.output.resolve() == source.resolve() or (
                    args.output.exists()
                    and source.exists()
                    and args.output.samefile(source)
                ):
                    raise ValidationError(
                        f"--output would overwrite input {source}: {args.output}"
                    )
        spectrum = validate_spectrum(_load_json(args.spectrum))
        profile = validate_limit_profile(_load_json(args.limits))
        result = screen_harmonics(
            spectrum,
            profile,
            limit_column=args.limit_column,
            design_margin_db=args.design_margin_db,
        )
        _write_json(result, args.output)
    except (ValidationError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # UTF-8 on a cp1252 pipe (Windows)
        if (getattr(_stream, "encoding", "") or "").lower().replace("-", "") != "utf8" \
                and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    raise SystemExit(main())
