#!/usr/bin/env python3
"""morning-ai data collection orchestrator.

Runs all collectors concurrently, normalizes, scores, deduplicates,
and outputs a structured JSON report.

Usage:
    python3 skills/tracking-list/scripts/collect.py [--date YYYY-MM-DD] [--depth quick|default|deep] [--output PATH]
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from lib import env, cache
from lib.schema import TrackerItem, CollectionResult, DailyReport
from lib.score import score_items, apply_verification_bonus
from lib.dedupe import dedupe_by_source, cross_source_link
from lib.classify import classify_items
from lib import entities
from lib.util import log


_log = lambda msg: log("collect", msg)


def get_time_window(date_str: str) -> tuple:
    """Get 24-hour collection window (08:00 UTC+8 yesterday to 08:00 UTC+8 today).

    Returns:
        (from_date, to_date) as YYYY-MM-DD strings
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    from_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = date_str
    return from_date, to_date


def collect_reddit(config: Dict[str, Any], from_date: str, to_date: str, depth: str) -> CollectionResult:
    """Collect from Reddit."""
    from lib import reddit
    return reddit.collect(
        entities.REDDIT_KEYWORDS, from_date, to_date,
        entity_subreddits=entities.REDDIT_SUBREDDITS, depth=depth,
    )


def collect_hackernews(config: Dict[str, Any], from_date: str, to_date: str, depth: str) -> CollectionResult:
    """Collect from Hacker News."""
    from lib import hackernews
    return hackernews.collect(entities.HN_KEYWORDS, from_date, to_date, depth)


def collect_github(config: Dict[str, Any], from_date: str, to_date: str, depth: str) -> CollectionResult:
    """Collect from GitHub."""
    from lib import github

    token = env.get_key(config, "GITHUB_TOKEN")
    return github.collect(entities.GITHUB_SOURCES, from_date, to_date, token, depth)


def collect_huggingface(config: Dict[str, Any], from_date: str, to_date: str, depth: str) -> CollectionResult:
    """Collect from HuggingFace."""
    from lib import huggingface
    return huggingface.collect(entities.HUGGINGFACE_AUTHORS, from_date, to_date, depth)


def collect_arxiv(config: Dict[str, Any], from_date: str, to_date: str, depth: str) -> CollectionResult:
    """Collect from arXiv."""
    from lib import arxiv
    return arxiv.collect(entities.ARXIV_QUERIES, from_date, to_date, depth)


def collect_x(config: Dict[str, Any], from_date: str, to_date: str, depth: str) -> CollectionResult:
    """Collect from X/Twitter via sub-agent web search.

    Uses two parallel `claude -p` sub-agents (official accounts + Key People),
    each searching x.com via the WebSearch tool. Honours HTTPS_PROXY inherited
    from the parent process (set by foreman/adapters/daily-report/adapter.py).
    """
    from lib import x_agent
    return x_agent.collect(
        {
            "official": entities.X_HANDLES_OFFICIAL,
            "key_people": entities.X_HANDLES_KEY_PEOPLE,
            "kol": entities.X_HANDLES_KOL,
        },
        from_date, to_date, depth,
    )


# All collectors with their names
COLLECTORS = {
    "x": collect_x,
    "reddit": collect_reddit,
    "hackernews": collect_hackernews,
    "github": collect_github,
    "huggingface": collect_huggingface,
    "arxiv": collect_arxiv,
}


def run_collection(
    date_str: str,
    depth: str = "default",
    skip: Optional[List[str]] = None,
) -> DailyReport:
    """Run full data collection pipeline.

    Args:
        date_str: Target date YYYY-MM-DD
        depth: Collection depth (quick|default|deep)
        skip: Optional list of sources to skip (default: none — all collectors run).
            Deny-list semantics on purpose: an allow-list (`--sources`) lets
            callers — including LLM agents reading SKILL.md — silently omit a
            collector by forgetting to list it. arxiv was dropped from prod for
            5 days that way. Forcing the caller to *name* what they skip
            ("--skip arxiv") makes the omission obvious in shell history.

    Returns:
        DailyReport with all collected, scored, and deduplicated items
    """
    config = env.get_config()
    from_date, to_date = get_time_window(date_str)
    available = env.get_available_sources(config)

    _log(f"Date: {date_str}, Window: {from_date} ~ {to_date}, Depth: {depth}")
    _log(f"Available sources: {[k for k, v in available.items() if v]}")

    # Determine which collectors to run (skip list is deny-list)
    skip_set = set(skip or [])
    unknown = skip_set - COLLECTORS.keys()
    if unknown:
        raise ValueError(
            f"Unknown collector(s) in --skip: {sorted(unknown)}. "
            f"Valid: {sorted(COLLECTORS.keys())}"
        )
    active_collectors = {
        name: func for name, func in COLLECTORS.items() if name not in skip_set
    }
    if skip_set:
        _log(f"Skipping collectors: {sorted(skip_set)}")
    if not active_collectors:
        raise ValueError(
            f"--skip excluded every collector. Valid sources: {sorted(COLLECTORS.keys())}"
        )

    # Run collectors concurrently
    start_time = time.time()
    collection_results = []
    all_items: List[TrackerItem] = []

    with ThreadPoolExecutor(max_workers=len(active_collectors)) as executor:
        futures = {
            executor.submit(func, config, from_date, to_date, depth): name
            for name, func in active_collectors.items()
        }

        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result(timeout=600)
                collection_results.append(result)
                all_items.extend(result.items)
                _log(f"[{name}] Done: {len(result.items)} items, {len(result.errors)} errors")
            except Exception as e:
                _log(f"[{name}] Failed: {e}")
                collection_results.append(
                    CollectionResult(source=name, errors=[str(e)])
                )

    collect_time = time.time() - start_time
    _log(f"Collection complete: {len(all_items)} raw items in {collect_time:.1f}s")

    # Pipeline: Classify → Score → Dedupe by source → Cross-source link → Verification bonus
    _log("Classifying content types...")
    all_items = classify_items(all_items)

    _log("Scoring items...")
    all_items = score_items(all_items)

    _log("Deduplicating within sources...")
    all_items = dedupe_by_source(all_items)
    _log(f"After source dedup: {len(all_items)} items")

    _log("Cross-source linking...")
    all_items = cross_source_link(all_items)

    _log("Applying verification bonus...")
    all_items = apply_verification_bonus(all_items)

    # Re-assign sequential IDs
    for i, item in enumerate(all_items):
        item.id = f"T{i + 1:03d}"

    # Build stats
    stats = {
        "total_raw": sum(len(r.items) for r in collection_results),
        "total_after_dedup": len(all_items),
        "by_source": {},
        "by_importance": {
            "9-10 (industry-changing)": len([i for i in all_items if i.importance >= 9]),
            "7-8 (important)": len([i for i in all_items if 7 <= i.importance < 9]),
            "5-6 (routine)": len([i for i in all_items if 5 <= i.importance < 7]),
            "3-4 (minor)": len([i for i in all_items if 3 <= i.importance < 5]),
            "1-2 (trivial)": len([i for i in all_items if i.importance < 3]),
        },
        "verified_count": len([i for i in all_items if i.verified]),
        "collection_time_seconds": round(collect_time, 1),
        "errors": [],
    }

    for r in collection_results:
        stats["by_source"][r.source] = {
            "items": len(r.items),
            "entities_checked": r.entities_checked,
            "entities_with_updates": r.entities_with_updates,
            "errors": r.errors,
        }
        stats["errors"].extend(r.errors)

    # Build report
    report = DailyReport(
        date=date_str,
        time_window=f"{from_date} 08:00 ~ {to_date} 08:00 UTC+8",
        generated_at=datetime.now(timezone.utc).isoformat(),
        items=all_items,
        collection_results=collection_results,
        stats=stats,
    )

    _log(f"Report ready: {len(all_items)} items, {stats['verified_count']} verified")
    return report


def main():
    parser = argparse.ArgumentParser(description="morning-ai data collection")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="Target date (default: today)")
    parser.add_argument("--depth", default="default", choices=["quick", "default", "deep"],
                        help="Collection depth")
    parser.add_argument("--skip", nargs="*", default=[],
                        help="Sources to SKIP (default: none — all 6 collectors run). "
                             "Use deny-list semantics so omission is explicit, "
                             "e.g. --skip arxiv reddit")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file path (default: stdout)")
    parser.add_argument("--cache-ttl", type=int, default=1,
                        help="Cache TTL in hours (default: 1, 0 to disable)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Skip cache entirely (equivalent to --cache-ttl 0)")
    parser.add_argument("--clear-cache", action="store_true",
                        help="Clear all cached data and exit")
    args = parser.parse_args()

    # Clear cache and exit
    if args.clear_cache:
        cache.clear_cache()
        _log("Cache cleared")
        return

    # Check cache. Include the skip filter in the key so a partial run
    # (--skip arxiv) can't poison a subsequent full run.
    ttl = 0 if args.no_cache else args.cache_ttl
    skip_key = ",".join(sorted(args.skip)) if args.skip else "all"
    cache_key = cache.get_cache_key("daily", args.date, args.depth, skip_key)
    if ttl > 0:
        cached = cache.load_cache(cache_key, ttl)
        if cached:
            _log("Using cached report")
            if args.output:
                Path(args.output).write_text(json.dumps(cached, ensure_ascii=False, indent=2))
            else:
                json.dump(cached, sys.stdout, ensure_ascii=False, indent=2)
            return

    # Run collection
    report = run_collection(args.date, args.depth, args.skip)
    report_dict = report.to_dict()

    # Save cache
    if ttl > 0:
        cache.save_cache(cache_key, report_dict)

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report_dict, ensure_ascii=False, indent=2))
        _log(f"Report saved to {args.output}")
    else:
        json.dump(report_dict, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
