"""Batch and large-item recommendations for source-index output."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from source_index.metrics import empty_metrics, language_counts, metric_sum, segment_metric_sum


def split_files_for_batch(
    files: list[dict[str, Any]], file_ids: list[str], max_batch_tokens: int
) -> list[list[str]]:
    by_id = {file_record["file_id"]: file_record for file_record in files}
    chunks: list[list[str]] = []
    current: list[str] = []
    current_tokens = 0
    for file_id in sorted(file_ids, key=lambda item: (by_id[item]["path"], item)):
        tokens = by_id[file_id]["metrics"]["estimated_tokens"]
        if current and current_tokens + tokens > max_batch_tokens:
            chunks.append(current)
            current = []
            current_tokens = 0
        current.append(file_id)
        current_tokens += tokens
    if current:
        chunks.append(current)
    return chunks


def build_batches(
    files: list[dict[str, Any]],
    file_segments: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    max_batch_tokens: int,
) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    pending_group_ids: list[str] = []
    pending_file_ids: list[str] = []
    pending_tokens = 0
    segments_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for segment in file_segments:
        segments_by_file[segment["file_id"]].append(segment)

    def flush(note: str) -> None:
        nonlocal pending_group_ids, pending_file_ids, pending_tokens
        if not pending_file_ids:
            return
        batches.append(
            {
                "batch_id": f"batch-{len(batches) + 1:04d}",
                "group_ids": pending_group_ids,
                "file_ids": pending_file_ids,
                "segment_ids": [],
                "metrics": metric_sum(files, pending_file_ids),
                "language_counts": language_counts(files, pending_file_ids),
                "notes": note,
            }
        )
        pending_group_ids = []
        pending_file_ids = []
        pending_tokens = 0

    for group in groups:
        group_tokens = group["metrics"]["estimated_tokens"]
        group_has_segments = any(file_id in segments_by_file for file_id in group["file_ids"])
        if group_tokens > max_batch_tokens or group_has_segments:
            flush(f"Fits max_batch_tokens {max_batch_tokens}.")
            split_note = (
                f"Split large {group['group_id']} to respect max_batch_tokens {max_batch_tokens}."
                if group_tokens > max_batch_tokens
                else f"Split {group['group_id']} to preserve large-file segment boundaries."
            )

            def append_regular_chunk(chunk_file_ids: list[str], note: str) -> None:
                batches.append(
                    {
                        "batch_id": f"batch-{len(batches) + 1:04d}",
                        "group_ids": [group["group_id"]],
                        "file_ids": chunk_file_ids,
                        "segment_ids": [],
                        "metrics": metric_sum(files, chunk_file_ids),
                        "language_counts": language_counts(files, chunk_file_ids),
                        "notes": note,
                    }
                )

            def append_segment_batches(file_id: str) -> None:
                for segment in segments_by_file[file_id]:
                    segment_ids = [segment["segment_id"]]
                    batches.append(
                        {
                            "batch_id": f"batch-{len(batches) + 1:04d}",
                            "group_ids": [group["group_id"]],
                            "file_ids": [file_id],
                            "segment_ids": segment_ids,
                            "metrics": segment_metric_sum(file_segments, segment_ids),
                            "language_counts": language_counts(files, [file_id]),
                            "notes": (
                                f"Split large {file_id} from {group['group_id']} by line spans "
                                f"to respect max_batch_tokens {max_batch_tokens}."
                            ),
                        }
                    )

            for chunk in split_files_for_batch(files, group["file_ids"], max_batch_tokens):
                if any(file_id in segments_by_file for file_id in chunk):
                    regular_chunk: list[str] = []
                    for file_id in chunk:
                        if file_id in segments_by_file:
                            if regular_chunk:
                                append_regular_chunk(regular_chunk, split_note)
                                regular_chunk = []
                            append_segment_batches(file_id)
                        else:
                            regular_chunk.append(file_id)
                    if regular_chunk:
                        append_regular_chunk(regular_chunk, split_note)
                    continue
                append_regular_chunk(chunk, split_note)
            continue
        if pending_file_ids and pending_tokens + group_tokens > max_batch_tokens:
            flush(f"Fits max_batch_tokens {max_batch_tokens}.")
        pending_group_ids.append(group["group_id"])
        pending_file_ids.extend(group["file_ids"])
        pending_tokens += group_tokens
    flush(f"Fits max_batch_tokens {max_batch_tokens}.")
    return batches


def build_large_items(
    files: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    batches: list[dict[str, Any]],
    large_file_words: int,
    large_group_words: int,
    max_batch_tokens: int,
) -> list[dict[str, Any]]:
    large_items: list[dict[str, Any]] = []

    def reason_for(metrics: dict[str, int], word_limit: int) -> str | None:
        if metrics["words"] > word_limit:
            return "word-count-threshold"
        if metrics["estimated_tokens"] > max_batch_tokens:
            return "token-threshold"
        return None

    for file_record in files:
        reason = reason_for(file_record["metrics"], large_file_words)
        if reason:
            large_items.append(
                {
                    "item_id": file_record["file_id"],
                    "kind": "file",
                    "metrics": file_record["metrics"],
                    "reason": reason,
                    "notes": "Large source file should be assigned through file_segments or a narrow unit.",
                }
            )
    for group in groups:
        reason = reason_for(group["metrics"], large_group_words)
        if reason:
            large_items.append(
                {
                    "item_id": group["group_id"],
                    "kind": "group",
                    "metrics": group["metrics"],
                    "reason": reason,
                    "notes": "Large dependency group should be decomposed through recommended_batches.",
                }
            )
    for batch in batches:
        reason = reason_for(batch["metrics"], large_group_words)
        if reason:
            large_items.append(
                {
                    "item_id": batch["batch_id"],
                    "kind": "batch",
                    "metrics": batch["metrics"],
                    "reason": reason,
                    "notes": "Batch is still large; controller should narrow the unit before source analysis.",
                }
            )
    return large_items


def aggregate_metrics(
    files: list[dict[str, Any]],
    file_segments: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    batches: list[dict[str, Any]],
    large_items: list[dict[str, Any]],
    skipped_count: int,
    skipped_entries: list[dict[str, str]],
) -> dict[str, int | bool]:
    file_ids = [file_record["file_id"] for file_record in files]
    totals = metric_sum(files, file_ids) if file_ids else empty_metrics()
    totals.update(
        {
            "file_count": len(files),
            "file_segment_count": len(file_segments),
            "skipped_count": skipped_count,
            "skipped_entries_truncated": skipped_count > len(skipped_entries),
            "relationship_count": len(relationships),
            "resolved_relationship_count": sum(1 for item in relationships if item.get("to_file_id")),
            "group_count": len(groups),
            "batch_count": len(batches),
            "large_item_count": len(large_items),
        }
    )
    return totals

