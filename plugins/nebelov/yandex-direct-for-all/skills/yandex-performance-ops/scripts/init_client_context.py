#!/usr/bin/env python3
"""Write a starter local client context file for yandex-performance-ops."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


TEMPLATE = {
    "client_key": "replace-me",
    "notes": "Keep secrets in env vars. Keep IDs, routing, and product context here.",
    "analytics": {
        "source_priority": ["roistat", "metrika", "direct_reports", "wordstat"],
        "roistat_first": True,
        "manual_analysis_required": True,
        "roistat_attribution": ["first_click", "last_click"],
    },
    "analysis": {
        "keywords_manual_only": True,
        "analysis_scripts_forbidden": True,
        "roistat_keyword_analysis_manual_only": True,
    },
    "direct": {
        "login": "",
        "tracking_params": "utm_source=yandex&utm_medium=cpc&utm_campaign={campaign_name}&utm_content={ad_id}&utm_term={keyword}",
        "regions": [225],
        "counter_ids": [],
        "priority_goals": [],
        "campaign_defaults": {
            "daily_budget_micros": 500000000,
            "negative_keywords": ["скачать", "бесплатно", "вакансия"],
            "time_targeting": {"days": [1, 2, 3, 4, 5, 6, 7], "start_hour": 7, "end_hour": 22},
            "search_placement_types": {
                "SearchResults": "YES",
                "ProductGallery": "NO",
                "DynamicPlaces": "YES",
                "Maps": "NO",
                "SearchOrganizationList": "NO"
            },
            "network_strategy": "SERVING_OFF",
            "offer_retargeting": "NO"
        }
    },
    "metrika": {"counter_id": "", "goal_id": ""},
    "wordstat": {"regions": [225], "devices": ["all"]},
    "roistat": {
        "enabled": False,
        "api_key_env": "ROISTAT_API_KEY",
        "project_env": "ROISTAT_PROJECT",
        "base_url": "https://cloud.roistat.com/api/v1",
        "marker_level_1": "direct3",
        "marker_level_2_search": "search"
    },
    "yougile": {"project_id": "", "legacy_board_id": "", "boards": []},
    "search_routing": {
        "routing_map_path": "",
        "cluster_map_path": "semantics/<product>/cluster-map.tsv",
        "campaign_id_map_path": "",
        "campaign_ids": {}
    },
    "collector_defaults": {
        "operational_window_days": 2,
        "goal_id": "",
        "rsya_campaign_ids": []
    },
    "references": {
        "product_maps": [],
        "local_skill_paths": [],
        "rules": [],
        "docs": []
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".codex/yandex-performance-client.json")
    parser.add_argument("--client-key", default="replace-me")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    output = Path(os.path.expanduser(args.output)).resolve()
    if output.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {output}. Use --force.")

    data = dict(TEMPLATE)
    data["client_key"] = args.client_key
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output.parent, 0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        os.chmod(output, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("Локальный контекст создан")


if __name__ == "__main__":
    main()
