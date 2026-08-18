#!/usr/bin/env python3
"""Verify live readiness of search campaigns against cluster map and minus words."""

import argparse
import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from check_access_paths import PageManifestStore, fetch_direct_pages, load_direct_access

API_V5 = "https://api.direct.yandex.com/json/v5"
API_V501 = "https://api.direct.yandex.com/json/v501"


def normalize(text: str) -> str:
    text = (text or "").strip().lower()
    return re.sub(r"\s+", " ", text)


def load_cluster_map(path: str) -> Dict[str, Dict[str, Set[str]]]:
    out: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
    with open(path, "r", encoding="utf-8") as f:
        rd = csv.DictReader(f, delimiter="\t")
        for row in rd:
            cname = (row.get("campaign_name") or "").strip()
            gname = (row.get("adgroup_name") or "").strip()
            phrase = normalize(row.get("phrase") or "")
            if cname and gname and phrase:
                out[cname][gname].add(phrase)
    return out


def load_minus_words(path: str) -> List[str]:
    words: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        rd = csv.DictReader(f, delimiter="\t")
        for row in rd:
            w = normalize(row.get("word") or "")
            if w:
                words.append(w)
    seen = set()
    ordered = []
    for w in words:
        if w in seen:
            continue
        seen.add(w)
        ordered.append(w)
    return ordered


def main() -> None:
    os.umask(0o077)
    ap = argparse.ArgumentParser()
    ap.add_argument("--access-file", help="Защищённый файл доступа Директа")
    ap.add_argument("--campaign-ids", required=True, help="comma-separated")
    ap.add_argument("--cluster-map", required=True)
    ap.add_argument("--minus-words", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    access = load_direct_access(args.access_file)
    token, login = access.token, access.client_login

    campaign_ids = [int(x.strip()) for x in args.campaign_ids.split(",") if x.strip()]
    cluster_map = load_cluster_map(args.cluster_map)
    minus_words = load_minus_words(args.minus_words)
    minus_set = set(minus_words)
    campaign_name_to_id = {
        cname: cid for cname, cid in zip(sorted(cluster_map.keys()), sorted(campaign_ids))
    }  # fallback mapping by order

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    report = {"generated_at": datetime.utcnow().isoformat() + "Z", "campaign_ids": campaign_ids}
    manifests = PageManifestStore(Path(args.output).with_name(f"{Path(args.output).stem}.collection-manifest.json"))

    camps_result = manifests.add("campaigns", fetch_direct_pages(
        access,
        "campaigns",
        {"SelectionCriteria": {"Ids": campaign_ids}, "FieldNames": ["Id", "Name", "State", "Status", "NegativeKeywords"]},
        "Campaigns",
        version="v501",
    ))
    if not camps_result.manifest.complete:
        raise RuntimeError(camps_result.manifest.error)
    campaigns = camps_result.rows
    cid_to_name = {c["Id"]: c["Name"] for c in campaigns}
    campaign_name_to_id = {v: k for k, v in cid_to_name.items()}

    ag_result = manifests.add("adgroups", fetch_direct_pages(
        access,
        "adgroups",
        {"SelectionCriteria": {"CampaignIds": campaign_ids}, "FieldNames": ["Id", "Name", "CampaignId"]},
        "AdGroups",
        version="v501",
    ))
    if not ag_result.manifest.complete:
        raise RuntimeError(ag_result.manifest.error)
    adgroups = ag_result.rows

    target_group_ids: Set[int] = set()
    old_group_ids: Set[int] = set()
    expected_phrases_by_gid: Dict[int, Set[str]] = {}
    for g in adgroups:
        gid = g["Id"]
        cname = cid_to_name.get(g["CampaignId"], str(g["CampaignId"]))
        gname = g["Name"]
        if gname in cluster_map.get(cname, {}):
            target_group_ids.add(gid)
            expected_phrases_by_gid[gid] = set(cluster_map[cname][gname])
        else:
            old_group_ids.add(gid)

    kw_result = manifests.add("keywords", fetch_direct_pages(
        access,
        "keywords",
        {
            "SelectionCriteria": {"CampaignIds": campaign_ids},
            "FieldNames": ["Id", "Keyword", "AdGroupId", "CampaignId", "State", "AutotargetingCategories"],
        },
        "Keywords",
        version="v5",
    ))
    if not kw_result.manifest.complete:
        raise RuntimeError(kw_result.manifest.error)
    keywords = kw_result.rows

    on_target_phrases_by_gid: Dict[int, Set[str]] = defaultdict(set)
    missing_target_phrases = []
    old_groups_on_keywords = []
    non_target_on_target_groups = []
    autotarget_violations = []
    autotarget_count = 0
    for kw in keywords:
        gid = kw["AdGroupId"]
        phrase = normalize(kw.get("Keyword"))
        state = kw.get("State")
        if phrase == "---autotargeting":
            if gid in target_group_ids:
                autotarget_count += 1
                cats = {i.get("Category"): i.get("Value") for i in (kw.get("AutotargetingCategories") or {}).get("Items", [])}
                ok = (
                    cats.get("EXACT") == "YES"
                    and cats.get("ALTERNATIVE") == "NO"
                    and cats.get("COMPETITOR") == "NO"
                    and cats.get("BROADER") == "NO"
                    and cats.get("ACCESSORY") == "NO"
                )
                if not ok:
                    autotarget_violations.append({"adgroup_id": gid, "cats": cats})
            continue
        if state != "ON":
            continue
        if gid in target_group_ids:
            on_target_phrases_by_gid[gid].add(phrase)
            if phrase not in expected_phrases_by_gid.get(gid, set()):
                non_target_on_target_groups.append({"adgroup_id": gid, "keyword": kw.get("Keyword")})
        if gid in old_group_ids:
            old_groups_on_keywords.append({"adgroup_id": gid, "keyword": kw.get("Keyword")})

    for gid in sorted(target_group_ids):
        miss = sorted(expected_phrases_by_gid[gid] - on_target_phrases_by_gid.get(gid, set()))
        if miss:
            missing_target_phrases.append({"adgroup_id": gid, "missing_count": len(miss), "sample": miss[:15]})

    minus_checks = {}
    for c in campaigns:
        cid = str(c["Id"])
        live = [normalize(x) for x in ((c.get("NegativeKeywords") or {}).get("Items") or [])]
        live_set = set(live)
        minus_checks[cid] = {
            "count_live": len(live),
            "count_expected": len(minus_words),
            "match_set": live_set == minus_set,
            "missing": sorted(minus_set - live_set)[:20],
            "extra": sorted(live_set - minus_set)[:20],
        }

    critical = []
    if missing_target_phrases:
        critical.append({"check": "missing_target_phrases", "count": len(missing_target_phrases)})
    if old_groups_on_keywords:
        critical.append({"check": "old_groups_on_keywords", "count": len(old_groups_on_keywords)})
    if non_target_on_target_groups:
        critical.append({"check": "non_target_on_target_groups", "count": len(non_target_on_target_groups)})
    if autotarget_violations:
        critical.append({"check": "autotarget_violations", "count": len(autotarget_violations)})
    for cid, chk in minus_checks.items():
        if not chk["match_set"]:
            critical.append({"check": "minus_words_mismatch", "campaign_id": int(cid)})

    report["counts"] = {
        "campaigns": len(campaigns),
        "adgroups_total": len(adgroups),
        "target_adgroups": len(target_group_ids),
        "old_adgroups": len(old_group_ids),
        "keywords_total": len(keywords),
        "target_phrases_expected_total": sum(len(v) for v in expected_phrases_by_gid.values()),
        "target_phrases_on_total": sum(len(v) for v in on_target_phrases_by_gid.values()),
        "autotarget_keywords_target_groups": autotarget_count,
    }
    report["checks"] = {
        "missing_target_phrases": missing_target_phrases,
        "old_groups_on_keywords": old_groups_on_keywords[:100],
        "non_target_on_target_groups": non_target_on_target_groups[:100],
        "autotarget_violations": autotarget_violations,
        "minus_words": minus_checks,
    }
    report["critical_failures"] = critical
    report["overall_ready"] = len(critical) == 0

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps({"status": "ok", "report": args.output, "overall_ready": report["overall_ready"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
