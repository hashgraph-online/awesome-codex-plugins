"""Local ActivityWatch reporting primitives."""

from .classify import CATEGORY_ORDER, choose_main_focus, classify_activity
from .cli import build_parser, date_range, main, nonnegative_finite_float
from .intervals import (
    afk_intervals,
    clip_event,
    count_sessions,
    interval_seconds,
    local_iso,
    merge_intervals,
    overlap,
    parse_time,
    resolve_timezone,
    seconds,
    utc_offset_label,
    window_entries,
)
from .models import (
    BROWSER_APP_PATTERN,
    DEFAULT_BROWSER_THRESHOLD,
    format_duration,
    normalize_title,
    safe_cell,
    safe_title,
)
from .render import render_report, render_rows, render_table, table_data
from .reports import aggregate_browser_pages, filter_browser_pages, summarize_period
from .source import API, ActivityWatchUnavailable, get_json

__all__ = [
    "API",
    "BROWSER_APP_PATTERN",
    "CATEGORY_ORDER",
    "DEFAULT_BROWSER_THRESHOLD",
    "ActivityWatchUnavailable",
    "afk_intervals",
    "aggregate_browser_pages",
    "build_parser",
    "choose_main_focus",
    "classify_activity",
    "clip_event",
    "count_sessions",
    "date_range",
    "filter_browser_pages",
    "format_duration",
    "get_json",
    "interval_seconds",
    "local_iso",
    "main",
    "merge_intervals",
    "nonnegative_finite_float",
    "normalize_title",
    "overlap",
    "parse_time",
    "render_report",
    "render_rows",
    "render_table",
    "resolve_timezone",
    "safe_cell",
    "safe_title",
    "seconds",
    "summarize_period",
    "table_data",
    "utc_offset_label",
    "window_entries",
]
