#!/usr/bin/env python3
"""
Collect short-window Direct raw data for operational precheck.

Use when a task needs fresh local-only bundles for:
- ExcludedSites rotation in RSYA
- short-window placement review
- ad outsider shortlists

This script does NOT apply changes. It only fetches live raw data.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

from dataclasses import asdict
from pathlib import Path

from check_access_paths import DirectAccess, fetch_direct_pages, fetch_direct_report, load_direct_access

API_V5 = "https://api.direct.yandex.com/json/v5"
API_V501 = "https://api.direct.yandex.com/json/v501"


def parse_ids(raw):
    ids = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        ids.append(int(part))
    return ids


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def api_call(endpoint, method, params, token, login, version="v501", environment="production"):
    host = "api-sandbox.direct.yandex.com" if environment == "sandbox" else "api.direct.yandex.com"
    base = f"https://{host}/json/{version}"
    url = f"{base}/{endpoint}"
    body = json.dumps({"method": method, "params": params}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept-Language": "ru",
    }
    if login:
        headers["Client-Login"] = login
    attempt = 0
    while True:
        req = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="ignore")
            print(f"API ERROR {exc.code}: {payload[:400]}", file=sys.stderr)
            return {"error": payload}
        except Exception as exc:
            attempt += 1
            print(f"API RETRY {attempt}: {type(exc).__name__}", file=sys.stderr)
            time.sleep(5)


def report_call(
    report_type,
    fields,
    date_from,
    date_to,
    campaign_id,
    token,
    login,
    report_name,
    output_dir,
    extra_filters=None,
    goals=None,
    attribution_models=None,
    environment="production",
):
    params = {
        "SelectionCriteria": {
            "DateFrom": date_from,
            "DateTo": date_to,
            "Filter": [
                {"Field": "CampaignId", "Operator": "EQUALS", "Values": [str(campaign_id)]},
            ],
        },
        "FieldNames": fields,
        "ReportName": report_name,
        "ReportType": report_type,
        "DateRangeType": "CUSTOM_DATE",
        "Format": "TSV",
        "IncludeVAT": "YES",
        "IncludeDiscount": "NO",
    }
    if extra_filters:
        params["SelectionCriteria"]["Filter"].extend(extra_filters)
    if goals:
        params["Goals"] = goals
    if attribution_models:
        params["AttributionModels"] = attribution_models
    access = DirectAccess(token=token, client_login=login, environment=environment)
    state = fetch_direct_report(access, params, Path(output_dir))
    if state.get("status") != "ready":
        raise RuntimeError(f"Report {report_type} cid={campaign_id} не готов: {state.get('status')}")
    return Path(state["artifact_path"]).read_text(encoding="utf-8")


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def save_text(data, path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)


def prepend_column(tsv_text, header_name, value):
    lines = [line for line in tsv_text.splitlines() if line]
    if not lines:
        return f"{header_name}\n"
    out = [f"{header_name}\t{lines[0]}"]
    for line in lines[1:]:
        out.append(f"{value}\t{line}")
    return "\n".join(out) + "\n"


def merge_tsv_files(paths, output_path):
    merged = []
    header_written = False
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            lines = [line.rstrip("\n") for line in fh if line.strip()]
        if not lines:
            continue
        if not header_written:
            merged.append(lines[0])
            header_written = True
        merged.extend(lines[1:])
    if merged:
        save_text("\n".join(merged) + "\n", output_path)


def collect_campaign_meta(campaign_ids, access, outdir):
    if not campaign_ids:
        return None
    page = fetch_direct_pages(
        access,
        "campaigns",
        {
            "SelectionCriteria": {"Ids": campaign_ids},
            "FieldNames": [
                "Id",
                "Name",
                "Type",
                "Status",
                "State",
                "StartDate",
                "DailyBudget",
                "NegativeKeywords",
                "ExcludedSites",
                "TimeTargeting",
            ],
            "UnifiedCampaignFieldNames": [
                "BiddingStrategy",
                "CounterIds",
                "PriorityGoals",
                "TrackingParams",
                "Settings",
                "NegativeKeywordSharedSetIds",
            ],
            "UnifiedCampaignSearchStrategyPlacementTypesFieldNames": [
                "SearchResults",
                "ProductGallery",
                "DynamicPlaces",
                "Maps",
                "SearchOrganizationList",
            ],
        },
        version="v501",
        result_key="Campaigns",
    )
    result = {"result": {"Campaigns": page.rows}, "manifest": asdict(page.manifest)}
    path = os.path.join(outdir, "campaigns_meta.json")
    save_json(result, path)
    return path


def collect_report_group(
    campaign_ids,
    report_type,
    fields,
    stem,
    date_from,
    date_to,
    token,
    login,
    outdir,
    extra_filters=None,
    goals=None,
    attribution_models=None,
    environment="production",
):
    files = []
    for campaign_id in campaign_ids:
        report_name = f"{stem}_{campaign_id}_{int(time.time())}"
        tsv = report_call(
            report_type,
            fields,
            date_from,
            date_to,
            campaign_id,
            token,
            login,
            report_name,
            outdir,
            extra_filters=extra_filters,
            goals=goals,
            attribution_models=attribution_models,
            environment=environment,
        )
        prefixed = prepend_column(tsv, "CampaignId", campaign_id)
        path = os.path.join(outdir, f"{stem}_{campaign_id}.tsv")
        save_text(prefixed, path)
        files.append(path)
        time.sleep(1)
    if files:
        merge_tsv_files(files, os.path.join(outdir, f"all_{stem}.tsv"))
    return files


def collect_live_ads(campaign_ids, access, outdir):
    files = []
    all_ads = []
    for campaign_id in campaign_ids:
        page = fetch_direct_pages(
            access,
            "ads",
            {
                "SelectionCriteria": {"CampaignIds": [campaign_id]},
                "FieldNames": ["Id", "CampaignId", "AdGroupId", "Status", "State", "Type"],
                "TextAdFieldNames": [
                    "Title",
                    "Title2",
                    "Text",
                    "Href",
                    "DisplayUrlPath",
                    "SitelinkSetId",
                    "AdExtensions",
                    "AdImageHash",
                    "Mobile",
                ],
            },
            version="v501",
            result_key="Ads",
        )
        if not page.manifest.complete:
            raise RuntimeError(page.manifest.error)
        ads = page.rows
        all_ads.extend(ads)
        path = os.path.join(outdir, f"source_ads_{campaign_id}.json")
        save_json(ads, path)
        files.append(path)
        time.sleep(1)
    if files:
        save_json(all_ads, os.path.join(outdir, "all_source_ads.json"))
    return files, all_ads


def collect_ad_images(all_ads, token, login, outdir, environment="production"):
    hashes = []
    seen = set()
    for ad in all_ads:
        for ad_type in ("TextAd", "TextImageAd"):
            image_hash = str(((ad.get(ad_type) or {}).get("AdImageHash") or "")).strip()
            if not image_hash or image_hash in seen:
                continue
            seen.add(image_hash)
            hashes.append(image_hash)
    rows = []
    for index in range(0, len(hashes), 10000):
        batch = hashes[index:index + 10000]
        if not batch:
            continue
        result = api_call(
            "adimages",
            "get",
            {
                "SelectionCriteria": {"AdImageHashes": batch},
                "FieldNames": ["AdImageHash", "Name", "PreviewUrl", "OriginalUrl"],
            },
            token,
            login,
            version="v5",
            environment=environment,
        )
        rows.extend(result.get("result", {}).get("AdImages", []))
        time.sleep(1)
    save_json(rows, os.path.join(outdir, "all_ad_images.json"))
    return rows


def build_summary(meta_path, placements_dir, ads_dir, ad_texts_dir, output_path):
    summary = {
        "campaigns_meta": meta_path,
        "placements_dir": placements_dir if os.path.isdir(placements_dir) else None,
        "ads_dir": ads_dir if os.path.isdir(ads_dir) else None,
        "ad_texts_dir": ad_texts_dir if os.path.isdir(ad_texts_dir) else None,
        "ad_images_path": os.path.join(ad_texts_dir, "all_ad_images.json") if ad_texts_dir and os.path.exists(os.path.join(ad_texts_dir, "all_ad_images.json")) else None,
    }
    if meta_path and os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        rows = []
        for camp in data.get("result", {}).get("Campaigns", []):
            excluded_raw = camp.get("ExcludedSites") or {}
            excluded = excluded_raw.get("Items", []) if isinstance(excluded_raw, dict) else []
            rows.append(
                {
                    "id": camp.get("Id"),
                    "name": camp.get("Name"),
                    "state": camp.get("State"),
                    "status": camp.get("Status"),
                    "excluded_sites_count": len(excluded),
                    "excluded_sites_free_slots": max(0, 1000 - len(excluded)),
                }
            )
        summary["campaigns"] = rows
    save_json(summary, output_path)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="Collect short-window operational Direct raw bundle")
    parser.add_argument("--access-file", help="Защищённый файл доступа Директа")
    parser.add_argument("--date-from", required=True, help="DateFrom YYYY-MM-DD")
    parser.add_argument("--date-to", required=True, help="DateTo YYYY-MM-DD")
    parser.add_argument("--search-campaigns", default="", help="Comma-separated search campaign ids")
    parser.add_argument("--rsy-campaigns", default="", help="Comma-separated RSYA campaign ids")
    parser.add_argument("--goal-id", default="", help="Optional Direct goal id for placement conversions")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument(
        "--mode",
        default="all",
        choices=["all", "meta", "placements", "ads"],
        help="Which raw blocks to collect",
    )
    args = parser.parse_args()
    access = load_direct_access(args.access_file)
    token, login = access.token, access.client_login

    search_campaigns = parse_ids(args.search_campaigns)
    rsy_campaigns = parse_ids(args.rsy_campaigns)
    all_campaigns = sorted(set(search_campaigns + rsy_campaigns))

    ensure_dir(args.output_dir)
    placements_dir = os.path.join(args.output_dir, "placements")
    ads_dir = os.path.join(args.output_dir, "ads")
    ad_texts_dir = os.path.join(args.output_dir, "ad_texts")
    if args.mode in ("all", "placements"):
        ensure_dir(placements_dir)
    if args.mode in ("all", "ads"):
        ensure_dir(ads_dir)
        ensure_dir(ad_texts_dir)

    meta_path = None
    if args.mode in ("all", "meta", "placements") and all_campaigns:
        print(f"Collecting campaign meta for {len(all_campaigns)} campaigns...")
        meta_path = collect_campaign_meta(all_campaigns, access, args.output_dir)

    if args.mode in ("all", "placements") and rsy_campaigns:
        print(f"Collecting PLACEMENT_PERFORMANCE_REPORT for {len(rsy_campaigns)} RSYA campaigns...")
        placement_fields = ["Placement", "Impressions", "Clicks", "Cost", "Ctr", "AvgCpc"]
        placement_goals = None
        placement_attr_models = None
        if args.goal_id:
            placement_fields.extend(["Conversions", "CostPerConversion", "ConversionRate"])
            placement_goals = [args.goal_id]
            placement_attr_models = ["LC"]
        collect_report_group(
            rsy_campaigns,
            "CUSTOM_REPORT",
            placement_fields,
            "placements",
            args.date_from,
            args.date_to,
            token,
            login,
            placements_dir,
            extra_filters=[{"Field": "AdNetworkType", "Operator": "EQUALS", "Values": ["AD_NETWORK"]}],
            goals=placement_goals,
            attribution_models=placement_attr_models,
            environment=access.environment,
        )

    if args.mode in ("all", "ads") and all_campaigns:
        print(f"Collecting AD_PERFORMANCE_REPORT for {len(all_campaigns)} campaigns...")
        ad_fields = ["AdId", "AdGroupId", "AdGroupName", "Impressions", "Clicks", "Cost", "Ctr", "AvgCpc"]
        ad_goals = None
        ad_attr_models = None
        if args.goal_id:
            ad_fields.extend(["Conversions", "CostPerConversion", "ConversionRate"])
            ad_goals = [args.goal_id]
            ad_attr_models = ["LC"]
        collect_report_group(
            all_campaigns,
            "AD_PERFORMANCE_REPORT",
            ad_fields,
            "ads",
            args.date_from,
            args.date_to,
            token,
            login,
            ads_dir,
            goals=ad_goals,
            attribution_models=ad_attr_models,
            environment=access.environment,
        )
        print(f"Collecting live ads payload for {len(all_campaigns)} campaigns...")
        collect_live_ads(all_campaigns, access, ad_texts_dir)

    build_summary(
        meta_path,
        placements_dir,
        ads_dir,
        ad_texts_dir,
        os.path.join(args.output_dir, "bundle_summary.json"),
    )
    print("DONE")


if __name__ == "__main__":
    main()
