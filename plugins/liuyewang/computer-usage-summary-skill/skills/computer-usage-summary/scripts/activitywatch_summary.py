#!/usr/bin/env python3
"""Summarize local ActivityWatch window and AFK events without external access."""

import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

API = "http://127.0.0.1:5600/api/0"
URL_PATTERN = re.compile(r"(?:https?://|www\.|\b[\w.-]+\.(?:com|net|org|cn|io|app|dev)\b)", re.I)
BROWSER_APP_PATTERN = re.compile("(?:chrome|firefox|safari|edge|brave|arc|browser|\u6d4f\u89c8\u5668)", re.I)
BROWSER_TITLE_SUFFIXES = (
    re.compile(r"\s+-\s+Google Chrome(?:\s+-\s+.+)?$", re.I),
    re.compile(r"\s+-\s+(?:Doubao Browser|\u8c46\u5305\u6d4f\u89c8\u5668)$", re.I),
)
MEMORY_SUFFIX = re.compile(r"\s+-\s+\u5185\u5b58\u7528\u91cf\u9ad8\s+-\s+[\d.,]+\s*(?:MB|GB)", re.I)


def get_json(path):
    with urllib.request.urlopen(f"{API}{path}", timeout=30) as response:
        return json.load(response)


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds(value):
    return max(0.0, value.total_seconds())


def interval_seconds(intervals):
    return sum(seconds(right - left) for left, right in intervals)


def merge_intervals(intervals):
    merged = []
    for left, right in sorted(intervals):
        if right <= left:
            continue
        if not merged or left > merged[-1][1]:
            merged.append([left, right])
        elif right > merged[-1][1]:
            merged[-1][1] = right
    return [(left, right) for left, right in merged]


def overlap(start, end, intervals):
    return sum(
        seconds(min(end, right) - max(start, left))
        for left, right in intervals
        if left < end and right > start
    )


def safe_title(title):
    title = " ".join((title or "").split())
    return "[URL omitted]" if URL_PATTERN.search(title) else title[:160]


def normalize_title(title):
    title = unicodedata.normalize("NFKC", title or "")
    title = "".join(character for character in title if unicodedata.category(character) != "Cf")
    title = MEMORY_SUFFIX.sub("", " ".join(title.split()))
    for suffix in BROWSER_TITLE_SUFFIXES:
        title = suffix.sub("", title)
    return safe_title(title) or "(untitled)"


def format_duration(value):
    total = int(round(value))
    hours, remainder = divmod(total, 3600)
    minutes, seconds_value = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds_value:02}"


def safe_cell(value):
    """Prevent spreadsheet formula evaluation when a cell is pasted or imported."""
    text = str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


def resolve_timezone(requested=None):
    candidates = [requested] if requested else []
    localtime_path = os.path.realpath("/etc/localtime")
    if "/zoneinfo/" in localtime_path:
        candidates.append(localtime_path.split("/zoneinfo/", 1)[1])
    if not requested:
        candidates.append(os.environ.get("TZ"))
    for name in candidates:
        if not name:
            continue
        try:
            return ZoneInfo(name), name
        except ZoneInfoNotFoundError:
            if requested == name:
                raise ValueError(f"Unknown timezone: {name}") from None
    timezone = dt.datetime.now().astimezone().tzinfo
    return timezone, getattr(timezone, "key", None) or str(timezone)


def local_iso(value, timezone):
    return value.astimezone(timezone).isoformat()


def utc_offset_label(value):
    offset = parse_time(value).strftime("%z")
    return f"UTC{offset[:3]}:{offset[3:]}" if offset else "UTC"


def clip_event(event, start, end):
    event_start = max(parse_time(event["timestamp"]), start)
    event_end = min(
        parse_time(event["timestamp"]) + dt.timedelta(seconds=event.get("duration", 0)),
        end,
    )
    return event_start, event_end


def afk_intervals(events, start, end):
    longest = {}
    for event in events:
        status = event.get("data", {}).get("status")
        if status not in ("afk", "not-afk"):
            continue
        event_start, event_end = clip_event(event, start, end)
        if event_end <= event_start:
            continue
        key = (event_start, status)
        longest[key] = max(longest.get(key, event_start), event_end)
    active = merge_intervals(
        (event_start, event_end)
        for (event_start, status), event_end in longest.items()
        if status == "not-afk"
    )
    away = merge_intervals(
        (event_start, event_end)
        for (event_start, status), event_end in longest.items()
        if status == "afk"
    )
    return active, away


def window_entries(events, start, end):
    longest = {}
    for event in events:
        event_start, event_end = clip_event(event, start, end)
        if event_end <= event_start:
            continue
        data = event.get("data", {})
        app = data.get("app") or "Unknown"
        title = normalize_title(data.get("title", ""))
        key = (event_start, app, title)
        longest[key] = max(longest.get(key, event_start), event_end)
    return sorted(
        (event_start, event_end, app, title)
        for (event_start, app, title), event_end in longest.items()
    )


def count_sessions(intervals, gap_seconds=5):
    sessions = 0
    previous_end = None
    for event_start, event_end in sorted(intervals):
        if previous_end is None or event_start - previous_end > dt.timedelta(seconds=gap_seconds):
            sessions += 1
        previous_end = max(previous_end or event_end, event_end)
    return sessions


def aggregate_browser_pages(window_events, active_intervals, start, end, timezone):
    pages = defaultdict(lambda: {"active_seconds": 0.0, "events": []})
    for event_start, event_end, app, title in window_entries(window_events, start, end):
        if not BROWSER_APP_PATTERN.search(app):
            continue
        active = overlap(event_start, event_end, active_intervals)
        if active <= 0:
            continue
        item = pages[(app, title)]
        item["active_seconds"] += active
        item["events"].append((event_start, event_end))

    result = []
    for (app, title), value in pages.items():
        events = sorted(value["events"])
        result.append(
            {
                "app": app,
                "title": title,
                "foreground_sessions": count_sessions(events),
                "active_seconds": round(value["active_seconds"], 1),
                "first_seen": local_iso(events[0][0], timezone),
                "last_active": local_iso(max(event[1] for event in events), timezone),
                "source": "ActivityWatch foreground window title",
            }
        )
    result.sort(key=lambda item: item["active_seconds"], reverse=True)
    return result


def summarize_period(window_events, afk_events, start, end, timezone, timezone_name):
    active_intervals, away_intervals = afk_intervals(afk_events, start, end)
    coverage_intervals = merge_intervals(active_intervals + away_intervals)
    active_seconds = interval_seconds(active_intervals)
    coverage_seconds = interval_seconds(coverage_intervals)
    afk_seconds = max(0.0, coverage_seconds - active_seconds)
    absolute_period_seconds = seconds(
        end.astimezone(dt.timezone.utc) - start.astimezone(dt.timezone.utc)
    )
    period_seconds = min(absolute_period_seconds, 86400.0)
    active_seconds = min(active_seconds, period_seconds)
    coverage_seconds = min(coverage_seconds, period_seconds)
    afk_seconds = max(0.0, coverage_seconds - active_seconds)

    apps = defaultdict(lambda: {"active_seconds": 0.0, "events": []})
    timeline = []
    for event_start, event_end, app, title in window_entries(window_events, start, end):
        active = overlap(event_start, event_end, active_intervals)
        if active <= 0:
            continue
        item = apps[app]
        item["active_seconds"] += active
        item["events"].append((event_start, event_end))
        timeline.append(
            {
                "start": local_iso(event_start, timezone),
                "end": local_iso(event_end, timezone),
                "app": app,
                "title": title,
                "active_seconds": round(active, 1),
                "source": "ActivityWatch",
            }
        )

    summary_apps = []
    for app, value in apps.items():
        events = sorted(value["events"])
        summary_apps.append(
            {
                "app": app,
                "foreground_sessions": count_sessions(events),
                "active_seconds": round(value["active_seconds"], 1),
                "first_seen": local_iso(events[0][0], timezone),
                "last_active": local_iso(max(event[1] for event in events), timezone),
                "source": "ActivityWatch",
            }
        )
    summary_apps.sort(key=lambda item: item["active_seconds"], reverse=True)

    return {
        "date": start.astimezone(timezone).date().isoformat(),
        "timezone": timezone_name,
        "range_start": local_iso(start, timezone),
        "range_end": local_iso(end, timezone),
        "active_seconds": round(active_seconds, 1),
        "afk_seconds": round(afk_seconds, 1),
        "coverage_seconds": round(coverage_seconds, 1),
        "untracked_seconds": round(max(0.0, period_seconds - coverage_seconds), 1),
        "apps": summary_apps,
        "browser_pages": aggregate_browser_pages(
            window_events, active_intervals, start, end, timezone
        ),
        "timeline": sorted(timeline, key=lambda item: item["start"]),
        "source": "ActivityWatch",
    }


def table_data(summary, table):
    if table == "summary":
        return (
            ["metric", "value"],
            [
                ["timezone", summary["timezone"]],
                ["range_start", summary["range_start"]],
                ["range_end", summary["range_end"]],
                ["active_seconds", summary["active_seconds"]],
                ["active_duration", format_duration(summary["active_seconds"])],
                ["afk_seconds", summary["afk_seconds"]],
                ["afk_duration", format_duration(summary["afk_seconds"])],
                ["coverage_seconds", summary["coverage_seconds"]],
                ["untracked_seconds", summary["untracked_seconds"]],
                ["source", "ActivityWatch"],
            ],
        )
    if table == "daily":
        return (
            [
                "date",
                "active_seconds",
                "active_duration",
                "afk_seconds",
                "afk_duration",
                "coverage_seconds",
                "coverage_duration",
                "untracked_seconds",
                "untracked_duration",
                "timezone",
                "source",
            ],
            [
                [
                    day["date"],
                    day["active_seconds"],
                    format_duration(day["active_seconds"]),
                    day["afk_seconds"],
                    format_duration(day["afk_seconds"]),
                    day["coverage_seconds"],
                    format_duration(day["coverage_seconds"]),
                    day["untracked_seconds"],
                    format_duration(day["untracked_seconds"]),
                    day["timezone"],
                    "ActivityWatch",
                ]
                for day in summary.get("days", [summary])
            ],
        )
    if table == "apps":
        return (
            ["app", "foreground_sessions", "active_seconds", "active_duration", "first_seen", "last_active", "source"],
            [
                [
                    item["app"],
                    item["foreground_sessions"],
                    item["active_seconds"],
                    format_duration(item["active_seconds"]),
                    item["first_seen"],
                    item["last_active"],
                    item.get("source", "ActivityWatch"),
                ]
                for item in summary["apps"]
            ],
        )
    if table == "browser":
        return (
            ["browser", "title", "foreground_sessions", "active_seconds", "active_duration", "first_seen", "last_active", "source"],
            [
                [
                    item["app"],
                    item["title"],
                    item["foreground_sessions"],
                    item["active_seconds"],
                    format_duration(item["active_seconds"]),
                    item["first_seen"],
                    item["last_active"],
                    item.get("source", "ActivityWatch foreground window title"),
                ]
                for item in summary["browser_pages"]
            ],
        )
    return (
        ["start", "end", "app", "title", "active_seconds", "active_duration", "source"],
        [
            [
                item["start"],
                item["end"],
                item["app"],
                item["title"],
                item["active_seconds"],
                format_duration(item["active_seconds"]),
                item.get("source", "ActivityWatch"),
            ]
            for item in summary["timeline"]
        ],
    )


def render_rows(headers, rows, output_format):
    if output_format == "markdown":
        escaped = lambda value: safe_cell(value).replace("|", "\\|").replace("\n", " ")
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        ]
        lines.extend(
            "| " + " | ".join(escaped(value) for value in row) + " |"
            for row in rows
        )
        return "\n".join(lines)
    buffer = io.StringIO(newline="")
    writer = csv.writer(
        buffer,
        delimiter="\t" if output_format == "tsv" else ",",
        lineterminator="\n",
    )
    writer.writerow(headers)
    writer.writerows([[safe_cell(value) for value in row] for row in rows])
    return buffer.getvalue().rstrip("\n")


def render_report(summary, output_format):
    if output_format != "markdown":
        headers, rows = table_data(summary, "daily")
        return render_rows(headers, rows, output_format)

    parts = [
        "# Computer Usage Report",
        "",
        f"Timezone: {summary['timezone']} ({utc_offset_label(summary['range_start'])})",
        f"Range: {summary['range_start']} to {summary['range_end']}",
        "",
        "## Daily Overview",
        "",
    ]
    headers, rows = table_data(summary, "daily")
    parts.append(render_rows(headers, rows, "markdown"))
    for day in summary.get("days", [summary]):
        parts.extend(["", f"## {day['date']}", "", "### Applications", ""])
        headers, rows = table_data(day, "apps")
        parts.append(render_rows(headers, rows, "markdown"))
        parts.extend(["", "### Browser Foreground Pages", ""])
        headers, rows = table_data(day, "browser")
        parts.append(render_rows(headers, rows, "markdown"))
        parts.extend(["", "### Timeline", ""])
        headers, rows = table_data(day, "timeline")
        parts.append(render_rows(headers, rows, "markdown"))
    return "\n".join(parts)


def render_table(summary, output_format, table):
    if output_format == "json":
        return json.dumps(summary, ensure_ascii=False)
    if table == "report":
        return render_report(summary, output_format)
    headers, rows = table_data(summary, table)
    return render_rows(headers, rows, output_format)


def build_parser():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--date", help="Local date in YYYY-MM-DD format or 'today'")
    group.add_argument("--start", help="Inclusive local start date in YYYY-MM-DD format")
    parser.add_argument("--end", help="Inclusive local end date; required with --start")
    parser.add_argument("--timezone", help="IANA timezone name; defaults to the Mac system timezone")
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "tsv", "csv"),
        default="markdown",
        help="Output format; Markdown is the default and TSV is suitable for spreadsheets",
    )
    parser.add_argument(
        "--table",
        choices=("report", "summary", "daily", "apps", "browser", "timeline"),
        default="report",
        help="Table to render; report produces the complete Markdown report",
    )
    parser.add_argument(
        "--min-tab-seconds",
        type=float,
        default=0.0,
        help="Hide browser pages below this foreground duration; default 0 includes every observed page",
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


def filter_browser_pages(summary, minimum_seconds):
    summary["browser_pages"] = [
        item for item in summary["browser_pages"]
        if item["active_seconds"] >= minimum_seconds
    ]
    for day in summary.get("days", []):
        day["browser_pages"] = [
            item for item in day["browser_pages"]
            if item["active_seconds"] >= minimum_seconds
        ]


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        timezone, timezone_name = resolve_timezone(args.timezone)
        start_day, end_day = date_range(args, timezone)
    except ValueError as error:
        parser.error(str(error))

    local_start = dt.datetime.combine(start_day, dt.time.min, timezone)
    local_end = dt.datetime.combine(end_day + dt.timedelta(days=1), dt.time.min, timezone)
    query_start = local_start.astimezone(dt.timezone.utc)
    query_end = local_end.astimezone(dt.timezone.utc)
    query = urllib.parse.urlencode(
        {"starttime": query_start.isoformat(), "endtime": query_end.isoformat()}
    )
    try:
        buckets = get_json("/buckets/")
        window_id = next(
            key for key, value in buckets.items() if value.get("type") == "currentwindow"
        )
        afk_id = next(
            key for key, value in buckets.items() if value.get("type") == "afkstatus"
        )
        window_events = get_json(
            f"/buckets/{urllib.parse.quote(window_id, safe='')}/events?{query}"
        )
        afk_events = get_json(
            f"/buckets/{urllib.parse.quote(afk_id, safe='')}/events?{query}"
        )
    except (OSError, StopIteration, ValueError) as error:
        print(json.dumps({"available": False, "reason": str(error)}))
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

    filter_browser_pages(summary, max(0.0, args.min_tab_seconds))
    result = render_table(summary, args.format, args.table)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as file:
            file.write(result)
    else:
        print(result, end="" if result.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
