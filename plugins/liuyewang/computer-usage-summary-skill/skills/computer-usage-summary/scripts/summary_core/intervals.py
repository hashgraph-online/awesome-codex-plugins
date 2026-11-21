"""Timezone-aware interval and ActivityWatch event normalization helpers."""

import datetime as dt
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import normalize_title


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
        parse_time(event["timestamp"])
        + dt.timedelta(seconds=event.get("duration", 0)),
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
        if previous_end is None or event_start - previous_end > dt.timedelta(
            seconds=gap_seconds
        ):
            sessions += 1
        previous_end = max(previous_end or event_end, event_end)
    return sessions
