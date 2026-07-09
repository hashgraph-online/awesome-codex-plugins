"""Text metrics and aggregate metric helpers for source-index output."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any


WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)


def line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def metrics_for_text(data: bytes, text: str) -> dict[str, int]:
    characters = len(text)
    return {
        "bytes": len(data),
        "lines": line_count(text),
        "words": len(WORD_RE.findall(text)),
        "characters": characters,
        "estimated_tokens": math.ceil(characters / 4),
    }


def metrics_for_text_fragment(text: str) -> dict[str, int]:
    return metrics_for_text(text.encode("utf-8", errors="replace"), text)


def empty_metrics() -> dict[str, int]:
    return {"bytes": 0, "lines": 0, "words": 0, "characters": 0, "estimated_tokens": 0}


def add_metrics(left: dict[str, int], right: dict[str, int]) -> None:
    for key in ("bytes", "lines", "words", "characters", "estimated_tokens"):
        left[key] += right[key]


def metric_sum(files: list[dict[str, Any]], file_ids: list[str]) -> dict[str, int]:
    by_id = {file_record["file_id"]: file_record for file_record in files}
    totals = empty_metrics()
    for file_id in file_ids:
        metrics = by_id[file_id]["metrics"]
        add_metrics(totals, metrics)
    return totals


def segment_metric_sum(file_segments: list[dict[str, Any]], segment_ids: list[str]) -> dict[str, int]:
    by_id = {segment["segment_id"]: segment for segment in file_segments}
    totals = empty_metrics()
    for segment_id in segment_ids:
        add_metrics(totals, by_id[segment_id]["metrics"])
    return totals


def language_counts(files: list[dict[str, Any]], file_ids: list[str]) -> dict[str, int]:
    by_id = {file_record["file_id"]: file_record for file_record in files}
    counts: dict[str, int] = defaultdict(int)
    for file_id in file_ids:
        counts[str(by_id[file_id]["language"])] += 1
    return dict(sorted(counts.items()))

