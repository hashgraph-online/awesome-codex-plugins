"""JSON, Markdown, TSV, and CSV rendering."""

import csv
import io
import json

from .intervals import utc_offset_label
from .models import format_duration, safe_cell


def _unavailable_rows(summary):
    return (
        ["status", "reason", "source"],
        [["unavailable", summary.get("reason", "unknown"), summary.get("source", "ActivityWatch")]],
    )


def table_data(summary, table):
    if not summary.get("available", True):
        return _unavailable_rows(summary)
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
                ["main_focus", summary.get("main_focus", "unknown context")],
                ["source", "ActivityWatch"],
            ],
        )
    if table == "daily":
        headers = [
            "date", "active_seconds", "active_duration",
            "afk_seconds", "afk_duration", "coverage_seconds", "coverage_duration",
            "untracked_seconds", "untracked_duration", "timezone", "source",
            "first_seen", "last_active", "main_focus",
        ]
        rows = []
        days = summary.get("days", [summary])
        for day in days:
            rows.append(
                [
                    day["date"], day["active_seconds"], format_duration(day["active_seconds"]),
                    day["afk_seconds"], format_duration(day["afk_seconds"]),
                    day["coverage_seconds"], format_duration(day["coverage_seconds"]),
                    day["untracked_seconds"], format_duration(day["untracked_seconds"]),
                    day["timezone"], "ActivityWatch", day.get("first_seen"),
                    day.get("last_active"), day.get("main_focus", "unknown context"),
                ]
            )
        if len(days) > 1:
            rows.append(
                [
                    "TOTAL", summary["active_seconds"], format_duration(summary["active_seconds"]),
                    summary["afk_seconds"], format_duration(summary["afk_seconds"]),
                    summary["coverage_seconds"], format_duration(summary["coverage_seconds"]),
                    summary["untracked_seconds"], format_duration(summary["untracked_seconds"]),
                    summary["timezone"], "ActivityWatch", summary.get("first_seen"),
                    summary.get("last_active"), summary.get("main_focus", "unknown context"),
                ]
            )
        return headers, rows
    if table == "categories":
        return (
            ["category", "active_seconds", "active_duration", "top_apps", "source"],
            [
                [
                    item["category"], item["active_seconds"], item["active_duration"],
                    ", ".join(item["top_apps"]), item.get("source", "ActivityWatch"),
                ]
                for item in summary.get("category_summary", [])
            ],
        )
    if table == "apps":
        return (
            ["app", "foreground_sessions", "active_seconds", "active_duration", "first_seen", "last_active", "source", "category"],
            [
                [
                    item["app"], item["foreground_sessions"],
                    item["active_seconds"], format_duration(item["active_seconds"]),
                    item["first_seen"], item["last_active"], item.get("source", "ActivityWatch"),
                    item.get("category", "other"),
                ]
                for item in summary["apps"]
            ],
        )
    if table == "browser":
        return (
            ["browser", "title", "foreground_sessions", "active_seconds", "active_duration", "first_seen", "last_active", "source", "category", "confidence"],
            [
                [
                    item["app"], item["title"], item["foreground_sessions"], item["active_seconds"], format_duration(item["active_seconds"]),
                    item["first_seen"], item["last_active"], item.get("source", "ActivityWatch foreground window title"),
                    item.get("category", "other"), item.get("confidence", "unknown context"),
                ]
                for item in summary["browser_pages"]
            ],
        )
    return (
        ["start", "end", "app", "title", "active_seconds", "active_duration", "source", "category", "confidence"],
        [
            [
                item["start"], item["end"], item["app"], item["title"], item["active_seconds"], format_duration(item["active_seconds"]),
                item.get("source", "ActivityWatch"),
                item.get("category", "other"), item.get("confidence", "unknown context"),
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


def _caveats():
    return [
        "Foreground sessions are observed intervals, not application launch counts.",
        "First-to-last spans are observation windows and may contain gaps.",
        "Tracking covers only periods when ActivityWatch was running.",
        "Browser data covers foreground titles only and does not come from browser history.",
    ]


def render_report(summary, output_format):
    if output_format != "markdown":
        headers, rows = table_data(summary, "daily")
        return render_rows(headers, rows, output_format)
    if not summary.get("available", True):
        parts = [
            "# Computer Usage Report", "",
            f"Timezone: {summary.get('timezone', 'unknown')} ({utc_offset_label(summary['range_start'])})",
            f"Range: {summary.get('range_start', 'unknown')} to {summary.get('range_end', 'unknown')}",
            "", "## Status", "",
        ]
        headers, rows = _unavailable_rows(summary)
        parts.append(render_rows(headers, rows, "markdown"))
        parts.extend(["", "## Caveats", ""])
        parts.extend(f"- {item}" for item in _caveats())
        return "\n".join(parts)

    parts = [
        "# Computer Usage Report", "",
        f"Timezone: {summary['timezone']} ({utc_offset_label(summary['range_start'])})",
        f"Range: {summary['range_start']} to {summary['range_end']}", "",
        "## Daily Overview", "",
    ]
    headers, rows = table_data(summary, "daily")
    parts.append(render_rows(headers, rows, "markdown"))
    for day in summary.get("days", [summary]):
        parts.extend(["", f"## {day['date']}", "", "### What You Did", ""])
        headers, rows = table_data(day, "categories")
        parts.append(render_rows(headers, rows, "markdown"))
        parts.extend(["", "### Applications", ""])
        headers, rows = table_data(day, "apps")
        parts.append(render_rows(headers, rows, "markdown"))
        parts.extend(["", "### Browser Foreground Pages", ""])
        headers, rows = table_data(day, "browser")
        parts.append(render_rows(headers, rows, "markdown"))
        short = day.get("browser_short_visits", {})
        parts.extend(
            [
                "", "### Short Browser Visits", "",
                (
                    f"Omitted {short.get('count', 0)} page groups below "
                    f"{short.get('threshold_seconds', 0)} seconds; "
                    f"total foreground time {short.get('active_duration', '00:00:00')}."
                ),
            ]
        )
        parts.extend(["", "### Timeline", ""])
        headers, rows = table_data(day, "timeline")
        parts.append(render_rows(headers, rows, "markdown"))
    parts.extend(["", "## Caveats", ""])
    parts.extend(f"- {item}" for item in _caveats())
    return "\n".join(parts)


def render_table(summary, output_format, table):
    if output_format == "json":
        return json.dumps(summary, ensure_ascii=False)
    if table == "report":
        return render_report(summary, output_format)
    headers, rows = table_data(summary, table)
    return render_rows(headers, rows, output_format)
