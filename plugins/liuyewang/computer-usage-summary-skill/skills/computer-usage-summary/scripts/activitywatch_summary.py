#!/usr/bin/env python3
"""Create privacy-preserving local ActivityWatch summaries and reports."""

import argparse
import csv
import datetime as dt
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_API = "http://127.0.0.1:5600/api/0"
URL_PATTERN = re.compile(r"(?:https?://|www\.|\b[\w.-]+\.(?:com|net|org|cn|io|app|dev)\b)", re.I)
MAX_TITLE_LENGTH = 160
DEFAULT_ATTRIBUTES = {
    "project": "Unassigned",
    "client": "",
    "category": "Uncategorized",
    "billable": False,
}


class ActivityWatchUnavailable(RuntimeError):
    """Raised when accurate local ActivityWatch data cannot be retrieved."""


class RulesConfigurationError(ValueError):
    """Raised when a local rules file is malformed or unsafe to use."""


def get_json(path, api=DEFAULT_API):
    with urllib.request.urlopen(f"{api}{path}", timeout=5) as response:
        return json.load(response)


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def seconds(value):
    return max(0.0, value.total_seconds())


def resolve_timezone(value):
    if value:
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"unknown IANA time zone: {value}") from error
    return dt.datetime.now().astimezone().tzinfo


def timezone_name(timezone):
    return getattr(timezone, "key", None) or str(timezone)


def safe_title(title):
    title = " ".join((title or "").split())
    return "[URL omitted]" if URL_PATTERN.search(title) else title[:MAX_TITLE_LENGTH]


def format_duration(value):
    total = int(round(value))
    hours, remainder = divmod(total, 3600)
    minutes, seconds_value = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds_value:02}"


def safe_cell(value):
    """Prevent spreadsheet formula evaluation when a cell is pasted or imported."""
    text = str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


def parse_date_range(date_value, start_value, end_value, period, timezone):
    if start_value:
        if not end_value:
            raise ValueError("--end is required with --start")
        start_day = dt.date.fromisoformat(start_value)
        end_day = dt.date.fromisoformat(end_value)
    else:
        anchor = dt.datetime.now(timezone).date() if date_value in (None, "today") else dt.date.fromisoformat(date_value)
        if period == "week":
            start_day = anchor - dt.timedelta(days=anchor.weekday())
            end_day = start_day + dt.timedelta(days=6)
        elif period == "month":
            start_day = anchor.replace(day=1)
            following_month = (start_day.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
            end_day = following_month - dt.timedelta(days=1)
        else:
            start_day = anchor
            end_day = anchor
    if end_day < start_day:
        raise ValueError("--end must not precede --start")
    return start_day, end_day


def load_rules(path):
    if not path:
        return {"defaults": dict(DEFAULT_ATTRIBUTES), "rules": []}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RulesConfigurationError(f"Rules file is unavailable or invalid JSON: {error}") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("rules", []), list):
        raise RulesConfigurationError("Rules file must be an object with a 'rules' array.")
    defaults = dict(DEFAULT_ATTRIBUTES)
    supplied_defaults = payload.get("defaults", {})
    if not isinstance(supplied_defaults, dict):
        raise RulesConfigurationError("Rules 'defaults' must be an object.")
    for key in DEFAULT_ATTRIBUTES:
        if key in supplied_defaults:
            defaults[key] = supplied_defaults[key]
    if not isinstance(defaults["billable"], bool):
        raise RulesConfigurationError("Rules 'billable' values must be true or false.")
    rules = []
    for index, rule in enumerate(payload["rules"], start=1):
        if not isinstance(rule, dict):
            raise RulesConfigurationError(f"Rule {index} must be an object.")
        if not rule.get("app") and not rule.get("app_pattern") and not rule.get("title_pattern"):
            raise RulesConfigurationError(f"Rule {index} needs app, app_pattern, or title_pattern.")
        for key in ("app_pattern", "title_pattern"):
            if key in rule:
                if not isinstance(rule[key], str):
                    raise RulesConfigurationError(f"Rule {index} {key} must be a string.")
                try:
                    re.compile(rule[key], re.I)
                except re.error as error:
                    raise RulesConfigurationError(f"Rule {index} has an invalid {key}: {error}") from error
        if "billable" in rule and not isinstance(rule["billable"], bool):
            raise RulesConfigurationError(f"Rule {index} billable must be true or false.")
        rules.append(rule)
    return {"defaults": defaults, "rules": rules}


def attributes_for(app, title, rules):
    attributes = dict(rules["defaults"])
    for rule in rules["rules"]:
        matches = True
        if "app" in rule:
            matches = matches and app == rule["app"]
        if "app_pattern" in rule:
            matches = matches and bool(re.search(rule["app_pattern"], app, re.I))
        if "title_pattern" in rule:
            matches = matches and bool(re.search(rule["title_pattern"], title, re.I))
        if matches:
            for key in DEFAULT_ATTRIBUTES:
                if key in rule:
                    attributes[key] = rule[key]
            break
    return attributes


def intersect_intervals(start, end, intervals):
    return [(max(start, right_start), min(end, right_end)) for right_start, right_end in intervals if right_start < end and right_end > start]


def day_chunks(start, end, timezone):
    current = start
    while current < end:
        local_day = current.astimezone(timezone).date()
        next_day = dt.datetime.combine(local_day + dt.timedelta(days=1), dt.time.min, timezone).astimezone(dt.timezone.utc)
        chunk_end = min(end, next_day)
        yield local_day.isoformat(), current, chunk_end
        current = chunk_end


def add_aggregate(target, key, active_seconds, billable):
    item = target[key]
    item["active_seconds"] += active_seconds
    if billable:
        item["billable_seconds"] += active_seconds


def collect_summary(start_day, end_day, timezone, fetch=get_json, include_titles=True, rules=None):
    start = dt.datetime.combine(start_day, dt.time.min, timezone).astimezone(dt.timezone.utc)
    end = dt.datetime.combine(end_day + dt.timedelta(days=1), dt.time.min, timezone).astimezone(dt.timezone.utc)
    query = urllib.parse.urlencode({"starttime": start.isoformat(), "endtime": end.isoformat()})
    rules = rules or {"defaults": dict(DEFAULT_ATTRIBUTES), "rules": []}
    try:
        buckets = fetch("/buckets/")
        window_id = next(key for key, value in buckets.items() if value.get("type") == "currentwindow")
        afk_id = next(key for key, value in buckets.items() if value.get("type") == "afkstatus")
        window_events = fetch(f"/buckets/{urllib.parse.quote(window_id, safe='')}/events?{query}")
        afk_events = fetch(f"/buckets/{urllib.parse.quote(afk_id, safe='')}/events?{query}")
    except (OSError, StopIteration, ValueError, urllib.error.URLError) as error:
        raise ActivityWatchUnavailable(f"ActivityWatch data is unavailable: {error}") from error
    if not window_events:
        raise ActivityWatchUnavailable("ActivityWatch has no window events for the requested range.")

    active_intervals = []
    afk_seconds = 0.0
    daily = defaultdict(lambda: {"active_seconds": 0.0, "afk_seconds": 0.0, "billable_seconds": 0.0})
    for event in afk_events:
        event_start = max(parse_time(event["timestamp"]), start)
        event_end = min(parse_time(event["timestamp"]) + dt.timedelta(seconds=event.get("duration", 0)), end)
        if event_end <= event_start:
            continue
        is_active = event.get("data", {}).get("status") == "not-afk"
        if is_active:
            active_intervals.append((event_start, event_end))
        else:
            afk_seconds += seconds(event_end - event_start)
            for date_key, chunk_start, chunk_end in day_chunks(event_start, event_end, timezone):
                daily[date_key]["afk_seconds"] += seconds(chunk_end - chunk_start)

    apps = defaultdict(lambda: {"active_seconds": 0.0, "billable_seconds": 0.0, "events": [], "first_seen": None, "last_active": None})
    projects = defaultdict(lambda: {"active_seconds": 0.0, "billable_seconds": 0.0, "client": ""})
    categories = defaultdict(lambda: {"active_seconds": 0.0, "billable_seconds": 0.0})
    timeline = []
    for event in window_events:
        event_start = max(parse_time(event["timestamp"]), start)
        event_end = min(parse_time(event["timestamp"]) + dt.timedelta(seconds=event.get("duration", 0)), end)
        if event_end <= event_start:
            continue
        data = event.get("data", {})
        app = data.get("app") or "Unknown"
        title = safe_title(data.get("title", "")) if include_titles else "[Title hidden]"
        attributes = attributes_for(app, title, rules)
        for active_start, active_end in intersect_intervals(event_start, event_end, active_intervals):
            active = seconds(active_end - active_start)
            app_item = apps[app]
            app_item["active_seconds"] += active
            if attributes["billable"]:
                app_item["billable_seconds"] += active
            app_item["events"].append((active_start, active_end))
            app_item["first_seen"] = min(app_item["first_seen"] or active_start, active_start)
            app_item["last_active"] = max(app_item["last_active"] or active_end, active_end)
            project = str(attributes["project"])
            client = str(attributes["client"])
            projects[project]["client"] = client
            add_aggregate(projects, project, active, attributes["billable"])
            add_aggregate(categories, str(attributes["category"]), active, attributes["billable"])
            for date_key, chunk_start, chunk_end in day_chunks(active_start, active_end, timezone):
                chunk_seconds = seconds(chunk_end - chunk_start)
                daily[date_key]["active_seconds"] += chunk_seconds
                if attributes["billable"]:
                    daily[date_key]["billable_seconds"] += chunk_seconds
            timeline.append({
                "start": active_start.astimezone(timezone).isoformat(),
                "end": active_end.astimezone(timezone).isoformat(),
                "app": app,
                "title": title,
                "active_seconds": round(active, 1),
                **attributes,
            })

    summary_apps = []
    for app, value in apps.items():
        events = sorted(value["events"])
        sessions = 0
        previous_end = None
        for event_start, event_end in events:
            if previous_end is None or event_start - previous_end > dt.timedelta(seconds=5):
                sessions += 1
            previous_end = max(previous_end or event_end, event_end)
        summary_apps.append({
            "app": app,
            "foreground_sessions": sessions,
            "active_seconds": round(value["active_seconds"], 1),
            "billable_seconds": round(value["billable_seconds"], 1),
            "first_seen": value["first_seen"].astimezone(timezone).isoformat(),
            "last_active": value["last_active"].astimezone(timezone).isoformat(),
        })
    summary_apps.sort(key=lambda item: item["active_seconds"], reverse=True)
    summary_projects = sorted(({
        "project": project,
        "client": value["client"],
        "active_seconds": round(value["active_seconds"], 1),
        "billable_seconds": round(value["billable_seconds"], 1),
    } for project, value in projects.items()), key=lambda item: item["active_seconds"], reverse=True)
    summary_categories = sorted(({
        "category": category,
        "active_seconds": round(value["active_seconds"], 1),
        "billable_seconds": round(value["billable_seconds"], 1),
    } for category, value in categories.items()), key=lambda item: item["active_seconds"], reverse=True)
    trend = [{"date": date_key, **{key: round(value[key], 1) for key in value}} for date_key, value in sorted(daily.items())]
    active_seconds = round(sum(item["active_seconds"] for item in summary_apps), 1)
    return {
        "available": True,
        "timezone": timezone_name(timezone),
        "range_start": start.astimezone(timezone).isoformat(),
        "range_end": end.astimezone(timezone).isoformat(),
        "active_seconds": active_seconds,
        "billable_seconds": round(sum(item["billable_seconds"] for item in summary_apps), 1),
        "afk_seconds": round(afk_seconds, 1),
        "apps": summary_apps,
        "projects": summary_projects,
        "categories": summary_categories,
        "trend": trend,
        "timeline": timeline,
    }


def table_data(summary, table):
    if table == "summary":
        return ["metric", "value"], [["range_start", summary["range_start"]], ["range_end", summary["range_end"]], ["timezone", summary["timezone"]], ["active_seconds", summary["active_seconds"]], ["active_duration", format_duration(summary["active_seconds"])], ["billable_seconds", summary["billable_seconds"]], ["billable_duration", format_duration(summary["billable_seconds"])], ["afk_seconds", summary["afk_seconds"]], ["afk_duration", format_duration(summary["afk_seconds"])], ["source", "ActivityWatch"]]
    if table == "apps":
        return ["app", "foreground_sessions", "active_seconds", "active_duration", "billable_seconds", "billable_duration", "first_seen", "last_active", "source"], [[item["app"], item["foreground_sessions"], item["active_seconds"], format_duration(item["active_seconds"]), item["billable_seconds"], format_duration(item["billable_seconds"]), item["first_seen"], item["last_active"], "ActivityWatch"] for item in summary["apps"]]
    if table in ("projects", "client-timesheet"):
        return ["client", "project", "active_seconds", "active_duration", "billable_seconds", "billable_duration", "source"], [[item["client"], item["project"], item["active_seconds"], format_duration(item["active_seconds"]), item["billable_seconds"], format_duration(item["billable_seconds"]), "ActivityWatch"] for item in summary["projects"]]
    if table == "categories":
        return ["category", "active_seconds", "active_duration", "billable_seconds", "billable_duration", "source"], [[item["category"], item["active_seconds"], format_duration(item["active_seconds"]), item["billable_seconds"], format_duration(item["billable_seconds"]), "ActivityWatch"] for item in summary["categories"]]
    if table in ("trend", "app-trend"):
        return ["date", "active_seconds", "active_duration", "billable_seconds", "billable_duration", "afk_seconds", "afk_duration", "source"], [[item["date"], item["active_seconds"], format_duration(item["active_seconds"]), item["billable_seconds"], format_duration(item["billable_seconds"]), item["afk_seconds"], format_duration(item["afk_seconds"]), "ActivityWatch"] for item in summary["trend"]]
    if table == "weekly-review":
        return ["metric", "value"], [["active_duration", format_duration(summary["active_seconds"])], ["billable_duration", format_duration(summary["billable_seconds"])], ["afk_duration", format_duration(summary["afk_seconds"])], ["top_project", summary["projects"][0]["project"] if summary["projects"] else "Unassigned"], ["top_category", summary["categories"][0]["category"] if summary["categories"] else "Uncategorized"], ["source", "ActivityWatch"]]
    return ["start", "end", "app", "title", "client", "project", "category", "billable", "active_seconds", "active_duration", "source"], [[item["start"], item["end"], item["app"], item["title"], item["client"], item["project"], item["category"], item["billable"], item["active_seconds"], format_duration(item["active_seconds"]), "ActivityWatch"] for item in sorted(summary["timeline"], key=lambda item: item["start"])]


def unavailable_data(reason):
    return ["status", "reason", "source"], [["unavailable", reason, "ActivityWatch"]]


def render_table(summary, output_format, table, csv_bom=False):
    if output_format == "json":
        return json.dumps(summary, ensure_ascii=False)
    headers, rows = table_data(summary, table) if summary["available"] else unavailable_data(summary["reason"])
    if output_format == "markdown":
        escaped = lambda value: safe_cell(value).replace("|", "\\|").replace("\n", " ")
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        lines.extend("| " + " | ".join(escaped(value) for value in row) + " |" for row in rows)
        return "\n".join(lines)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter="\t" if output_format == "tsv" else ",", lineterminator="\n")
    writer.writerow(headers)
    writer.writerows([[safe_cell(value) for value in row] for row in rows])
    return ("\ufeff" if output_format == "csv" and csv_bom else "") + buffer.getvalue()


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--date", help="Local anchor date in YYYY-MM-DD format or 'today'")
    group.add_argument("--start", help="Inclusive local start date in YYYY-MM-DD format")
    parser.add_argument("--end", help="Inclusive local end date; required with --start")
    parser.add_argument("--period", choices=("day", "week", "month"), default="day", help="Range around --date; week starts Monday")
    parser.add_argument("--timezone", help="IANA time zone, for example Asia/Singapore; defaults to the local time zone")
    parser.add_argument("--api-url", default=DEFAULT_API, help="Local ActivityWatch API URL; defaults to http://127.0.0.1:5600/api/0")
    parser.add_argument("--rules", help="Optional local JSON mapping rules; never uploaded")
    parser.add_argument("--format", choices=("json", "markdown", "tsv", "csv"), default="json", help="TSV is suitable for pasting into a spreadsheet")
    parser.add_argument("--table", choices=("summary", "apps", "projects", "categories", "trend", "timeline"), default="apps", help="Table for Markdown, TSV, or CSV output")
    parser.add_argument("--report", choices=("client-timesheet", "weekly-review", "app-trend"), help="Named report template; overrides --table")
    parser.add_argument("--csv-bom", action="store_true", help="Prefix CSV output with a UTF-8 BOM for spreadsheet compatibility")
    parser.add_argument("--hide-titles", action="store_true", help="Replace timeline window titles with [Title hidden]")
    parser.add_argument("--output", help="Optional UTF-8 file path; otherwise write to standard output")
    args = parser.parse_args()
    if args.csv_bom and args.format != "csv":
        parser.error("--csv-bom requires --format csv")
    try:
        timezone = resolve_timezone(args.timezone)
        start_day, end_day = parse_date_range(args.date, args.start, args.end, args.period, timezone)
        rules = load_rules(args.rules)
    except (ValueError, RulesConfigurationError) as error:
        parser.error(str(error))
    try:
        fetch = lambda path: get_json(path, args.api_url)
        summary = collect_summary(start_day, end_day, timezone, fetch, include_titles=not args.hide_titles, rules=rules)
    except ActivityWatchUnavailable as error:
        summary = {"available": False, "reason": str(error), "timezone": timezone_name(timezone)}
    result = render_table(summary, args.format, args.report or args.table, args.csv_bom)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as file:
            file.write(result)
    else:
        print(result, end="" if result.endswith("\n") else "\n")
    return 0 if summary["available"] else 1


if __name__ == "__main__":
    sys.exit(main())
