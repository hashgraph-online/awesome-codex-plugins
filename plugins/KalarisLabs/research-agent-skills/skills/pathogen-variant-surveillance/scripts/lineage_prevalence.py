#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Weekly prevalence of one or more lineages, with intervals and a coverage flag.

Answers "what is circulating, and is it growing" from live sequence counts
rather than from memory. Every number is a count returned by the instance at
the data version printed in the provenance block.

    python3 lineage_prevalence.py XFG.1.1 XFJ.3 --instance sars-cov-2 --where country=USA
    python3 lineage_prevalence.py XFG --sublineages --weeks 12 --growth
    python3 lineage_prevalence.py 2.3.4.4b --instance h5n1 --where country=USA --weeks 52

Proportions carry Wilson intervals because surveillance weeks are small, and
recent weeks are flagged ``low`` when their denominator has not filled in yet
-- see reporting_lag.py for the measured filling-in curve.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from lapis_client import (
    LapisError,
    aggregated,
    bin_weekly,
    count,
    data_version,
    describe_instance,
    emit,
    flag_low_coverage,
    lineage_filter,
    logit_slope,
    pick_date_field,
    pick_lineage_field,
    range_keys,
    resolve_base_url,
    top_values,
    week_range,
    wilson_interval,
)

COLUMNS = (
    "lineage",
    "week",
    "n",
    "total",
    "proportion",
    "ci_low",
    "ci_high",
    "coverage",
)


def _field_base(key: str, types: dict) -> str:
    """Strip a range suffix (``From``/``To``) when the remainder is a known field."""
    base = key.split(".")[0]
    for suffix in ("From", "To"):
        if base.endswith(suffix) and base[: -len(suffix)] in types:
            return base[: -len(suffix)]
    return base


def parse_where(pairs: list[str], schema: dict) -> dict[str, str]:
    """Turn ``KEY=VALUE`` arguments into filters, checking keys against the schema."""
    filters: dict[str, str] = {}
    types = schema.get("types", {})
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            raise LapisError(f"--where expects KEY=VALUE, got {pair!r}")
        base = _field_base(key, types)
        if base not in types:
            near = sorted(n for n in types if base.lower() in n.lower())
            hint = f" Did you mean: {', '.join(near[:6])}?" if near else ""
            raise LapisError(f"{key!r} is not a field on this instance.{hint}")
        filters[key] = value
    return filters


def weekly_counts(
    base_url: str, filters: dict, date_field: str, weeks: list[str]
) -> tuple[dict[str, int], int]:
    """Weekly counts over the requested window, zero-filled for empty weeks."""
    rows = aggregated(base_url, filters, [date_field])
    binned, undated = bin_weekly(rows, date_field)
    return {week: binned.get(week, 0) for week in weeks}, undated


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description="Weekly lineage prevalence from a LAPIS instance.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("lineages", nargs="*",
                        help="lineage or clade names; 'NAME*' includes descendants. "
                             "Omit to discover them with --top")
    parser.add_argument("--top", type=int, metavar="N",
                        help="discover the N most common lineages in the window instead of "
                             "naming them (default when no names are given)")
    parser.add_argument("--instance", default="sars-cov-2", help="registry name (default: sars-cov-2)")
    parser.add_argument("--base-url", help="any other LAPIS deployment")
    parser.add_argument("--lineage-field", help="override the auto-detected lineage column")
    parser.add_argument("--date-field", help="override the auto-detected collection-date column")
    parser.add_argument("--where", action="append", default=[], metavar="KEY=VALUE",
                        help="extra filter, repeatable (e.g. --where country=USA)")
    parser.add_argument("--weeks", type=int, default=26, help="window length in weeks (default: 26)")
    parser.add_argument("--since", help="window start, YYYY-MM-DD; overrides --weeks")
    parser.add_argument("--until", help="window end, YYYY-MM-DD (default: today)")
    parser.add_argument("--sublineages", action="store_true", help="include descendant lineages")
    parser.add_argument("--growth", action="store_true",
                        help="also fit a weighted log-odds slope over the trusted weeks")
    parser.add_argument("--include-incomplete", action="store_true",
                        help="let low-coverage weeks into the growth fit")
    parser.add_argument("--coverage-fraction", type=float, default=0.4,
                        help="flag weeks below this fraction of the settled median (default: 0.4)")
    parser.add_argument("--format", choices=("table", "tsv", "json"), default="table")
    parser.add_argument("-o", "--output", help="write to a file instead of stdout")
    return parser


def _requested_window(args: argparse.Namespace) -> tuple[date, date]:
    """Resolve the requested (since, until) dates from --since/--until/--weeks."""
    requested_until = date.fromisoformat(args.until) if args.until else date.today()
    requested_since = (
        date.fromisoformat(args.since)
        if args.since
        else requested_until - timedelta(weeks=max(1, args.weeks))
    )
    return requested_since, requested_until


def _window_error(args: argparse.Namespace, since: date, until: date) -> str | None:
    """Return the error message for an invalid window or --top value, if any."""
    if since > until:
        return "error: --since is after --until"
    if args.top is not None and args.top < 1:
        return "error: --top must be at least 1"
    return None


def _discover_targets(
    args: argparse.Namespace,
    ctx: dict,
    notes: list[str],
) -> list[str] | None:
    """Return the lineages to report, discovering the top ones when none are named.

    Returns None (after printing an error) when discovery finds no sequences.
    """
    targets = list(args.lineages)
    if args.top is None and targets:
        return targets
    wanted = args.top or 10
    lineage_field = ctx["lineage_field"]
    discovered = top_values(
        aggregated(ctx["base_url"], ctx["window"], [lineage_field]), lineage_field, wanted
    )
    if not discovered:
        where = ctx["where"]
        print(
            f"error: no sequences in {ctx['since']} to {ctx['until']}"
            + (f" with {where}" if where else "")
            + ". Widen the window or relax the filters.",
            file=sys.stderr,
        )
        return None
    notes.append(
        f"discovered the {len(discovered)} most common {lineage_field} "
        f"value{'s' if len(discovered) != 1 else ''} in the window: "
        f"{', '.join(discovered)}"
    )
    return discovered + [t for t in targets if t not in discovered]


def _descendant_note(ctx: dict, value: str) -> str | None:
    """Note when a lineage has descendants that an exact-name query leaves out."""
    # Both sides must come from the same kind of query. Summing the
    # weekly bins would drop sequences with no usable collection
    # date, making every lineage that has some look as though it had
    # descendants it does not.
    base_url, window, lineage_field = ctx["base_url"], ctx["window"], ctx["lineage_field"]
    exact = count(base_url, {**window, lineage_field: value})
    inclusive = count(base_url, {**window, lineage_field: f"{value}*"})
    if inclusive > exact:
        return (
            f"{value}: {exact} sequences named exactly {value}, "
            f"{inclusive} including descendants. Pass --sublineages "
            f"or write '{value}*' for the second number."
        )
    return None


def _prevalence_rows(
    value: str, weeks: list[str], counts: dict, totals: dict, coverage: dict
) -> list[dict]:
    """Build one table row per week with proportion and Wilson interval."""
    rows: list[dict] = []
    for week in weeks:
        k, n = counts[week], totals[week]
        low, high = wilson_interval(k, n)
        rows.append(
            {
                "lineage": value,
                "week": week,
                "n": k,
                "total": n,
                "proportion": f"{(k / n):.4f}" if n else "",
                "ci_low": f"{low:.4f}" if n else "",
                "ci_high": f"{high:.4f}" if n else "",
                "coverage": "low" if coverage.get(week) else "ok",
            }
        )
    return rows


def _growth_fit(
    args: argparse.Namespace,
    value: str,
    weeks: list[str],
    counts: dict,
    totals: dict,
    coverage: dict,
) -> tuple[dict | None, str | None]:
    """Fit the log-odds slope; return (fit, None) or (None, explanatory note)."""
    usable = [
        (i, counts[w], totals[w])
        for i, w in enumerate(weeks)
        if args.include_incomplete or not coverage.get(w)
    ]
    fit = logit_slope([(float(t), k, n) for t, k, n in usable])
    if fit:
        return fit, None
    return None, (
        f"{value}: too few observations for a growth estimate "
        f"({sum(k for _, k, _ in usable)} sequences across "
        f"{sum(1 for _, k, _ in usable if k > 0)} non-empty weeks). "
        "No slope is reported rather than a slope driven by the denominator."
    )


def _collect_results(
    args: argparse.Namespace,
    ctx: dict,
    totals: dict,
    coverage: dict,
    notes: list[str],
) -> tuple[list[dict], dict[str, dict]] | None:
    """Query every target lineage; return (rows, fits) or None when discovery failed."""
    targets = _discover_targets(args, ctx, notes)
    if targets is None:
        return None
    rows: list[dict] = []
    fits: dict[str, dict] = {}
    weeks = ctx["weeks"]
    for name in targets:
        value = lineage_filter(name, ctx["has_index"], args.sublineages)
        counts, _ = weekly_counts(
            ctx["base_url"],
            {**ctx["window"], ctx["lineage_field"]: value},
            ctx["date_field"],
            weeks,
        )
        if ctx["has_index"] and not value.endswith("*"):
            note = _descendant_note(ctx, value)
            if note:
                notes.append(note)
        rows.extend(_prevalence_rows(value, weeks, counts, totals, coverage))
        if args.growth:
            fit, note = _growth_fit(args, value, weeks, counts, totals, coverage)
            if fit:
                fits[value] = fit
            else:
                notes.append(note)
    return rows, fits


def _json_payload(
    ctx: dict, version: str, undated: int, notes: list[str], rows: list[dict], fits: dict
) -> str:
    """Serialise the JSON report with its provenance metadata."""
    import json

    payload = {
        "meta": {
            "instance": ctx["schema"]["name"],
            "base_url": ctx["base_url"],
            "data_version": version,
            "lineage_field": ctx["lineage_field"],
            "lineage_index": ctx["has_index"],
            "date_field": ctx["date_field"],
            "window": [ctx["since"].isoformat(), ctx["until"].isoformat()],
            "filters": ctx["where"],
            "undated_sequences": undated,
            "notes": notes,
        },
        "rows": rows,
        "growth": fits,
    }
    return json.dumps(payload, indent=2)


def _print_footer(
    ctx: dict,
    version: str,
    undated: int,
    notes: list[str],
    coverage: dict,
    fits: dict,
    requested: tuple[date, date],
) -> None:
    """Print the stderr provenance, notes, coverage and growth footer."""
    schema, base_url, where = ctx["schema"], ctx["base_url"], ctx["where"]
    since, until = ctx["since"], ctx["until"]
    snapped = (since, until) != requested
    print(
        f"\n# {schema['name']} via {base_url}"
        f"\n# data version {version} | {ctx['lineage_field']}"
        f"{' (lineage-indexed)' if ctx['has_index'] else ' (no lineage index)'}"
        f" | dates from {ctx['date_field']}"
        f"\n# window {since} to {until}"
        + (f" (widened from {requested[0]}..{requested[1]} to whole ISO weeks)"
           if snapped else "")
        + (f" | filters {where}" if where else "")
        + (f"\n# {undated} matching sequences carry no usable collection date" if undated else ""),
        file=sys.stderr,
    )
    for note in notes:
        print(f"# note: {note}", file=sys.stderr)
    if any(coverage.values()):
        flagged = [w for w, bad in coverage.items() if bad]
        print(
            f"# {len(flagged)} week(s) flagged low: denominator still filling in "
            f"(earliest {min(flagged)}). Treat their proportions as unstable.",
            file=sys.stderr,
        )
    for name, fit in fits.items():
        print(
            f"# growth {name}: log-odds slope {fit['slope_per_week']:+.3f}/week "
            f"(95% CI {fit['ci_low']:+.3f} to {fit['ci_high']:+.3f}, "
            f"{int(fit['n_weeks'])} weeks, dispersion {fit['dispersion']:.1f}). "
            f"Descriptive only -- confounded by sampling and reporting changes.",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args(argv)

    try:
        base_url = resolve_base_url(args.instance, args.base_url)
        schema = describe_instance(base_url)
        lineage_field, has_index = pick_lineage_field(schema, args.lineage_field)
        date_field = pick_date_field(schema, "collection", args.date_field)
        where = parse_where(args.where, schema)
    except LapisError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    requested_since, requested_until = _requested_window(args)
    window_error = _window_error(args, requested_since, requested_until)
    if window_error:
        print(window_error, file=sys.stderr)
        return 2

    # Snap both ends to ISO week boundaries. A window that starts mid-week gives
    # a first row covering three days and a last row covering four, and neither
    # is comparable to the full weeks between them -- exactly the kind of
    # silently uneven denominator this skill exists to prevent. Widening to whole
    # weeks keeps every row meaning the same thing; a still-unfilled final week
    # shows up through the coverage flag rather than as a short bar.
    since = requested_since - timedelta(days=requested_since.weekday())
    until = requested_until + timedelta(days=6 - requested_until.weekday())

    from_key, to_key = range_keys(date_field)
    window = {from_key: since.isoformat(), to_key: until.isoformat(), **where}
    weeks = week_range(since.isoformat(), until.isoformat())
    ctx = {
        "base_url": base_url,
        "schema": schema,
        "lineage_field": lineage_field,
        "has_index": has_index,
        "date_field": date_field,
        "where": where,
        "since": since,
        "until": until,
        "window": window,
        "weeks": weeks,
    }

    notes: list[str] = []
    try:
        version = data_version(base_url)
        totals, undated = weekly_counts(base_url, window, date_field, weeks)
        coverage = flag_low_coverage(totals, args.coverage_fraction)
        results = _collect_results(args, ctx, totals, coverage, notes)
        if results is None:
            return 1
        rows, fits = results
    except LapisError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        text = _json_payload(ctx, version, undated, notes, rows, fits)
    else:
        text = emit(rows, COLUMNS, args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)

    sys.stdout.flush()
    if args.format != "json":
        _print_footer(
            ctx, version, undated, notes, coverage, fits,
            (requested_since, requested_until),
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
