#!/usr/bin/env python3
"""Полный читающий снимок управляющих сущностей Яндекс.Директа."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from check_access_paths import (
    PageManifest,
    PageResult,
    atomic_write_json,
    fetch_direct_pages,
    load_direct_access,
    sanitize_error,
)


def _ids(raw: str) -> list[int]:
    values = []
    for part in (raw or "").split(","):
        part = part.strip()
        if part:
            if not part.isdigit():
                raise ValueError("Номера кампаний должны быть целыми числами")
            values.append(int(part))
    return values


def _write_result(root: Path, name: str, result: PageResult) -> dict[str, Any]:
    atomic_write_json(root / f"{name}.json", result.rows)
    manifest = asdict(result.manifest)
    atomic_write_json(root / f"{name}.manifest.json", manifest)
    return manifest


def collect(access_file: str | None, output_dir: Path, campaign_ids: list[int], name_pattern: str = "") -> dict[str, Any]:
    access = load_direct_access(access_file)
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_dir, 0o700)

    campaign_params: dict[str, Any] = {
        "SelectionCriteria": {"Ids": campaign_ids} if campaign_ids else {},
        "FieldNames": ["Id", "Name", "Type", "State", "Status", "StartDate", "EndDate", "NegativeKeywords"],
        "UnifiedCampaignFieldNames": ["CounterIds", "NegativeKeywordSharedSetIds", "TrackingParams"],
    }
    campaigns = fetch_direct_pages(access, "campaigns", campaign_params, "Campaigns", version="v501")
    if name_pattern:
        pattern = re.compile(name_pattern, re.IGNORECASE)
        campaigns.rows = [row for row in campaigns.rows if pattern.search(str(row.get("Name", "")))]
        campaigns.manifest.objects = len(campaigns.rows)
    selected = [int(row["Id"]) for row in campaigns.rows if row.get("Id") is not None]

    manifests: dict[str, Any] = {"campaigns": _write_result(output_dir, "campaigns", campaigns)}
    if not campaigns.manifest.complete:
        overall = {"complete": False, "sources": manifests, "error": campaigns.manifest.error}
        atomic_write_json(output_dir / "manifest.json", overall)
        return overall

    if not selected:
        for service, key in [
            ("adgroups", "AdGroups"), ("ads", "Ads"), ("keywords", "Keywords"),
            ("bids", "Bids"), ("keywordbids", "KeywordBids"), ("sitelinks", "SitelinksSets"),
            ("adextensions", "AdExtensions"), ("negativekeywordsharedsets", "NegativeKeywordSharedSets"),
        ]:
            result = PageResult([], PageManifest(service, key, 0, 0, True, campaigns.manifest.checksum))
            manifests[service] = _write_result(output_dir, service, result)
        overall = {"complete": True, "campaigns_selected": 0, "sources": manifests}
        atomic_write_json(output_dir / "manifest.json", overall)
        return overall

    selection = {"CampaignIds": selected}
    requests = [
        ("adgroups", "AdGroups", "v501", {"SelectionCriteria": selection, "FieldNames": ["Id", "Name", "CampaignId", "Status", "ServingStatus", "RegionIds", "NegativeKeywords", "NegativeKeywordSharedSetIds"]}),
        ("ads", "Ads", "v5", {"SelectionCriteria": selection, "FieldNames": ["Id", "AdGroupId", "CampaignId", "Type", "State", "Status"], "TextAdFieldNames": ["Title", "Title2", "Text", "Href", "SitelinkSetId", "AdExtensions"]}),
        ("keywords", "Keywords", "v5", {"SelectionCriteria": selection, "FieldNames": ["Id", "AdGroupId", "CampaignId", "Keyword", "State", "Status", "Bid", "ContextBid", "StrategyPriority", "UserParam1", "UserParam2"]}),
        ("bids", "Bids", "v5", {"SelectionCriteria": selection, "FieldNames": ["KeywordId", "AdGroupId", "CampaignId", "Bid", "ContextBid", "StrategyPriority"]}),
        ("keywordbids", "KeywordBids", "v5", {"SelectionCriteria": selection, "FieldNames": ["KeywordId", "AdGroupId", "CampaignId", "Bid", "ContextBid", "StrategyPriority"]}),
    ]
    collected: dict[str, PageResult] = {}
    for service, key, version, params in requests:
        result = fetch_direct_pages(access, service, params, key, version=version)
        collected[service] = result
        manifests[service] = _write_result(output_dir, service, result)

    sitelink_ids = sorted({int(text["SitelinkSetId"]) for row in collected["ads"].rows for text in [row.get("TextAd") or {}] if text.get("SitelinkSetId")})
    extension_ids = sorted({int(item["AdExtensionId"]) for row in collected["ads"].rows for text in [row.get("TextAd") or {}] for item in (text.get("AdExtensions") or []) if isinstance(item, dict) and item.get("AdExtensionId")})
    negative_ids = {int(item) for row in campaigns.rows for item in ((row.get("UnifiedCampaign") or {}).get("NegativeKeywordSharedSetIds") or {}).get("Items", [])}
    negative_ids.update(int(item) for row in collected["adgroups"].rows for item in ((row.get("NegativeKeywordSharedSetIds") or {}).get("Items", []) if isinstance(row.get("NegativeKeywordSharedSetIds"), dict) else (row.get("NegativeKeywordSharedSetIds") or [])))
    negative_ids = sorted(negative_ids)
    referenced = [
        ("sitelinks", "SitelinksSets", {"SelectionCriteria": {"Ids": sitelink_ids}, "FieldNames": ["Id"], "SitelinkFieldNames": ["Title", "Href", "Description"]}),
        ("adextensions", "AdExtensions", {"SelectionCriteria": {"Ids": extension_ids}, "FieldNames": ["Id", "Type", "Status"], "CalloutFieldNames": ["CalloutText"]}),
        ("negativekeywordsharedsets", "NegativeKeywordSharedSets", {"SelectionCriteria": {"Ids": negative_ids}, "FieldNames": ["Id", "Name", "NegativeKeywords"]}),
    ]
    for service, key, params in referenced:
        if not params["SelectionCriteria"]["Ids"]:
            result = PageResult(rows=[], manifest=PageManifest(service, key, 0, 0, True, campaigns.manifest.checksum))
        else:
            result = fetch_direct_pages(access, service, params, key, version="v5")
        manifests[service] = _write_result(output_dir, service, result)

    complete = all(bool(item.get("complete")) for item in manifests.values())
    overall = {"complete": complete, "campaigns_selected": len(selected), "sources": manifests}
    atomic_write_json(output_dir / "manifest.json", overall)
    return overall


def main() -> int:
    parser = argparse.ArgumentParser(description="Собрать безопасный снимок сущностей Яндекс.Директа")
    parser.add_argument("--access-file", help="Защищённый файл доступа; можно использовать YANDEX_DIRECT_ACCESS_FILE")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--campaign-ids", default="")
    parser.add_argument("--name-regex", default="")
    args = parser.parse_args()
    if any(item in {"--token", "--direct-token"} for item in sys.argv[1:]):
        parser.error("сырой токен в командной строке запрещён")
    try:
        result = collect(args.access_file, Path(args.output_dir), _ids(args.campaign_ids), args.name_regex)
    except Exception as exc:
        print(f"Снимок не собран: {sanitize_error(exc)}", file=sys.stderr)
        return 1
    print("Снимок собран полностью" if result["complete"] else "Снимок собран частично")
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
