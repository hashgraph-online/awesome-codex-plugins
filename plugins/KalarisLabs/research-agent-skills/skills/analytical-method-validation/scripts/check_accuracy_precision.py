#!/usr/bin/env python3
"""Evaluate accuracy and precision per ICH Q2(R2) 3.3.

Accuracy is reported as mean recovery with a confidence interval, which is what
Q2(R2) 3.3.1.4 asks for -- a bare mean is not sufficient. Precision is
decomposed into repeatability and intermediate precision by a one-way
random-effects model, because pooling all results into a single standard
deviation understates the day-to-day variability the procedure will actually
show in routine use.

    python3 check_accuracy_precision.py --input ap.csv
    python3 check_accuracy_precision.py -i ap.csv --accuracy-limit 2 --rsd-limit 2
    python3 check_accuracy_precision.py -i ap.csv --design-check assay --format json

Input columns:
  level      nominal / added concentration (groups the accuracy analysis)
  measured   measured or recovered concentration
  group      optional: day, analyst, instrument or run -- the intermediate
             precision factor. Without it only repeatability is estimated.

Exit codes: 0 no findings, 1 findings raised, 2 bad input.
"""

from __future__ import annotations

import argparse
import math
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    EXIT_FINDINGS,
    EXIT_OK,
    InputError,
    add_common_args,
    emit,
    finding,
    mean,
    note,
    one_way_components,
    parse_rows,
    read_input,
    require_columns,
    rsd_percent,
    run_cli,
    sample_sd,
    sd_confidence_interval,
    t_ppf,
    to_float,
)

# ICH Q2(R2) 3.3.2.1 minima, used only to comment on the design. Either option
# is sufficient on its own.
DESIGN_MINIMA = {
    "assay": {
        "range_determinations": 9,
        "range_levels": 3,
        "single_level_determinations": 6,
        "note": "9 determinations across the range (3x3), or 6 at 100% of test concentration",
    },
    "impurity": {
        "range_determinations": 9,
        "range_levels": 3,
        "single_level_determinations": 6,
        "note": "9 determinations across the range (3x3), or 6 at 100% of test concentration",
    },
}


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Check accuracy and precision from validation data."
    )
    parser.add_argument("--input", "-i", help="CSV/TSV/JSON file, or '-' for stdin")
    parser.add_argument("--accuracy-limit", type=float, default=None,
                        help="flag a level whose mean recovery deviates more than this %% "
                             "from 100%%")
    parser.add_argument("--rsd-limit", type=float, default=None,
                        help="flag repeatability or intermediate precision %%RSD above this")
    parser.add_argument("--ci-level", type=float, default=0.95,
                        help="confidence level for accuracy intervals (default 0.95)")
    parser.add_argument("--sd-ci-level", type=float, default=0.90,
                        help="confidence level for SD intervals (default 0.90)")
    parser.add_argument("--design-check", choices=sorted(DESIGN_MINIMA), default=None,
                        help="comment on the design against Q2(R2) recommended minima")
    parser.add_argument("--require-ci-within-limit", action="store_true",
                        help="require the whole accuracy CI inside the limit, not just the mean")
    add_common_args(parser)
    return parser


def _load_records(args: argparse.Namespace) -> tuple[list[dict], bool]:
    """Read the input rows and return typed records plus whether a group column exists."""
    rows = parse_rows(read_input(args.input), args.input)
    require_columns(rows, ["level", "measured"])
    has_group = "group" in rows[0]
    records = []
    for i, r in enumerate(rows):
        records.append(
            {
                "level": to_float(r["level"], "level", i),
                "measured": to_float(r["measured"], "measured", i),
                "group": (r.get("group") or "all").strip() or "all",
            }
        )
    return records, has_group


def _accuracy_findings(args: argparse.Namespace, level: float, m: float,
                       lo: float, hi: float) -> list[str]:
    """Return the accuracy findings (if any) raised for one level."""
    if args.accuracy_limit is None:
        return []
    if abs(m - 100.0) > args.accuracy_limit:
        return [
            f"level {level:g}: mean recovery {m:.2f}% is {m - 100.0:+.2f}% from nominal, "
            f"outside +/-{args.accuracy_limit:g}%"
        ]
    if not (args.require_ci_within_limit and math.isfinite(lo)):
        return []
    if lo < 100.0 - args.accuracy_limit or hi > 100.0 + args.accuracy_limit:
        return [
            f"level {level:g}: mean recovery {m:.2f}% is inside "
            f"+/-{args.accuracy_limit:g}% but its "
            f"{int(args.ci_level * 100)}% CI ({lo:.2f}, {hi:.2f}) is not -- the data "
            "do not demonstrate accuracy at this limit"
        ]
    return []


def _accuracy_row(args: argparse.Namespace, level: float, vals: list[float],
                  recoveries: list[float]) -> tuple[dict, float, float, float]:
    """Build one accuracy table row; return it with mean recovery and CI bounds."""
    m = mean(recoveries)
    n = len(recoveries)
    if n >= 2:
        sd = sample_sd(recoveries)
        half = t_ppf(0.5 + args.ci_level / 2.0, n - 1) * sd / math.sqrt(n)
        lo, hi = m - half, m + half
    else:
        sd, lo, hi = float("nan"), float("nan"), float("nan")
    row = {
        "level": level,
        "n": n,
        "mean_measured": mean(vals),
        "mean_recovery_pct": m,
        "bias_pct": m - 100.0,
        "sd_recovery_pct": sd,
        f"ci{int(args.ci_level * 100)}_low": lo,
        f"ci{int(args.ci_level * 100)}_high": hi,
    }
    return row, m, lo, hi


def _accuracy_section(args: argparse.Namespace, records: list[dict], levels: list[float],
                      findings: list[str]) -> tuple[list[dict], list[float]]:
    """Compute accuracy rows per level and append any findings."""
    accuracy_rows = []
    all_recoveries: list[float] = []
    for level in levels:
        vals = [rec["measured"] for rec in records if rec["level"] == level]
        if math.isclose(level, 0, rel_tol=0.0, abs_tol=0.0):
            raise InputError("a nominal level of 0 cannot be used for recovery")
        recoveries = [100.0 * v / level for v in vals]
        all_recoveries.extend(recoveries)
        row, m, lo, hi = _accuracy_row(args, level, vals, recoveries)
        accuracy_rows.append(row)
        findings.extend(_accuracy_findings(args, level, m, lo, hi))
    return accuracy_rows, all_recoveries


def _ratio_rsd(sd: float, base: float) -> float:
    """Express an SD as a percent of a base value, NaN when the base is zero."""
    return 100.0 * sd / base if base else float("nan")


def _repeatability_only_row(args: argparse.Namespace, label: str, groups: dict[str, list[float]],
                            reference: float | None, exc: InputError) -> dict | None:
    """Fallback row when intermediate precision cannot be estimated."""
    pct = int(args.sd_ci_level * 100)
    vals = [v for vs in groups.values() for v in vs]
    if len(vals) < 2:
        note(f"{label}: too few values for a precision estimate")
        return None
    sd = sample_sd(vals)
    base = reference if reference else abs(mean(vals))
    lo, hi = sd_confidence_interval(sd, len(vals) - 1, args.sd_ci_level)
    row = {"level": label, "component": "repeatability only", "sd": sd,
           "rsd_pct": _ratio_rsd(sd, base),
           "df": len(vals) - 1, f"ci{pct}_low_sd": lo, f"ci{pct}_high_sd": hi}
    note(f"{label}: intermediate precision not estimated ({exc})")
    return row


def _component_rows(args: argparse.Namespace, label: str, comp, base: float) -> list[dict]:
    """Build the repeatability, between-group and intermediate rows for one level."""
    pct = int(args.sd_ci_level * 100)
    sr_lo, sr_hi = sd_confidence_interval(
        comp.sd_repeatability, comp.df_within, args.sd_ci_level
    )
    sat_df = comp.satterthwaite_df()
    si_lo, si_hi = sd_confidence_interval(comp.sd_intermediate, sat_df, args.sd_ci_level)
    return [
        {"level": label, "component": "repeatability (within group)",
         "sd": comp.sd_repeatability, "rsd_pct": _ratio_rsd(comp.sd_repeatability, base),
         "df": comp.df_within, f"ci{pct}_low_sd": sr_lo, f"ci{pct}_high_sd": sr_hi},
        {"level": label, "component": "between-group", "sd": comp.sd_between,
         "rsd_pct": _ratio_rsd(comp.sd_between, base), "df": comp.df_between,
         f"ci{pct}_low_sd": float("nan"), f"ci{pct}_high_sd": float("nan")},
        {"level": label, "component": "intermediate precision (total)",
         "sd": comp.sd_intermediate, "rsd_pct": _ratio_rsd(comp.sd_intermediate, base),
         "df": sat_df, f"ci{pct}_low_sd": si_lo, f"ci{pct}_high_sd": si_hi},
    ]


def _component_notes_and_findings(args: argparse.Namespace, label: str, comp, base: float,
                                  findings: list[str]) -> None:
    """Emit design notes and RSD-limit findings for one level's components."""
    if math.isclose(comp.sd_between, 0.0, rel_tol=0.0, abs_tol=0.0):
        note(
            f"{label}: between-group variance estimated as zero (MS_between <= MS_within); "
            "the groups are indistinguishable at this level"
        )
    if not comp.balanced:
        note(f"{label}: unbalanced design, effective group size {comp.n_effective:.3f}")
    if args.rsd_limit is None:
        return
    for name, value in (
        ("repeatability", _ratio_rsd(comp.sd_repeatability, base)),
        ("intermediate precision", _ratio_rsd(comp.sd_intermediate, base)),
    ):
        if math.isfinite(value) and value > args.rsd_limit:
            findings.append(
                f"{label}: {name} {value:.3f}% RSD exceeds the stated "
                f"{args.rsd_limit:g}% limit"
            )


def _precision_block(args: argparse.Namespace, precision_rows: list[dict], findings: list[str],
                     label: str, groups: dict[str, list[float]], reference: float | None) -> None:
    """Append rows for one level (or for the normalised all-levels view)."""
    try:
        comp = one_way_components(groups)
    except InputError as exc:
        row = _repeatability_only_row(args, label, groups, reference, exc)
        if row is not None:
            precision_rows.append(row)
        return
    base = reference if reference else abs(comp.grand_mean)
    precision_rows.extend(_component_rows(args, label, comp, base))
    _component_notes_and_findings(args, label, comp, base, findings)


def _grouped_precision(args: argparse.Namespace, records: list[dict], levels: list[float],
                       precision_rows: list[dict], findings: list[str]) -> None:
    """Estimate precision per level, plus a normalised all-levels view, using groups."""
    for level in levels:
        groups: dict[str, list[float]] = {}
        for rec in records:
            if rec["level"] == level:
                groups.setdefault(rec["group"], []).append(rec["measured"])
        _precision_block(args, precision_rows, findings, f"{level:g}", groups,
                         reference=abs(level))

    # Level-independent view: recovery as % of nominal, pooled across levels.
    norm_groups: dict[str, list[float]] = {}
    for rec in records:
        norm_groups.setdefault(rec["group"], []).append(
            100.0 * rec["measured"] / rec["level"]
        )
    if len(norm_groups) >= 2:
        _precision_block(args, precision_rows, findings, "all (% of nominal)", norm_groups,
                         reference=100.0)


def _ungrouped_precision(args: argparse.Namespace, records: list[dict], levels: list[float],
                         precision_rows: list[dict], findings: list[str]) -> None:
    """Estimate repeatability only, per level, when there is no group column."""
    pct = int(args.sd_ci_level * 100)
    for level in levels:
        vals = [rec["measured"] for rec in records if rec["level"] == level]
        if len(vals) < 2:
            continue
        sd = sample_sd(vals)
        lo, hi = sd_confidence_interval(sd, len(vals) - 1, args.sd_ci_level)
        rsd = 100.0 * sd / abs(level)
        precision_rows.append(
            {"level": f"{level:g}", "component": "repeatability (no group column)",
             "sd": sd, "rsd_pct": rsd, "df": len(vals) - 1,
             f"ci{pct}_low_sd": lo, f"ci{pct}_high_sd": hi}
        )
        if args.rsd_limit is not None and rsd > args.rsd_limit:
            findings.append(
                f"{level:g}: repeatability {rsd:.3f}% RSD exceeds {args.rsd_limit:g}%"
            )
    note(
        "no `group` column, so only repeatability was estimated. Q2(R2) 3.3.2.2 expects "
        "intermediate precision from different days, analysts or equipment"
    )


def _precision_section(args: argparse.Namespace, records: list[dict], levels: list[float],
                       has_group: bool, findings: list[str]) -> list[dict]:
    """Compute precision rows (estimated WITHIN each concentration level)."""
    # Pooling levels together would let the 80/100/120 spread masquerade as imprecision.
    precision_rows: list[dict] = []
    if has_group:
        _grouped_precision(args, records, levels, precision_rows, findings)
    else:
        _ungrouped_precision(args, records, levels, precision_rows, findings)

    naive = rsd_percent([rec["measured"] for rec in records])
    if len(levels) > 1:
        note(
            f"a single SD over every result regardless of level would report {naive:.3f}% RSD, "
            "which is a range effect and not precision. Precision is reported per level below"
        )
    return precision_rows


def _design_commentary(args: argparse.Namespace, records: list[dict], levels: list[float],
                       findings: list[str]) -> None:
    """Comment on the design against Q2(R2) 3.3.2.1 and flag it when neither option holds."""
    # Q2(R2) 3.3.2.1 offers two alternatives, and either one is sufficient:
    #   (a) >=9 determinations covering the reportable range (e.g. 3 levels x 3), or
    #   (b) >=6 determinations at 100% of the test concentration.
    # Flag only when neither holds. Requiring 9 unconditionally would raise a
    # finding against a design the guideline explicitly permits.
    spec = DESIGN_MINIMA[args.design_check]
    option_a = len(records) >= spec["range_determinations"] and len(levels) >= spec["range_levels"]
    per_level = {lv: sum(1 for r in records if r["level"] == lv) for lv in levels}
    best_single = max(per_level.values())
    option_b = best_single >= spec["single_level_determinations"]
    if option_a:
        note(
            f"design satisfies Q2(R2) 3.3.2.1 option (a): {len(records)} determinations "
            f"across {len(levels)} levels"
        )
    elif option_b:
        note(
            f"design satisfies Q2(R2) 3.3.2.1 option (b): {best_single} determinations at a "
            "single level. Note that option (b) gives no information about precision "
            "across the range"
        )
    else:
        findings.append(
            f"repeatability design meets neither Q2(R2) 3.3.2.1 option: "
            f"{len(records)} determinations across {len(levels)} level(s), with at most "
            f"{best_single} at any one level. Option (a) needs "
            f"{spec['range_determinations']} across at least {spec['range_levels']} levels; "
            f"option (b) needs {spec['single_level_determinations']} at 100% of the test "
            "concentration"
        )


def _emit_results(args: argparse.Namespace, accuracy_rows: list[dict],
                  precision_rows: list[dict], all_recoveries: list[float],
                  findings: list[str]) -> None:
    """Print the accuracy and precision tables in the requested format."""
    if args.format == "json":
        emit([{"accuracy": accuracy_rows, "precision": precision_rows,
               "overall_mean_recovery_pct": mean(all_recoveries),
               "findings": findings}], "json")
    else:
        emit(accuracy_rows, args.format)
        print()
        emit(precision_rows, args.format)


def main() -> int:
    """Run the command-line interface."""
    args = _build_parser().parse_args()

    if not 0.5 <= args.ci_level < 1.0:
        raise InputError("--ci-level must be in [0.5, 1)")

    records, has_group = _load_records(args)
    findings: list[str] = []
    levels = sorted({rec["level"] for rec in records})

    accuracy_rows, all_recoveries = _accuracy_section(args, records, levels, findings)
    precision_rows = _precision_section(args, records, levels, has_group, findings)

    if args.design_check:
        _design_commentary(args, records, levels, findings)

    _emit_results(args, accuracy_rows, precision_rows, all_recoveries, findings)

    note(
        "Q2(R2) 3.3.1.4: report accuracy as mean percent recovery, or the difference from the "
        "accepted true value, with a 100(1-alpha)% confidence interval"
    )
    note(
        "Q2(R2) 3.3.2.2: intermediate precision covers days, environmental conditions, analysts "
        "and equipment; the effects need not be studied individually"
    )
    for f in findings:
        finding(f)
    if not findings:
        note("no findings against the checks that were run")
    note("this tool does not decide that accuracy or precision is acceptable")
    return EXIT_FINDINGS if findings else EXIT_OK


if __name__ == "__main__":
    run_cli(main)
