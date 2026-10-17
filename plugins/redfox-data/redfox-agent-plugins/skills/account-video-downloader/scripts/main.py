#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-platform account video extractor — unified entry point
=====================================
Supported platforms: Douyin, Kuaishou, Bilibili, YouTube

Usage:
    python3 main.py --platform douyin --account "DouyinID"
    python3 main.py --platform kuaishou --account "kwaiId"
    python3 main.py --platform bilibili --account "HomepageURL" --download
    python3 main.py --platform youtube --account "ChannelURL" --download --output-dir ./videos
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Windows terminal UTF-8 encoding fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .base import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_RATE_LIMIT,
    MAX_PAGE_SIZE,
    get_api_key,
    info,
    warn,
    error,
    BOLD,
    CYAN,
    RED,
    YELLOW,
    RESET,
    process_account,
    print_markdown_table,
    print_json_output,
)
from .kuaishou import KuaishouDownloader
from .douyin import DouyinDownloader
from .bilibili import BilibiliDownloader
from .youtube import YouTubeDownloader

# ─── Platform registry ────────────────────────────────────────────────────────────────────

PLATFORM_REGISTRY = {
    "douyin": {
        "label": "Douyin",
        "downloader_cls": DouyinDownloader,
        "help": "Douyin account video download (Douyin ID / uniqueName)",
    },
    "kuaishou": {
        "label": "Kuaishou",
        "downloader_cls": KuaishouDownloader,
        "help": "Kuaishou account video download (user ID / kwaiId)",
    },
    "bilibili": {
        "label": "Bilibili",
        "downloader_cls": BilibiliDownloader,
        "help": "Bilibili account video download (homepage URL / accountUrl)",
    },
    "youtube": {
        "label": "YouTube",
        "downloader_cls": YouTubeDownloader,
        "help": "YouTube channel video download (channel ID / @handle)",
    },
}


def get_platform(name: str) -> dict:
    """Look up a platform config by name, with fuzzy matching."""
    name_lower = name.lower().strip()
    if name_lower in PLATFORM_REGISTRY:
        return PLATFORM_REGISTRY[name_lower]
    # Fuzzy matching. The "b站" alias is kept on purpose so users who type the
    # native Chinese name for Bilibili still resolve to the right platform.
    fuzzy_map = {
        "dy": "douyin",
        "douyin": "douyin",
        "ks": "kuaishou",
        "kuaishou": "kuaishou",
        "bili": "bilibili",
        "bilibili": "bilibili",
        "b站": "bilibili",
        "yt": "youtube",
        "youtube": "youtube",
    }
    mapped = fuzzy_map.get(name_lower)
    if mapped:
        return PLATFORM_REGISTRY[mapped]
    return None


def main():
    platforms_help = "\n".join(
        f"  {k:12s} — {v['label']}: {v['help']}"
        for k, v in PLATFORM_REGISTRY.items()
    )

    parser = argparse.ArgumentParser(
        description="Multi-platform account video extractor — Douyin / Kuaishou / Bilibili / YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported platforms:
{platforms_help}

Examples:
  python3 main.py --platform kuaishou --account "kwaiId"
  python3 main.py --platform bilibili --account "HomepageURL" --download
  python3 main.py --platform youtube --account "ChannelURL" --download --output-dir ./videos
        """,
    )
    parser.add_argument("--platform", "-p", required=True,
                        help="Target platform: douyin / kuaishou / bilibili / youtube")
    parser.add_argument("--account", "-a", required=False,
                        help="A single account identifier")
    parser.add_argument("--accounts", required=False,
                        help="Multiple account identifiers, comma-separated")
    parser.add_argument("--count", "-c", type=int, default=DEFAULT_PAGE_SIZE,
                        help=f"Number of works to fetch (default {DEFAULT_PAGE_SIZE}, max {MAX_PAGE_SIZE})")
    parser.add_argument("--page", type=int, default=1, help="Page number (default 1)")
    parser.add_argument("--date-start", help="Start date YYYY-MM-DD")
    parser.add_argument("--date-end", help="End date YYYY-MM-DD")
    parser.add_argument("--download", "-d", action="store_true", help="Download video files to local disk")
    parser.add_argument("--output-dir", "-o", default="", help="Download directory (default output/)")
    parser.add_argument("--json", "-j", action="store_true", help="Output in JSON format")
    parser.add_argument("--rate-limit", "-r", type=float, default=DEFAULT_RATE_LIMIT,
                        help=f"Seconds between requests (default {DEFAULT_RATE_LIMIT})")

    args = parser.parse_args()

    # ── Platform resolution ──
    platform_cfg = get_platform(args.platform)
    if not platform_cfg:
        error(f"Unsupported platform: {args.platform}")
        print(f"  Supported: {', '.join(PLATFORM_REGISTRY.keys())}")
        sys.exit(1)

    platform_label = platform_cfg["label"]
    downloader_cls = platform_cfg["downloader_cls"]

    # ── Collect account list ──
    account_ids = []
    if args.account:
        account_ids.append(args.account.strip())
    if args.accounts:
        account_ids.extend([a.strip() for a in args.accounts.split(",") if a.strip()])

    if not account_ids:
        error("Please provide at least one account identifier (--account or --accounts)")
        sys.exit(1)

    # ── API Key ──
    api_key = get_api_key()
    if not api_key:
        error("API Key not found. Please set the REDFOX_API_KEY environment variable")
        print(f"  Get a key: https://redfox.hk/settings/api-keys?source=github")
        print(f"  How to set: export REDFOX_API_KEY=ak_your_key")
        sys.exit(1)

    # ── Create downloader ──
    downloader = downloader_cls(api_key)

    # ── Validate account identifiers ──
    invalid_ids = []
    for aid in account_ids:
        valid, msg = downloader.validate_account_id(aid)
        if not valid:
            invalid_ids.append((aid, msg))

    if invalid_ids:
        print(f"\n{RED}{BOLD}⚠️ The following inputs are not valid {platform_label} account identifiers:{RESET}\n")
        for aid, msg in invalid_ids:
            print(f"  {YELLOW}• {msg}{RESET}\n")
        print(f"{CYAN}💡 {downloader.description_hint()}{RESET}\n")
        sys.exit(2)

    # ── Download directory ──
    output_dir = args.output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    if args.download:
        os.makedirs(output_dir, exist_ok=True)

    # ── Banner ──
    print(f"""{CYAN}{BOLD}
  ╔══════════════════════════════════════════╗
  ║     Multi-Platform Account Video         ║
  ║     Extractor                            ║
  ╚══════════════════════════════════════════╝{RESET}
""")
    info(f"Platform: {platform_label} | API Key loaded | accounts: {len(account_ids)} | works/account: {min(args.count, MAX_PAGE_SIZE)}")

    all_accounts = []
    all_results = []

    for idx, account_id in enumerate(account_ids):
        if idx > 0:
            print(f"\n{CYAN}{'─' * 50}{RESET}\n")

        account, results = process_account(
            downloader,
            account_id,
            page_size=args.count,
            page_num=args.page,
            date_start=args.date_start or "",
            date_end=args.date_end or "",
            rate_limit=args.rate_limit,
            do_download=args.download,
            output_dir=output_dir,
        )
        all_accounts.append(account)
        all_results.append((account, results))

    # ── Output results ──
    print(f"\n{CYAN}{BOLD}{'=' * 50}{RESET}\n")

    if args.json:
        output = {
            "platform": platform_cfg["label"],
            "platform_key": args.platform,
            "accounts": [],
            "total_works": 0,
            "total_success": 0,
            "total_failed": 0,
            "generated_at": datetime.now().isoformat(),
        }
        for account, results in all_results:
            output["accounts"].append({
                "account": account,
                "total": len(results),
                "success": sum(1 for r in results if r.get("download_success")),
                "failed": sum(1 for r in results if not r.get("download_success")),
                "results": results,
            })
            output["total_works"] += len(results)
            output["total_success"] += sum(1 for r in results if r.get("download_success"))
            output["total_failed"] += sum(1 for r in results if not r.get("download_success"))
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for account, results in all_results:
            if results:
                print_markdown_table(downloader, account, results, page_num=args.page, page_size=args.count)
            else:
                name = account.get("accountName", account.get("accountId", "unknown"))
                warn(f"@{name}: no works or fetch failed")

        total_works = sum(len(r) for _, r in all_results)
        total_success = sum(sum(1 for x in r if x.get("download_success")) for _, r in all_results)
        total_failed = total_works - total_success
        print(f"\n{BOLD}Total:{RESET} {len(account_ids)} accounts, {total_works} works, {total_success} succeeded, {total_failed} failed")

    if args.download:
        info(f"Video files saved to: {os.path.abspath(output_dir)}")

    total_success_final = sum(sum(1 for x in r if x.get("download_success")) for _, r in all_results)
    total_works_final = sum(len(r) for _, r in all_results)
    sys.exit(0 if total_success_final == total_works_final else 1)


if __name__ == "__main__":
    main()
