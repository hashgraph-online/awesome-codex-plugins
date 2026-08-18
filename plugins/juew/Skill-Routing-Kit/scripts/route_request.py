#!/usr/bin/env python3
"""Route a user request against a local Skill Routing Kit registry.

This script is intentionally local, read-only, and conservative by default.
It does not call external connectors or inspect connector content.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GENERATED = ROOT / "registry" / "capabilities.generated.json"
DEFAULT_CORE = ROOT / "registry" / "core-capabilities.json"
STALE_DAYS = 7


TOKEN_RE = re.compile(r"[\w.+#/-]+", re.UNICODE)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def tokenize(text: str) -> set[str]:
    text = text.lower()
    raw = set(TOKEN_RE.findall(text))
    expanded = set(raw)
    aliases = {
        "ppt": "presentation",
        "pptx": "presentation",
        "slides": "presentation",
        "slide": "presentation",
        "word": "document",
        "docx": "document",
        "excel": "spreadsheet",
        "xlsx": "spreadsheet",
        "csv": "spreadsheet",
        "pdf": "pdf",
        "bug": "debug",
        "error": "debug",
        "failing": "debug",
        "test": "testing",
        "tests": "testing",
        "frontend": "frontend",
        "web": "web_app",
        "github": "github",
        "gmail": "gmail",
        "drive": "drive",
        "canva": "canva",
        "figma": "figma",
        "slack": "slack",
        "linear": "linear",
        "agent": "orchestration",
        "agents": "orchestration",
    }
    for token in list(raw):
        if token in aliases:
            expanded.add(aliases[token])
    return expanded


def infer_intents(request: str) -> dict[str, set[str]]:
    text = request.lower()
    artifacts: set[str] = set()
    processes: set[str] = set()
    sources: set[str] = set()

    if any(token in text for token in ["ppt", "pptx", "slide", "slides", "deck", "幻灯", "路演"]):
        artifacts.add("presentation")
    if any(token in text for token in ["pdf"]):
        artifacts.add("pdf")
    if any(token in text for token in ["docx", "word", "文档", "报告"]):
        artifacts.add("document")
    if any(token in text for token in ["xlsx", "excel", "csv", "spreadsheet", "表格"]):
        artifacts.add("spreadsheet")
    if any(token in text for token in ["web", "frontend", "react", "网页", "前端", "看板"]):
        artifacts.add("web_app")
    if any(token in text for token in ["image", "poster", "海报", "图片"]):
        artifacts.add("image")

    if any(token in text for token in ["bug", "error", "failing", "报错", "失败", "修复"]):
        processes.add("debugging")
    if any(token in text for token in ["test", "测试"]):
        processes.add("testing")
    if any(token in text for token in ["review", "审核", "评审"]):
        processes.add("review")
    if any(token in text for token in ["plan", "计划", "方案"]):
        processes.add("planning")
    if any(token in text for token in ["agent", "agents", "subagent", "多 agent", "多agent"]):
        processes.add("orchestration")
    if any(
        token in text
        for token in [
            "没命中",
            "未命中",
            "没有命中",
            "命中",
            "触发",
            "routing",
            "router",
            "route",
            "registry",
            "did not trigger",
            "didn't trigger",
            "not trigger",
            "路由",
        ]
    ):
        processes.add("routing")

    for source in ["github", "gmail", "drive", "notion", "slack", "figma", "linear", "canva"]:
        if source in text:
            sources.add(source)

    return {"artifacts": artifacts, "processes": processes, "sources": sources}


def load_registry(path: Path | None) -> tuple[dict[str, Any] | None, Path]:
    if path:
        registry_path = path
    elif DEFAULT_GENERATED.exists():
        registry_path = DEFAULT_GENERATED
    else:
        registry_path = DEFAULT_CORE

    if not registry_path.exists():
        return None, registry_path

    with registry_path.open("r", encoding="utf-8") as f:
        return json.load(f), registry_path


def registry_warnings(registry: dict[str, Any] | None, path: Path) -> list[str]:
    warnings: list[str] = []
    if registry is None or not path.exists():
        return [f"Registry not found: {path}"]

    generated_at = parse_time(registry.get("generated_at"))
    if generated_at:
        age_days = (now_utc() - generated_at.astimezone(timezone.utc)).days
        if age_days > STALE_DAYS:
            warnings.append(
                f"Registry is stale ({age_days} days old). Refresh with scripts/build_registry.py."
            )
    else:
        warnings.append("Registry has no parseable generated_at timestamp.")

    if registry.get("schema_version") != "1.0":
        warnings.append(
            f"Registry schema_version is {registry.get('schema_version')!r}; expected '1.0'."
        )

    missing_sources = []
    for card in registry.get("capabilities", []):
        provenance = card.get("provenance", {})
        source_path = provenance.get("path")
        source_type = provenance.get("source_type")
        if source_path and source_type != "core_static":
            expanded = Path(os.path.expanduser(source_path))
            if not expanded.exists():
                missing_sources.append(source_path)
    if missing_sources:
        warnings.append(
            f"{len(missing_sources)} capability source path(s) are missing; run --check-registry --debug."
        )

    return warnings


def text_blob(card: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("id", "name", "use_when"):
        value = card.get(key)
        if isinstance(value, str):
            values.append(value)
    for key in ("categories", "inputs", "outputs", "requires", "examples"):
        value = card.get(key, [])
        if isinstance(value, list):
            values.extend(str(item) for item in value)
    return " ".join(values).lower()


def score_card(
    card: dict[str, Any],
    request: str,
    request_tokens: set[str],
    intents: dict[str, set[str]],
) -> tuple[int, list[str], list[str]]:
    score = 0
    reasons: list[str] = []
    do_not_use: list[str] = []
    blob = text_blob(card)
    blob_tokens = tokenize(blob)
    overlap = request_tokens & blob_tokens
    if overlap:
        score += min(len(overlap) * 4, 24)
        reasons.append("matched terms: " + ", ".join(sorted(list(overlap))[:8]))

    card_id = str(card.get("id", "")).lower()
    name = str(card.get("name", "")).lower()
    if card_id and card_id in request.lower():
        score += 25
        reasons.append("explicit capability id mentioned")
    if name and name in request.lower():
        score += 20
        reasons.append("explicit capability name mentioned")

    categories = set(str(c).lower() for c in card.get("categories", []))
    outputs = set(str(o).lower() for o in card.get("outputs", []))

    for artifact in intents["artifacts"]:
        if artifact in categories or artifact in outputs:
            boost = 35 if artifact != "pdf" else 8
            score += boost
            reasons.append(f"matches inferred artifact target: {artifact}")

    for process in intents["processes"]:
        if process == "routing":
            continue
        if process in categories:
            score += 45
            reasons.append(f"matches inferred process need: {process}")

    is_skill_router = card_id == "skill-router" or name == "skill router" or name == "skill-router"
    if "routing" in intents["processes"] and is_skill_router:
        score += 120
        reasons.append("routing diagnostic request prefers the skill-router capability")
    elif "routing" in intents["processes"] and "routing" in categories:
        score += 30 if card_id == "skill-routing-kit" else 10
        reasons.append("matches inferred process need: routing")
    elif "routing" in intents["processes"] and "routing" not in categories:
        score -= 30
        reasons.append("routing diagnostic request prefers the skill-router capability")

    if "debugging" in intents["processes"] and "debugging" not in categories and "process" not in categories:
        score -= 18
        reasons.append("debugging request prefers a process/debugging primary skill")

    for source in intents["sources"]:
        if source == card_id or source in categories:
            score += 35
            reasons.append(f"matches explicit source/connector: {source}")

    if "presentation" in intents["artifacts"] and "pdf" in categories and "pdf" in request.lower():
        score -= 35
        do_not_use.append("PDF appears to be an input; presentation is the final artifact.")

    if "spreadsheet" in intents["artifacts"] and "pdf" in categories:
        score -= 25
        do_not_use.append("PDF is not the final spreadsheet artifact.")

    if "external_connector" in categories or "connector" in categories or "requires_auth" in categories:
        explicit = any(source in request.lower() for source in [card_id, name, "github", "gmail", "drive", "canva", "figma", "slack", "linear", "notion"])
        if explicit:
            reasons.append("external connector explicitly referenced")
        else:
            score -= 12
            reasons.append("external connector not explicitly referenced")

    for avoid in card.get("avoid_when", []):
        avoid_tokens = tokenize(str(avoid))
        if avoid_tokens and len(avoid_tokens & request_tokens) >= 2:
            score -= 20
            do_not_use.append(str(avoid))

    if "local" in categories and not any(x in request.lower() for x in ["github", "gmail", "drive", "canva", "figma", "slack", "linear", "notion"]):
        score += 5
        reasons.append("local-first preference")

    return score, reasons, do_not_use


def route_request(request: str, registry: dict[str, Any], debug: bool) -> dict[str, Any]:
    request_tokens = tokenize(request)
    intents = infer_intents(request)
    scored = []
    for card in registry.get("capabilities", []):
        score, reasons, do_not_use = score_card(card, request, request_tokens, intents)
        if score > 0 or debug:
            scored.append(
                {
                    "id": card.get("id"),
                    "name": card.get("name"),
                    "kind": card.get("kind"),
                    "categories": card.get("categories", []),
                    "score": score,
                    "reasons": reasons,
                    "do_not_use": do_not_use,
                    "requires": card.get("requires", []),
                }
            )

    scored.sort(key=lambda item: item["score"], reverse=True)
    positive = [item for item in scored if item["score"] > 0]
    primary = positive[0] if positive else None
    helpers = [
        item
        for item in positive[1:]
        if item["score"] >= 20 or item.get("do_not_use")
    ][:3] if primary else []

    needs_confirmation = []
    for item in ([primary] if primary else []) + helpers:
        if not item:
            continue
        requires = set(str(r).lower() for r in item.get("requires", []))
        categories = set(str(c).lower() for c in item.get("categories", []))
        if "connector_auth" in requires or "requires_auth" in categories:
            needs_confirmation.append(f"{item['name']} access/authentication")

    result: dict[str, Any] = {
        "recommended": primary,
        "helpers": helpers,
        "needs_confirmation": needs_confirmation,
    }
    if debug:
        result["candidates"] = scored[:12]
    return result


def print_route(result: dict[str, Any], warnings: list[str], debug: bool) -> None:
    if warnings:
        print("Registry warnings:")
        for warning in warnings:
            print(f"- {warning}")
        print()

    recommended = result.get("recommended")
    print("Recommended skill/plugin:")
    if recommended:
        print(f"- {recommended['name']} ({recommended['id']})")
    else:
        print("- None with confidence. Use native judgment or ask for clarification.")
    print()

    print("Helper skills/plugins:")
    helpers = result.get("helpers") or []
    if helpers:
        for helper in helpers:
            print(f"- {helper['name']} ({helper['id']})")
    else:
        print("- None")
    print()

    print("Why:")
    if recommended and recommended.get("reasons"):
        for reason in recommended["reasons"]:
            print(f"- {reason}")
    else:
        print("- No strong registry match.")
    print()

    print("Do not use:")
    do_not = recommended.get("do_not_use", []) if recommended else []
    if do_not:
        for item in do_not:
            print(f"- {item}")
    else:
        print("- None from the selected card.")
    print()

    print("Needs confirmation:")
    confirmations = result.get("needs_confirmation", [])
    if confirmations:
        for item in confirmations:
            print(f"- {item}")
    else:
        print("- None")

    if debug:
        print()
        print("Debug candidates:")
        for candidate in result.get("candidates", []):
            print(f"- {candidate['score']:>3} {candidate['id']}: {', '.join(candidate.get('reasons', []))}")


def check_registry(registry: dict[str, Any] | None, path: Path, debug: bool) -> int:
    print(f"Registry: {path}")
    print(f"Schema: {registry.get('schema_version') if registry else None}")
    print(f"Generated at: {registry.get('generated_at') if registry else None}")
    print(f"Capabilities: {len(registry.get('capabilities', [])) if registry else 0}")
    warnings = registry_warnings(registry, path)
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("Warnings: none")
    if debug and registry:
        for card in registry.get("capabilities", []):
            provenance = card.get("provenance", {})
            print(f"- {card.get('id')}: {provenance.get('source_type')} {provenance.get('path')}")
    return 1 if warnings else 0


def refresh_registry(output: Path | None = None) -> int:
    script = ROOT / "scripts" / "build_registry.py"
    if not script.exists():
        print(f"Cannot refresh; build script not found: {script}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(script), "--yes"]
    if output is not None:
        cmd.extend(["--output", str(output)])
    return subprocess.call(cmd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route a request using a local Skill Routing Kit registry.")
    parser.add_argument("request", nargs="?", help="User request to route.")
    parser.add_argument("--registry", type=Path, help="Registry JSON path.")
    parser.add_argument("--debug", action="store_true", help="Show candidates and detailed reasons.")
    parser.add_argument("--check-registry", action="store_true", help="Check registry freshness and provenance.")
    parser.add_argument("--refresh", action="store_true", help="Explicitly rebuild the registry before routing/checking.")
    args = parser.parse_args(argv)

    if args.refresh:
        refresh_output = args.registry if args.registry else DEFAULT_GENERATED
        status = refresh_registry(refresh_output)
        if status != 0:
            return status

    registry, registry_path = load_registry(args.registry)

    if args.check_registry:
        return check_registry(registry, registry_path, args.debug)

    if not args.request:
        parser.error("request is required unless --check-registry is used")

    warnings = registry_warnings(registry, registry_path)
    if registry is None:
        print_route({"recommended": None, "helpers": [], "needs_confirmation": []}, warnings, args.debug)
        return 1
    result = route_request(args.request, registry, args.debug)
    print_route(result, warnings, args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
