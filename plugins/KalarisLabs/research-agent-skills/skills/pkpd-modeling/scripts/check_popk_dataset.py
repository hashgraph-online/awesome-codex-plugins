#!/usr/bin/env python3
"""Validate a NONMEM/nlmixr2-ready population PK dataset before it costs you a run.

Most population analyses lose more time to dataset defects than to modelling.
The defects that hurt are the silent ones: NONMEM reads a non-numeric DV as
zero rather than refusing it, a missing II turns ADDL into nothing, records
that share a timestamp are applied in file order, and a dose with no
observations contributes an individual whose ETAs are pure prior. None of these
stop a run. They just change the answer.

    python3 check_popk_dataset.py -i nmdata.csv
    python3 check_popk_dataset.py -i nmdata.csv --covariates WT,AGE,CRCL --time-varying WT
    python3 check_popk_dataset.py -i nmdata.csv --strict --format json

Checks are grouped as errors (the run will be wrong), warnings (the run may be
wrong), and notes (worth confirming). Exit code is 1 if anything at or above
``--fail-on`` was raised.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence

from _common import (
    Report,
    add_format_argument,
    main_wrapper,
    read_table,
)

SEVERITY_ORDER = {"note": 0, "warning": 1, "error": 2}

# NONMEM data item conventions. EVID 3 resets the system, 4 resets and doses.
EVID_MEANINGS = {
    "0": "observation",
    "1": "dose",
    "2": "other-type event (no dose, no observation)",
    "3": "reset",
    "4": "reset and dose",
}

MISSING = {"", ".", "na", "n/a", "nan", "null", "none"}


def _num(value: str) -> float | None:
    """Handle num."""
    text = (value or "").strip()
    if text.lower() in MISSING:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _is_missing(value: str) -> bool:
    """Return whether missing."""
    return (value or "").strip().lower() in MISSING


class Findings:
    """Findings."""
    def __init__(self) -> None:
        """Initialise the instance."""
        self.items: list[dict[str, object]] = []

    def add(self, severity: str, check: str, detail: str, rows: Sequence[int] = ()) -> None:
        """Add."""
        listed = list(rows)[:8]
        self.items.append(
            {
                "severity": severity,
                "check": check,
                "detail": detail,
                "n_records": len(rows),
                "example_rows": ", ".join(str(r) for r in listed) + ("..." if len(rows) > 8 else ""),
            }
        )

    def max_severity(self) -> int:
        """Handle max severity."""
        return max((SEVERITY_ORDER[i["severity"]] for i in self.items), default=-1)


# ------------------------------------------------------------------ checks


@dataclass
class _Cols:
    """Resolved (case-insensitive) dataset column names; None when absent."""

    lookup: dict[str, str]
    id: str | None
    time: str | None
    dv: str | None
    amt: str | None
    evid: str | None
    mdv: str | None
    rate: str | None
    ss: str | None
    ii: str | None
    addl: str | None

    def get(self, name: str) -> str | None:
        """Resolve a column name case-insensitively, or None if absent."""
        return self.lookup.get(name.lower())


@dataclass
class _RecordIssues:
    """Row numbers collected by the per-record checks, one list per defect type."""

    bad_dv_text: list[int] = field(default_factory=list)
    neg_time: list[int] = field(default_factory=list)
    neg_conc: list[int] = field(default_factory=list)
    bad_evid: list[int] = field(default_factory=list)
    dose_without_amt: list[int] = field(default_factory=list)
    obs_with_amt: list[int] = field(default_factory=list)
    obs_missing_dv: list[int] = field(default_factory=list)
    mdv_conflict: list[int] = field(default_factory=list)
    rate_issues: list[int] = field(default_factory=list)
    ss_missing_ii: list[int] = field(default_factory=list)
    addl_missing_ii: list[int] = field(default_factory=list)
    zero_ii: list[int] = field(default_factory=list)


# (issue list name, severity, check label, detail) in report order.
_RECORD_FINDINGS: tuple[tuple[str, str, str, str], ...] = (
    (
        "bad_dv_text",
        "error",
        "non-numeric DV",
        "DV contains text (for example 'BLQ' or '<LLOQ'). NM-TRAN does not reject these - it reads "
        "them as 0, so they enter the fit as genuine zero concentrations. Recode to a numeric "
        "value plus a BLQ flag column and choose an M-method.",
    ),
    ("neg_time", "error", "negative TIME", "TIME before zero without --allow-negative-time"),
    ("neg_conc", "warning", "negative DV", "negative concentrations in observation records"),
    ("bad_evid", "error", "invalid EVID", f"EVID outside {sorted(EVID_MEANINGS)}"),
    ("dose_without_amt", "error", "dose without AMT", "EVID marks a dose but AMT is missing or not positive"),
    (
        "obs_with_amt",
        "warning",
        "observation carries AMT",
        "records marked as observations also carry a non-zero AMT; if EVID is dropped from $INPUT "
        "these become doses",
    ),
    ("obs_missing_dv", "error", "missing DV with MDV=0", "observation record has no DV but is not flagged MDV=1"),
    ("mdv_conflict", "warning", "MDV=1 with a DV present", "the observation will be ignored by the estimation"),
    ("rate_issues", "error", "invalid RATE", "RATE must be >0, or -1 (modelled duration), or -2 (modelled rate)"),
    ("ss_missing_ii", "error", "SS without II", "a steady-state record needs a positive II"),
    (
        "addl_missing_ii",
        "error",
        "ADDL without II",
        "ADDL repeats a dose every II; with no II the extra doses never happen",
    ),
    ("zero_ii", "error", "ADDL with II<=0", "II must be positive for ADDL to place additional doses"),
)


def _resolve_columns(columns: list[str], args: argparse.Namespace) -> _Cols:
    """Map the dataset header onto the NONMEM column roles (case-insensitive)."""
    lookup = {c.lower(): c for c in columns}
    return _Cols(
        lookup=lookup,
        id=lookup.get(args.id_column.lower()),
        time=lookup.get(args.time_column.lower()),
        dv=lookup.get(args.dv_column.lower()),
        amt=lookup.get(args.amt_column.lower()),
        evid=lookup.get("evid"),
        mdv=lookup.get("mdv"),
        rate=lookup.get("rate"),
        ss=lookup.get("ss"),
        ii=lookup.get("ii"),
        addl=lookup.get("addl"),
    )


def _check_required_columns(found: Findings, cols: _Cols, args: argparse.Namespace) -> None:
    """Flag missing ID/TIME/DV/AMT columns and an absent EVID column."""
    for required, name in ((cols.id, args.id_column), (cols.time, args.time_column), (cols.dv, args.dv_column)):
        if required is None:
            found.add("error", "required column", f"no '{name}' column; NONMEM cannot build a dataset without it")
    if cols.amt is None:
        found.add("error", "required column", "no AMT column: without it no dose is ever administered")
    if cols.evid is None:
        found.add(
            "warning",
            "EVID absent",
            "no EVID column. NONMEM then infers events from AMT, which works only if every dose "
            "record has AMT>0 and every observation has AMT=0 or missing. Supplying EVID is safer.",
        )


def _check_column_names(found: Findings, columns: list[str]) -> None:
    """Flag overly long or NM-TRAN-hostile column names."""
    long_names = [c for c in columns if len(c) > 20]
    if long_names:
        found.add("note", "column names", f"unusually long column name(s): {', '.join(long_names[:4])}")
    non_alnum = [c for c in columns if not c.replace("_", "").isalnum()]
    if non_alnum:
        found.add(
            "warning",
            "column names",
            f"column name(s) with characters NM-TRAN will reject in $INPUT: {', '.join(non_alnum[:6])}",
        )


def _record_kind(row: dict[str, str], cols: _Cols) -> tuple[str | None, float | None, bool, bool]:
    """Return (EVID text, AMT, is_dose, is_observation) for one record."""
    evid = (row.get(cols.evid) or "0").strip() if cols.evid else None
    amt = _num(row.get(cols.amt, "")) if cols.amt else None
    is_dose = (evid in {"1", "4"}) if cols.evid else bool(amt and amt > 0)
    is_obs = (evid == "0") if cols.evid else not is_dose
    return evid, amt, is_dose, is_obs


def _check_observation(
    index: int, row: dict[str, str], cols: _Cols, amt: float | None, issues: _RecordIssues
) -> None:
    """DV / MDV / AMT checks for a record that is an observation."""
    dv_raw = row.get(cols.dv, "") if cols.dv else ""
    dv_missing = _is_missing(dv_raw)
    value = _num(dv_raw)
    if not dv_missing and value is None:
        issues.bad_dv_text.append(index)
    if value is not None and value < 0:
        issues.neg_conc.append(index)
    mdv = (row.get(cols.mdv) or "0").strip() if cols.mdv else "0"
    if dv_missing and mdv != "1":
        issues.obs_missing_dv.append(index)
    if not dv_missing and mdv == "1":
        issues.mdv_conflict.append(index)
    if amt not in (None, 0.0):
        issues.obs_with_amt.append(index)


def _row_ii(row: dict[str, str], cols: _Cols) -> float | None:
    """The record's II as a number, or None when absent or unreadable."""
    return _num(row.get(cols.ii, "")) if cols.ii else None


def _check_rate(index: int, row: dict[str, str], cols: _Cols, issues: _RecordIssues) -> None:
    """RATE must be positive, -1 or -2 whenever it is given."""
    if not cols.rate or _is_missing(row.get(cols.rate, "")):
        return
    rate = _num(row.get(cols.rate, ""))
    if rate is None or (rate < 0 and rate not in (-1.0, -2.0)):
        issues.rate_issues.append(index)


def _check_steady_state(index: int, row: dict[str, str], cols: _Cols, issues: _RecordIssues) -> None:
    """A steady-state record needs a positive II."""
    if cols.ss and (row.get(cols.ss) or "0").strip() not in {"0", "", "."} and not _row_ii(row, cols):
        issues.ss_missing_ii.append(index)


def _check_addl(index: int, row: dict[str, str], cols: _Cols, issues: _RecordIssues) -> None:
    """ADDL needs a positive II to place the additional doses."""
    if not cols.addl or (_num(row.get(cols.addl, "")) or 0) <= 0:
        return
    ii = _row_ii(row, cols)
    if ii is None:
        issues.addl_missing_ii.append(index)
    elif ii <= 0:
        issues.zero_ii.append(index)


def _check_dosing_columns(index: int, row: dict[str, str], cols: _Cols, issues: _RecordIssues) -> None:
    """RATE / SS / ADDL / II consistency checks for one record."""
    _check_rate(index, row, cols, issues)
    _check_steady_state(index, row, cols, issues)
    _check_addl(index, row, cols, issues)


def _scan_records(
    rows: list[dict[str, str]], cols: _Cols, args: argparse.Namespace, found: Findings
) -> tuple[dict[str, list[tuple[int, dict[str, str]]]], _RecordIssues]:
    """Run every per-record check; return the rows grouped by subject plus the issues."""
    issues = _RecordIssues()
    subjects: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for index, row in enumerate(rows, start=2):  # header is line 1
        subject = (row.get(cols.id) or "").strip()
        subjects.setdefault(subject, []).append((index, row))

        evid, amt, is_dose, is_obs = _record_kind(row, cols)
        if cols.evid and evid not in EVID_MEANINGS and not _is_missing(evid):
            issues.bad_evid.append(index)

        time = _num(row.get(cols.time, ""))
        if time is None:
            found.add("error", "TIME not numeric", f"row {index}: TIME is {row.get(cols.time)!r}", [index])
        elif time < 0 and not args.allow_negative_time:
            issues.neg_time.append(index)

        if is_obs:
            _check_observation(index, row, cols, amt, issues)
        if is_dose and (amt is None or amt <= 0):
            issues.dose_without_amt.append(index)
        _check_dosing_columns(index, row, cols, issues)
    return subjects, issues


def _report_record_issues(found: Findings, issues: _RecordIssues) -> None:
    """Turn the collected per-record row lists into findings, in report order."""
    for name, severity, check, detail in _RECORD_FINDINGS:
        rows = getattr(issues, name)
        if rows:
            found.add(severity, check, detail, rows)


@dataclass
class _SubjectStats:
    """Per-subject tallies and the subjects that tripped each check."""

    no_obs: list[str] = field(default_factory=list)
    no_dose: list[str] = field(default_factory=list)
    unsorted: list[str] = field(default_factory=list)
    duplicated: list[str] = field(default_factory=list)
    first_not_dose: list[str] = field(default_factory=list)
    obs_counts: list[int] = field(default_factory=list)
    dose_counts: list[int] = field(default_factory=list)


def _count_subject_records(records: list[tuple[int, dict[str, str]]], cols: _Cols) -> tuple[list, int, int]:
    """Return ((time, row) pairs, observation count, dose count) for one subject."""
    times = []
    n_obs = n_dose = 0
    for index, row in records:
        times.append((_num(row.get(cols.time, "")), index))
        _, _, is_dose, is_obs = _record_kind(row, cols)
        if is_dose:
            n_dose += 1
        elif is_obs and not _is_missing(row.get(cols.dv, "")):
            n_obs += 1
    return times, n_obs, n_dose


def _tally_subject(
    stats: _SubjectStats, subject: str, records: list[tuple[int, dict[str, str]]], cols: _Cols
) -> None:
    """Update ``stats`` with one non-blank subject's counts and flags."""
    times, n_obs, n_dose = _count_subject_records(records, cols)
    stats.obs_counts.append(n_obs)
    stats.dose_counts.append(n_dose)
    if n_obs == 0:
        stats.no_obs.append(subject)
    if n_dose == 0:
        stats.no_dose.append(subject)
    numeric = [t for t, _ in times if t is not None]
    if any(b < a for a, b in zip(numeric, numeric[1:])):
        stats.unsorted.append(subject)
    if any(v > 1 for v in Counter(numeric).values()):
        stats.duplicated.append(subject)
    if not _record_kind(records[0][1], cols)[2]:
        stats.first_not_dose.append(subject)


def _scan_subjects(
    subjects: dict[str, list[tuple[int, dict[str, str]]]], cols: _Cols, found: Findings
) -> _SubjectStats:
    """Per-subject checks: observations, doses, TIME order, duplicates, first record."""
    stats = _SubjectStats()
    for subject, records in subjects.items():
        if subject == "":
            found.add("error", "blank ID", "records with an empty ID column", [r[0] for r in records])
            continue
        _tally_subject(stats, subject, records, cols)
    return stats


def _report_subject_findings(found: Findings, stats: _SubjectStats) -> None:
    """Turn the per-subject lists into findings."""
    if stats.no_obs:
        found.add(
            "error",
            "subject with no observations",
            f"{len(stats.no_obs)} subject(s) contribute no DV: {', '.join(stats.no_obs[:6])}. Their ETAs are drawn "
            "entirely from the prior and they inflate the apparent N of the analysis.",
        )
    if stats.no_dose:
        found.add(
            "error",
            "subject with no dose",
            f"{len(stats.no_dose)} subject(s) have observations but no dose: {', '.join(stats.no_dose[:6])}",
        )
    if stats.unsorted:
        found.add(
            "error",
            "TIME not sorted",
            f"{len(stats.unsorted)} subject(s) have out-of-order TIME: {', '.join(stats.unsorted[:6])}",
        )
    if stats.duplicated:
        found.add(
            "warning",
            "duplicate TIME within a subject",
            f"{len(stats.duplicated)} subject(s) have records sharing a timestamp: {', '.join(stats.duplicated[:6])}. "
            "NONMEM applies them in file order, so a dose and an observation at the same time give a "
            "pre-dose or post-dose value depending purely on which row came first.",
        )
    if stats.first_not_dose:
        found.add(
            "note",
            "first record is not a dose",
            f"{len(stats.first_not_dose)} subject(s) start with a non-dose record: {', '.join(stats.first_not_dose[:6])}. "
            "Fine for a pre-dose baseline; wrong if a dose is missing.",
        )


def _check_covariate(
    found: Findings, name: str, rows: list[dict[str, str]], cols: _Cols, args: argparse.Namespace
) -> None:
    """Missing / non-numeric / within-subject-varying checks for one covariate."""
    cov_col = cols.get(name)
    if cov_col is None:
        found.add("error", "covariate absent", f"--covariates names '{name}' but there is no such column")
        return
    missing_rows, non_numeric = [], []
    per_subject_values: dict[str, set[str]] = {}
    for index, row in enumerate(rows, start=2):
        raw = row.get(cov_col, "")
        subject = (row.get(cols.id) or "").strip()
        per_subject_values.setdefault(subject, set()).add(raw.strip())
        if _is_missing(raw):
            missing_rows.append(index)
        elif _num(raw) is None:
            non_numeric.append(index)
    if missing_rows:
        found.add(
            "error",
            f"covariate {name} missing",
            f"{len(missing_rows)} record(s) have no value. A blank or '.' is read as 0, not as "
            f"missing, so those records enter the covariate model with {name} = 0 - a 0 kg "
            "body weight, a 0 mL/min creatinine clearance - rather than being excluded.",
            missing_rows,
        )
    if non_numeric:
        found.add("error", f"covariate {name} non-numeric", "values NM-TRAN cannot read as numbers", non_numeric)
    varying = [s for s, values in per_subject_values.items() if len(values) > 1]
    if varying and name.lower() not in {t.lower() for t in args.time_varying}:
        found.add(
            "warning",
            f"covariate {name} varies within subject",
            f"{len(varying)} subject(s) have more than one value: {', '.join(varying[:6])}. "
            "If this is intended, list it in --time-varying; if not, the model will use whichever "
            "value is on the record being evaluated.",
        )


def _dataset_summary(n_rows: int, n_columns: int, n_subjects: int, stats: _SubjectStats) -> dict:
    """Headline counts reported alongside the findings."""
    obs_counts = stats.obs_counts
    return {
        "records": n_rows,
        "subjects": n_subjects,
        "observations": sum(obs_counts),
        "dose_records": sum(stats.dose_counts),
        "median_observations_per_subject": sorted(obs_counts)[len(obs_counts) // 2] if obs_counts else 0,
        "subjects_with_one_observation": sum(1 for c in obs_counts if c == 1),
        "columns": n_columns,
    }


def check_dataset(rows: list[dict[str, str]], args: argparse.Namespace) -> tuple[Findings, dict]:
    """Run every dataset check and return the findings plus a summary dict."""
    found = Findings()
    columns = list(rows[0].keys())
    cols = _resolve_columns(columns, args)

    _check_required_columns(found, cols, args)
    if not cols.id or not cols.time:
        return found, {}
    _check_column_names(found, columns)

    subjects, issues = _scan_records(rows, cols, args, found)
    _report_record_issues(found, issues)

    stats = _scan_subjects(subjects, cols, found)
    _report_subject_findings(found, stats)

    for name in args.covariates:
        _check_covariate(found, name, rows, cols, args)

    summary = _dataset_summary(len(rows), len(columns), len(subjects), stats)
    if summary["subjects"] and summary["observations"] / max(summary["subjects"], 1) < 2:
        found.add(
            "note",
            "sparse sampling",
            "fewer than two observations per subject on average. A structural model with an absorption "
            "phase is unlikely to be identifiable; consider fixing parameters from a richer study.",
        )
    return found, summary


# --------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description="Validate a population PK dataset against NONMEM/nlmixr2 data conventions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("--id-column", default="ID")
    parser.add_argument("--time-column", default="TIME")
    parser.add_argument("--dv-column", default="DV")
    parser.add_argument("--amt-column", default="AMT")
    parser.add_argument("--covariates", default="", help="comma-separated covariate columns to check")
    parser.add_argument("--time-varying", default="", help="covariates that are expected to change within a subject")
    parser.add_argument("--allow-negative-time", action="store_true")
    parser.add_argument(
        "--fail-on",
        choices=("note", "warning", "error"),
        default="error",
        help="lowest severity that makes the exit code 1 (default: error)",
    )
    parser.add_argument("--strict", action="store_true", help="shorthand for --fail-on warning")
    add_format_argument(parser)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Run."""
    args = build_parser().parse_args(argv)
    args.covariates = [c.strip() for c in args.covariates.split(",") if c.strip()]
    args.time_varying = [c.strip() for c in args.time_varying.split(",") if c.strip()]
    if args.strict:
        args.fail_on = "warning"

    rows = read_table(args.input)
    found, summary = check_dataset(rows, args)

    report = Report()
    for key, value in summary.items():
        report.scalar(key, value)
    if found.items:
        ordered = sorted(found.items, key=lambda i: -SEVERITY_ORDER[str(i["severity"])])
        report.table("dataset findings", ordered)
    else:
        report.table("dataset findings", [{"severity": "none", "check": "all checks passed", "detail": "", "n_records": 0, "example_rows": ""}])

    report.note(
        "This checks data conventions, not pharmacology. A dataset that passes can still be wrong: "
        "verify units, time origin, and that DV is the quantity the model predicts."
    )
    threshold = SEVERITY_ORDER[args.fail_on]
    for item in found.items:
        if SEVERITY_ORDER[str(item["severity"])] >= threshold:
            report.finding(f"[{item['severity']}] {item['check']}: {item['detail']}")
    return report.emit(args.format)


if __name__ == "__main__":
    raise SystemExit(main_wrapper(run))
