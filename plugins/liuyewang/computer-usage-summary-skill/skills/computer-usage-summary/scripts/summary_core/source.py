"""Local ActivityWatch API access."""

import datetime as dt
import json
import urllib.parse
import urllib.request

API = "http://127.0.0.1:5600/api/0"


class ActivityWatchUnavailable(RuntimeError):
    """Raised when required local ActivityWatch data cannot be retrieved."""


def _latest_bucket_id(buckets, bucket_type):
    if not isinstance(buckets, dict):
        raise ActivityWatchUnavailable("ActivityWatch returned an invalid bucket payload")
    candidates = [
        (bucket_id, bucket)
        for bucket_id, bucket in (buckets or {}).items()
        if isinstance(bucket, dict) and bucket.get("type") == bucket_type
    ]
    if not candidates:
        raise ActivityWatchUnavailable(
            f"required ActivityWatch bucket is missing: {bucket_type}"
        )
    return max(
        candidates,
        key=lambda item: item[1].get("last_updated") or "",
    )[0]


def get_json(path, api=API):
    with urllib.request.urlopen(f"{api}{path}", timeout=30) as response:
        return json.load(response)


def fetch_events(start, end, api=API):
    query = urllib.parse.urlencode(
        {
            "starttime": start.astimezone(dt.timezone.utc).isoformat(),
            "endtime": end.astimezone(dt.timezone.utc).isoformat(),
        }
    )
    try:
        buckets = get_json("/buckets/", api)
        window_id = _latest_bucket_id(buckets, "currentwindow")
        afk_id = _latest_bucket_id(buckets, "afkstatus")
    except ActivityWatchUnavailable:
        raise
    except (OSError, ValueError, TypeError) as error:
        raise ActivityWatchUnavailable(str(error)) from error

    try:
        window_events = get_json(
            f"/buckets/{urllib.parse.quote(window_id, safe='')}/events?{query}", api
        )
        afk_events = get_json(
            f"/buckets/{urllib.parse.quote(afk_id, safe='')}/events?{query}", api
        )
    except (OSError, ValueError, TypeError) as error:
        raise ActivityWatchUnavailable(str(error)) from error
    if not isinstance(window_events, list) or not isinstance(afk_events, list):
        raise ActivityWatchUnavailable("ActivityWatch returned an invalid event payload")
    if not window_events or not afk_events:
        raise ActivityWatchUnavailable("ActivityWatch returned no events for the requested range")
    return window_events, afk_events
