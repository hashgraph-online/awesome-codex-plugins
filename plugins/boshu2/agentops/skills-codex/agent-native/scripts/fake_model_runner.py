#!/usr/bin/env python3
"""Deterministic fake multi-model runner for conformance tests.

Emits canned artifacts for council / idea-genie duel / validate scenarios
without calling codex, ntm, or any real model. Used by
tests/integration/test_multi_model_dispatch.bats.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def council(args: argparse.Namespace) -> int:
    profiles = [p.strip() for p in args.models.split(",") if p.strip()]
    if len(profiles) < 2:
        print("council requires at least two --models", file=sys.stderr)
        return 2
    available = {p.strip() for p in (args.available or "").split(",") if p.strip()}
    unsatisfied = [p for p in profiles if available and p not in available]

    judges = []
    for i, profile in enumerate(profiles, start=1):
        judges.append(
            {
                "id": f"judge-{i}",
                "context_id": f"ctx-judge-{i}-{profile}",
                "model_identity": profile,
                "methodology": "static-reading" if i % 2 else "executing-subject",
                "judgment": "pass" if not unsatisfied else "abstain-disclosed",
                "evidence": [f"fixture://criterion/{i}"],
            }
        )

    report = {
        "schema_version": "council-report.v1",
        "question": args.question or "conformance fixture question",
        "judges": judges,
        "context_ids": [j["context_id"] for j in judges],
        "model_identities": [j["model_identity"] for j in judges],
        "agreement": {
            "cross_model": len({j["model_identity"] for j in judges}) > 1
            and not unsatisfied,
            "single_model_only": bool(unsatisfied)
            or len({j["model_identity"] for j in judges}) == 1,
            "note": (
                "diversity_unsatisfied: "
                + ",".join(unsatisfied)
                if unsatisfied
                else "cross-model agreement eligible"
            ),
        },
        "diversity_unsatisfied": unsatisfied,
        "synthesis": {
            "consensus": [] if unsatisfied else ["fixture consensus"],
            "divergence": [],
            "minority": [],
            "unresolved": unsatisfied,
        },
        "generated_at": utc_now(),
    }
    out = Path(args.output)
    write_json(out, report)
    print(f"wrote {out}")
    return 0


def duel(args: argparse.Namespace) -> int:
    profiles = [p.strip() for p in args.models.split(",") if p.strip()]
    if len(profiles) < 2:
        print("duel requires at least two --models", file=sys.stderr)
        return 2
    available = {p.strip() for p in (args.available or "").split(",") if p.strip()}
    unsatisfied = [p for p in profiles if available and p not in available]

    perspectives = []
    for i, profile in enumerate(profiles, start=1):
        perspectives.append(
            {
                "id": f"perspective-{i}",
                "context_id": f"ctx-perspective-{i}-{profile}",
                "model_identity": profile,
                "proposal": f"sealed proposal from {profile}",
            }
        )

    packet = {
        "schema_version": "idea-challenge.v1",
        "door_class": "one-way",
        "sealed_generation": True,
        "perspectives": perspectives,
        "cross_reviews": [
            {
                "reviewer": perspectives[0]["id"],
                "subject": perspectives[1]["id"],
                "dimensions": {
                    "evidence": "ok",
                    "reversibility": "ok",
                    "system_fit": "ok",
                    "failure_modes": "ok",
                    "cost": "ok",
                },
            },
            {
                "reviewer": perspectives[1]["id"],
                "subject": perspectives[0]["id"],
                "dimensions": {
                    "evidence": "ok",
                    "reversibility": "ok",
                    "system_fit": "ok",
                    "failure_modes": "ok",
                    "cost": "ok",
                },
            },
        ],
        "disagreements": ["fixture dissent preserved"],
        "refutations": [
            {
                "claim": "fixture claim",
                "attempt": "fixture attempt",
                "result": "failed",
            }
        ],
        "handoff": {
            "owner": "plan",
            "artifact_dir": str(Path(args.output).parent),
            "route": "sealed-multi-perspective",
        },
        "diversity_unsatisfied": unsatisfied,
    }
    # validate-challenge.sh forbids unknown top-level keys — strip disclosure
    # into handoff note via a sidecar when needed, keep packet valid.
    disclosure = packet.pop("diversity_unsatisfied")
    out = Path(args.output)
    write_json(out, packet)
    if disclosure:
        write_json(
            out.with_suffix(".diversity.json"),
            {"diversity_unsatisfied": disclosure, "proceeded_single_model": True},
        )
    print(f"wrote {out}")
    return 0


def validate_cross(args: argparse.Namespace) -> int:
    author_model = args.author_model
    validator_model = args.validator_model
    available = {p.strip() for p in (args.available or "").split(",") if p.strip()}
    unsatisfied = []
    if available and validator_model not in available:
        unsatisfied = [validator_model]
        validator_model = author_model  # degrade to same-model with disclosure

    evidence = {
        "schema_version": "cross-model-validate-evidence.v1",
        "author_model_identity": author_model,
        "validator_model_identity": validator_model,
        "author_context_id": args.author_context_id,
        "validator_context_id": args.validator_context_id,
        "freshness_attestation": {
            "source": "runtime",
            "attester": "fake-runner",
            "notes": (
                f"author_model={author_model}; validator_model={validator_model}"
                + (
                    f"; diversity_unsatisfied={','.join(unsatisfied)}"
                    if unsatisfied
                    else ""
                )
            ),
        },
        "diversity_unsatisfied": unsatisfied,
        "generated_at": utc_now(),
    }
    out = Path(args.output)
    write_json(out, evidence)
    print(f"wrote {out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("council")
    c.add_argument("--models", required=True, help="comma-separated model profiles")
    c.add_argument("--available", default="", help="comma-separated live profiles")
    c.add_argument("--question", default="")
    c.add_argument("--output", required=True)
    c.set_defaults(func=council)

    d = sub.add_parser("duel")
    d.add_argument("--models", required=True)
    d.add_argument("--available", default="")
    d.add_argument("--output", required=True)
    d.set_defaults(func=duel)

    v = sub.add_parser("validate-cross")
    v.add_argument("--author-model", required=True)
    v.add_argument("--validator-model", required=True)
    v.add_argument("--author-context-id", default="author-ctx")
    v.add_argument("--validator-context-id", default="validator-ctx")
    v.add_argument("--available", default="")
    v.add_argument("--output", required=True)
    v.set_defaults(func=validate_cross)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
