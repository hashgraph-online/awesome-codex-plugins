"""Activity aggregation and report shaping."""

import datetime as dt
from collections import defaultdict

from .classify import CATEGORY_ORDER, choose_main_focus, classify_activity
from .intervals import (
    afk_intervals,
    count_sessions,
    interval_seconds,
    local_iso,
    merge_intervals,
    overlap,
    seconds,
    window_entries,
)
from .models import BROWSER_APP_PATTERN, DEFAULT_BROWSER_THRESHOLD, format_duration


def _period_seconds(start, end, timezone):
    absolute = seconds(end.astimezone(dt.timezone.utc) - start.astimezone(dt.timezone.utc))
    local_start = start.astimezone(timezone).date()
    local_end = end.astimezone(timezone).date()
    if local_end == local_start + dt.timedelta(days=1):
        return min(absolute, 86400.0)
    return absolute


def _browser_short_visits(browser_pages, minimum_seconds):
    omitted = [
        item for item in browser_pages if item["active_seconds"] < minimum_seconds
    ]
    return {
        "threshold_seconds": float(minimum_seconds),
        "count": len(omitted),
        "active_seconds": round(
            sum(item["active_seconds"] for item in omitted), 1
        ),
        "active_duration": format_duration(
            sum(item["active_seconds"] for item in omitted)
        ),
    }


def aggregate_browser_pages(window_events, active_intervals, start, end, timezone):
    pages = defaultdict(lambda: {"active_seconds": 0.0, "events": []})
    for event_start, event_end, app, title in window_entries(
        window_events, start, end
    ):
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
        classification = classify_activity(app, title)
        result.append(
            {
                "app": app,
                "title": title,
                "category": classification["category"],
                "confidence": classification["confidence"],
                "foreground_sessions": count_sessions(events),
                "active_seconds": round(value["active_seconds"], 1),
                "first_seen": local_iso(events[0][0], timezone),
                "last_active": local_iso(max(event[1] for event in events), timezone),
                "source": "ActivityWatch foreground window title",
            }
        )
    result.sort(key=lambda item: item["active_seconds"], reverse=True)
    return result


def _category_summary(category_totals, category_apps):
    result = []
    for category in CATEGORY_ORDER:
        total = category_totals.get(category, 0.0)
        if total <= 0:
            continue
        apps = sorted(
            category_apps.get(category, {}).items(),
            key=lambda item: (-item[1], item[0]),
        )
        result.append(
            {
                "category": category,
                "active_seconds": round(total, 1),
                "active_duration": format_duration(total),
                "top_apps": [app for app, _ in apps[:3]],
                "source": "ActivityWatch",
            }
        )
    return result


def summarize_period(window_events, afk_events, start, end, timezone, timezone_name):
    active_intervals, away_intervals = afk_intervals(afk_events, start, end)
    coverage_intervals = merge_intervals(active_intervals + away_intervals)
    active_seconds = interval_seconds(active_intervals)
    coverage_seconds = interval_seconds(coverage_intervals)
    period_seconds = _period_seconds(start, end, timezone)
    active_seconds = min(active_seconds, period_seconds)
    coverage_seconds = min(coverage_seconds, period_seconds)
    afk_seconds = max(0.0, coverage_seconds - active_seconds)

    apps = defaultdict(
        lambda: {
            "active_seconds": 0.0,
            "events": [],
            "categories": defaultdict(float),
        }
    )
    category_totals = defaultdict(float)
    category_apps = defaultdict(lambda: defaultdict(float))
    timeline = []
    for event_start, event_end, app, title in window_entries(
        window_events, start, end
    ):
        active = overlap(event_start, event_end, active_intervals)
        if active <= 0:
            continue
        classification = classify_activity(app, title)
        category = classification["category"]
        item = apps[app]
        item["active_seconds"] += active
        item["events"].append((event_start, event_end))
        item["categories"][category] += active
        category_totals[category] += active
        category_apps[category][app] += active
        timeline.append(
            {
                "start": local_iso(event_start, timezone),
                "end": local_iso(event_end, timezone),
                "app": app,
                "title": title,
                "category": category,
                "confidence": classification["confidence"],
                "active_seconds": round(active, 1),
                "source": "ActivityWatch",
            }
        )

    summary_apps = []
    for app, value in apps.items():
        events = sorted(value["events"])
        category = max(
            value["categories"],
            key=lambda name: (value["categories"][name], name),
        )
        summary_apps.append(
            {
                "app": app,
                "category": category,
                "foreground_sessions": count_sessions(events),
                "active_seconds": round(value["active_seconds"], 1),
                "first_seen": local_iso(events[0][0], timezone),
                "last_active": local_iso(max(event[1] for event in events), timezone),
                "source": "ActivityWatch",
            }
        )
    summary_apps.sort(key=lambda item: item["active_seconds"], reverse=True)
    browser_pages = aggregate_browser_pages(
        window_events, active_intervals, start, end, timezone
    )
    first_seen = min((item["first_seen"] for item in summary_apps), default=None)
    last_active = max((item["last_active"] for item in summary_apps), default=None)
    return {
        "date": start.astimezone(timezone).date().isoformat(),
        "timezone": timezone_name,
        "range_start": local_iso(start, timezone),
        "range_end": local_iso(end, timezone),
        "first_seen": first_seen,
        "last_active": last_active,
        "active_seconds": round(active_seconds, 1),
        "afk_seconds": round(afk_seconds, 1),
        "coverage_seconds": round(coverage_seconds, 1),
        "untracked_seconds": round(max(0.0, period_seconds - coverage_seconds), 1),
        "main_focus": choose_main_focus(category_totals),
        "category_totals": {
            category: round(value, 1) for category, value in category_totals.items()
        },
        "category_summary": _category_summary(category_totals, category_apps),
        "apps": summary_apps,
        "browser_pages": browser_pages,
        "browser_short_visits": _browser_short_visits(
            browser_pages, DEFAULT_BROWSER_THRESHOLD
        ),
        "timeline": sorted(timeline, key=lambda item: item["start"]),
        "source": "ActivityWatch",
    }


def filter_browser_pages(summary, minimum_seconds):
    """Apply a display threshold while retaining complete grouped JSON data."""
    targets = [summary] + list(summary.get("days", []))
    for target in targets:
        all_pages = target.get("browser_pages_all", target.get("browser_pages", []))
        target["browser_pages_all"] = list(all_pages)
        target["browser_short_visits"] = _browser_short_visits(
            all_pages, minimum_seconds
        )
        target["browser_pages"] = [
            item for item in all_pages if item["active_seconds"] >= minimum_seconds
        ]
