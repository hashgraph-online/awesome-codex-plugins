#!/usr/bin/env python3
"""Estimate DL and QL by every approach ICH Q2(R2) 3.2.3 allows, and compare them.

The four approaches routinely disagree by a factor of two or more on the same
data. Reporting one number without naming the approach is the finding an
assessor raises, so this script computes all of the applicable ones side by side
and checks the answer against the reporting threshold it has to serve.

    # sigma from the calibration line, slope from the same fit
    python3 check_detection_limits.py --calibration calib.csv

    # sigma from blank responses
    python3 check_detection_limits.py --calibration calib.csv --blanks blanks.csv

    # confirm an estimated QL with real data at that level
    python3 check_detection_limits.py --calibration calib.csv \
        --confirm-ql 0.05 --confirm-data ql_check.csv --reporting-threshold 0.05

Input:
  --calibration  CSV with `level` and `response` (low-range calibration curve)
  --blanks       CSV with `response` (blank measurements)
  --confirm-data CSV with `measured` (results at or near the claimed QL)

Exit codes: 0 no findings, 1 findings raised, 2 bad input.
"""

from __future__ import annotations

import argparse
import math
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from _catalog import DL_QL_APPROACHES  # noqa: E402
from _common import (  # noqa: E402
    EXIT_FINDINGS,
    EXIT_OK,
    InputError,
    add_common_args,
    emit,
    finding,
    fit_linear,
    mean,
    note,
    parse_rows,
    read_input,
    require_columns,
    rsd_percent,
    run_cli,
    sample_sd,
    to_float,
)

DL_FACTOR = 3.3
QL_FACTOR = 10.0
REF_SD_SLOPE = "Q2(R2) 3.2.3.3"


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Estimate detection and quantitation limits per ICH Q2(R2) 3.2.3."
    )
    parser.add_argument("--calibration", required=True,
                        help="CSV/TSV/JSON with `level` and `response`")
    parser.add_argument("--blanks", help="CSV/TSV/JSON with `response` for blank samples")
    parser.add_argument("--signal-to-noise", type=float, default=None,
                        help="measured S/N at a stated concentration (use with --sn-level)")
    parser.add_argument("--sn-level", type=float, default=None,
                        help="the concentration at which --signal-to-noise was measured")
    parser.add_argument("--confirm-ql", type=float, default=None,
                        help="the QL being claimed, to be confirmed with --confirm-data")
    parser.add_argument("--confirm-data", help="CSV/TSV/JSON with `measured` at/near the QL")
    parser.add_argument("--confirm-accuracy-limit", type=float, default=20.0,
                        help="max %% bias allowed when confirming the QL (default 20)")
    parser.add_argument("--confirm-rsd-limit", type=float, default=20.0,
                        help="max %%RSD allowed when confirming the QL (default 20)")
    parser.add_argument("--reporting-threshold", type=float, default=None,
                        help="impurity reporting threshold the QL must be at or below")
    parser.add_argument("--weight", choices=("none", "1/x", "1/x2"), default="none")
    add_common_args(parser)
    return parser


def _fit_calibration(args: argparse.Namespace):
    """Read the calibration file and fit the (optionally weighted) line."""
    rows = parse_rows(read_input(args.calibration), args.calibration)
    require_columns(rows, ["level", "response"])
    xs = [to_float(r["level"], "level", i) for i, r in enumerate(rows)]
    ys = [to_float(r["response"], "response", i) for i, r in enumerate(rows)]
    weights = None
    if args.weight != "none":
        if any(x == 0 for x in xs):
            raise InputError("weighting needs non-zero levels")
        power = 1 if args.weight == "1/x" else 2
        weights = [1.0 / (abs(x) ** power) for x in xs]
    fit = fit_linear(xs, ys, weights)
    if fit.slope == 0:
        raise InputError("calibration slope is zero; DL/QL cannot be computed")
    return fit


def _sd_slope_result(approach: str, sigma: float, slope: float) -> dict:
    """Build a 3.2.3.3 result row for one choice of sigma."""
    return {
        "approach": approach,
        "sigma": sigma,
        "slope": slope,
        "DL": DL_FACTOR * sigma / abs(slope),
        "QL": QL_FACTOR * sigma / abs(slope),
        "reference": REF_SD_SLOPE,
    }


def _blank_result(args: argparse.Namespace, slope: float) -> dict:
    """Build the blank-SD result row, validating the blank measurements."""
    brows = parse_rows(read_input(args.blanks), args.blanks)
    require_columns(brows, ["response"])
    blanks = [to_float(r["response"], "response", i) for i, r in enumerate(brows)]
    if len(blanks) < 3:
        raise InputError("blank SD needs at least 3 blank measurements")
    bsd = sample_sd(blanks)
    result = _sd_slope_result(f"sd-and-slope (sigma = SD of {len(blanks)} blanks)", bsd, slope)
    note(f"blank mean response {mean(blanks):.6g}, SD {bsd:.6g}, n={len(blanks)}")
    return result


def _signal_to_noise_result(args: argparse.Namespace, slope: float) -> dict:
    """Build the signal-to-noise (3.2.3.2) result row."""
    if args.sn_level is None:
        raise InputError("--signal-to-noise needs --sn-level")
    if args.signal_to_noise <= 0 or args.sn_level <= 0:
        raise InputError("--signal-to-noise and --sn-level must be > 0")
    per_unit = args.signal_to_noise / args.sn_level
    result = {
        "approach": f"signal-to-noise (S/N {args.signal_to_noise:g} at {args.sn_level:g})",
        "sigma": float("nan"),
        "slope": slope,
        "DL": 3.0 / per_unit,
        "QL": 10.0 / per_unit,
        "reference": "Q2(R2) 3.2.3.2",
    }
    note(
        "signal-to-noise DL uses the 3:1 ratio and QL the 10:1 ratio from Q2(R2) 3.2.3.2, "
        "scaled linearly from the measured S/N. Linear scaling of noise is an assumption -- "
        "confirm at the resulting level"
    )
    return result


def _estimate_results(args: argparse.Namespace, fit) -> list[dict]:
    """Compute DL/QL by every applicable approach."""
    slope = fit.slope
    results = [
        _sd_slope_result("sd-and-slope (sigma = residual SD of regression)",
                         fit.residual_sd, slope),
        _sd_slope_result("sd-and-slope (sigma = SD of y-intercept)", fit.se_intercept, slope),
    ]
    if args.blanks:
        results.append(_blank_result(args, slope))
    if args.signal_to_noise is not None:
        results.append(_signal_to_noise_result(args, slope))
    return results


def _spread_findings(qls: list[float], findings: list[str]) -> str:
    """Describe the QL spread across approaches; flag it when it exceeds 2x."""
    if len(qls) < 2:
        return ""
    ratio = max(qls) / min(qls) if min(qls) > 0 else float("inf")
    spread_note = (
        f"QL estimates span {min(qls):.6g} to {max(qls):.6g} ({ratio:.2f}x) across "
        f"{len(qls)} approaches"
    )
    if ratio > 2.0:
        findings.append(
            spread_note
            + ": name the approach used in the report, and confirm the claimed limit with "
            "real data at that level (Q2(R2) 3.2.3.5)"
        )
    return spread_note


def _confirmation(args: argparse.Namespace, findings: list[str]) -> list[dict]:
    """Confirm the claimed QL with real data (Q2(R2) 3.2.3.4 / 3.2.3.5)."""
    if not args.confirm_data:
        if args.confirm_ql is not None:
            note(
                "a QL was claimed but no confirmation data supplied. Q2(R2) 3.2.3.5 asks that an "
                "estimated limit be validated by analysing samples at or near it"
            )
        return []
    if args.confirm_ql is None:
        raise InputError("--confirm-data needs --confirm-ql")
    crows = parse_rows(read_input(args.confirm_data), args.confirm_data)
    require_columns(crows, ["measured"])
    measured = [to_float(r["measured"], "measured", i) for i, r in enumerate(crows)]
    if len(measured) < 3:
        raise InputError("QL confirmation needs at least 3 determinations")
    m = mean(measured)
    bias = 100.0 * (m - args.confirm_ql) / args.confirm_ql
    rsd = rsd_percent(measured)
    confirm_rows = [
        {"metric": "claimed QL", "value": args.confirm_ql},
        {"metric": "n determinations", "value": len(measured)},
        {"metric": "mean measured", "value": m},
        {"metric": "bias vs claimed QL (%)", "value": bias},
        {"metric": "RSD (%)", "value": rsd},
        {"metric": "accuracy limit (%)", "value": args.confirm_accuracy_limit},
        {"metric": "RSD limit (%)", "value": args.confirm_rsd_limit},
    ]
    if abs(bias) > args.confirm_accuracy_limit:
        findings.append(
            f"QL confirmation: bias {bias:+.2f}% at the claimed QL exceeds "
            f"+/-{args.confirm_accuracy_limit:g}%"
        )
    if math.isfinite(rsd) and rsd > args.confirm_rsd_limit:
        findings.append(
            f"QL confirmation: {rsd:.2f}% RSD at the claimed QL exceeds "
            f"{args.confirm_rsd_limit:g}%"
        )
    return confirm_rows


def _straddle_check(args: argparse.Namespace, qls: list[float], conservative: float,
                    findings: list[str]) -> None:
    """Note the conservative estimate used, and flag QLs that straddle the threshold."""
    note(
        f"no --confirm-ql given, so the reporting-threshold check uses the most "
        f"conservative estimate ({conservative:.6g}), not the most favourable "
        f"({min(qls):.6g})"
    )
    if min(qls) <= args.reporting_threshold < conservative:
        findings.append(
            f"the QL estimates straddle the reporting threshold "
            f"{args.reporting_threshold:.6g}: {min(qls):.6g} would pass and "
            f"{conservative:.6g} would not. Whether this procedure meets Q2(R2) "
            "3.2.3.5 depends on which approach is chosen, so choose it, justify it, "
            "and confirm the claimed limit with data at that level"
        )


def _margin_notes(args: argparse.Namespace, claimed: float) -> None:
    """Report how far the claimed QL sits below the reporting threshold."""
    ratio = args.reporting_threshold / claimed if claimed > 0 else float("inf")
    if math.isclose(ratio, 1.0, rel_tol=1e-9):
        note(
            f"QL {claimed:.6g} sits exactly at the reporting threshold "
            f"{args.reporting_threshold:.6g}, which satisfies Q2(R2) 3.2.3.5 with no "
            "margin -- any drift puts the procedure out of compliance"
        )
    else:
        note(
            f"QL {claimed:.6g} is {ratio:.1f}x below the reporting threshold "
            f"{args.reporting_threshold:.6g}"
        )
    if ratio >= 10:
        note(
            "the QL is roughly 10x or more below the reporting limit, so Q2(R2) 3.2.3.5 "
            "allows the confirmatory validation to be omitted with justification"
        )


def _reporting_threshold_check(args: argparse.Namespace, qls: list[float],
                               findings: list[str]) -> None:
    """Check the QL against the reporting threshold that gates an impurity method."""
    # With no claimed QL, use the LARGEST estimate. Taking the smallest would
    # let the check pass on the most flattering choice of sigma, which is the
    # wrong direction to err on a compliance requirement.
    conservative = max(qls) if qls else float("nan")
    claimed = args.confirm_ql if args.confirm_ql is not None else conservative
    if args.confirm_ql is None and qls:
        _straddle_check(args, qls, conservative, findings)
    if math.isfinite(claimed) and claimed > args.reporting_threshold:
        findings.append(
            f"QL {claimed:.6g} is above the reporting threshold "
            f"{args.reporting_threshold:.6g}. Q2(R2) 3.2.3.5 requires the QL for an "
            "impurity procedure to be at or below the reporting threshold"
        )
    elif math.isfinite(claimed):
        _margin_notes(args, claimed)


def _emit_results(args: argparse.Namespace, fit, results: list[dict],
                  confirm_rows: list[dict], findings: list[str]) -> None:
    """Print the estimates (and confirmation) in the requested format."""
    if args.format == "json":
        emit(
            [
                {
                    "calibration": {
                        "n": fit.n,
                        "slope": fit.slope,
                        "intercept": fit.intercept,
                        "residual_sd": fit.residual_sd,
                        "weighting": args.weight,
                    },
                    "estimates": results,
                    "confirmation": confirm_rows,
                    "findings": findings,
                }
            ],
            "json",
        )
        return
    emit(results, args.format)
    if confirm_rows:
        print()
        emit(confirm_rows, args.format)


def main() -> int:
    """Run the command-line interface."""
    args = _build_parser().parse_args()

    fit = _fit_calibration(args)
    findings: list[str] = []
    results = _estimate_results(args, fit)

    # Spread across approaches: the point of computing all of them.
    qls = [r["QL"] for r in results if math.isfinite(r["QL"])]
    spread_note = _spread_findings(qls, findings)

    confirm_rows = _confirmation(args, findings)

    if args.reporting_threshold is not None:
        _reporting_threshold_check(args, qls, findings)

    _emit_results(args, fit, results, confirm_rows, findings)

    if not args.confirm_data:
        note(
            f"approach 'accuracy-precision' ({DL_QL_APPROACHES['accuracy-precision']['note']}) "
            "validates the QL directly rather than estimating it -- supply --confirm-data "
            "to use it"
        )
    if spread_note and not any(spread_note in f for f in findings):
        note(spread_note)
    note("Q2(R2) 3.2.3.5: report the limit AND the approach used to determine it")
    for f in findings:
        finding(f)
    if not findings:
        note("no findings against the checks that were run")
    note("this tool does not decide that a detection or quantitation limit is acceptable")
    return EXIT_FINDINGS if findings else EXIT_OK


if __name__ == "__main__":
    run_cli(main)
