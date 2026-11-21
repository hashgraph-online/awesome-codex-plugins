"""Command-line orchestration for the ActivityWatch report skill."""

import argparse
import datetime as dt
import math
import sys

from .intervals import resolve_timezone
from .models import DEFAULT_BROWSER_THRESHOLD
from .render import render_table
from .reports import filter_browser_pages, summarize_period
from .source import API, ActivityWatchUnavailable, fetch_events


def nonnegative_finite_float(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("must be a finite non-negative number") from error
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("must be a finite non-negative number")
    return parsed


def build_parser():
    parser = argparse.ArgumentParser(
        description="Summarize local ActivityWatch foreground and AFK events."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--date", help="Local date in YYYY-MM-DD format or 'today'")
    group.add_argument("--start", help="Inclusive local start date in YYYY-MM-DD format")
    parser.add_argument("--end", help="Inclusive local end date; required with --start")
    parser.add_argument(
        "--timezone",
        help="IANA timezone name; defaults to the Mac system timezone",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "tsv", "csv"),
        default="markdown",
        help="Output format; Markdown is the default and TSV is suitable for spreadsheets",
    )
    parser.add_argument(
        "--table",
        choices=("report", "summary", "daily", "categories", "apps", "browser", "timeline"),
        default="report",
        help="Table to render; report produces the complete Markdown report",
    )
    parser.add_argument(
        "--min-tab-seconds",
        type=nonnegative_finite_float,
        default=DEFAULT_BROWSER_THRESHOLD,
        help="Display browser pages at or above this foreground duration; default 120",
    )
    parser.add_argument("--output", help="Optional UTF-8 file path; otherwise write to standard output")
    return parser


def date_range(args, timezone):
    if args.start:
        if not args.end:
            raise ValueError("--end is required with --start")
        start_day = dt.date.fromisoformat(args.start)
        end_day = dt.date.fromisoformat(args.end)
    else:
        start_day = (
            dt.datetime.now(timezone).date()
            if args.date in (None, "today")
            else dt.date.fromisoformat(args.date)
        )
        end_day = start_day
    if end_day < start_day:
        raise ValueError("--end must not precede --start")
    return start_day, end_day


def _write_result(result, output_path):
    if output_path:
        with open(output_path, "w", encoding="utf-8", newline="") as file:
            file.write(result)
    else:
        print(result, end="" if result.endswith("\n") else "\n")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        timezone, timezone_name = resolve_timezone(args.timezone)
        start_day, end_day = date_range(args, timezone)
    except (ValueError, OverflowError) as error:
        parser.error(str(error))

    local_start = dt.datetime.combine(start_day, dt.time.min, timezone)
    local_end = dt.datetime.combine(end_day + dt.timedelta(days=1), dt.time.min, timezone)
    try:
        window_events, afk_events = fetch_events(local_start, local_end, API)
    except ActivityWatchUnavailable as error:
        summary = {
            "available": False,
            "reason": str(error),
            "source": "ActivityWatch",
            "timezone": timezone_name,
            "range_start": local_start.isoformat(),
            "range_end": local_end.isoformat(),
        }
        try:
            _write_result(render_table(summary, args.format, args.table), args.output)
        except OSError as output_error:
            parser.error(str(output_error))
        return 1

    summary = summarize_period(
        window_events,
        afk_events,
        local_start,
        local_end,
        timezone,
        timezone_name,
    )
    summary["available"] = True
    summary["days"] = []
    day = start_day
    while day <= end_day:
        day_start = dt.datetime.combine(day, dt.time.min, timezone)
        day_end = dt.datetime.combine(day + dt.timedelta(days=1), dt.time.min, timezone)
        summary["days"].append(
            summarize_period(
                window_events,
                afk_events,
                day_start,
                day_end,
                timezone,
                timezone_name,
            )
        )
        day += dt.timedelta(days=1)

    filter_browser_pages(summary, args.min_tab_seconds)
    try:
        _write_result(render_table(summary, args.format, args.table), args.output)
    except OSError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
