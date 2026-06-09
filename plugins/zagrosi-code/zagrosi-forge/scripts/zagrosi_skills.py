#!/usr/bin/env python3
"""Codex-native helpers for the Zagrosi Project/Plan/Implement skills.

The helpers do deterministic validation and state detection. They intentionally
avoid Claude-specific hooks, task directories, and session environment values.
Each command prints JSON so Codex can decide the next workflow step.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SPLIT_RE = re.compile(r"^\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
SECTION_RE = re.compile(r"^section-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
SECTION_TOKEN_RE = re.compile(r"\bsection-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\b")
CONFIG_RE = re.compile(r"^[a-z][a-z0-9_]*:\s*.+$")
REQ_ID_RE = re.compile(r"\bREQ-[A-Z0-9][A-Z0-9-]*\b")
FILE_PATH_RE = re.compile(
    r"`?[\w./-]+\.(?:avif|css|gif|go|htm|html|ico|java|jpeg|jpg|js|json|jsx|less|md|php|png|py|rb|rs|sass|scss|sh|sql|svg|toml|ts|tsx|webp|yaml|yml)(?:`|\b)"
)
FORGE_META_START = "FORGE_META"
LEGACY_META_START = "DEEP_META"
REVIEW_BOARD_PASSES = [
    "architecture",
    "test-strategy",
    "security-privacy",
    "migration-data",
    "product-ambiguity",
    "implementation-feasibility",
]
SENSITIVE_KEY_RE = re.compile(r"(token|secret|key|password|credential|authorization|bearer)", re.I)
WORKFLOW_AMBIGUITY_TERMS = [
    "maybe",
    "option",
    "or",
    "recommend",
    "whatever",
    "vague",
    "decide",
    "should",
    "could",
    "autonomous",
    "external",
    "privacy",
    "review",
    "ci",
    "pr",
    "workflow",
    "research",
    "auto",
]
LOCAL_TOOL_NAMES = ["gh", "codex", "claude", "gemini"]
DEPTH_REMEDIATION_RECOMMENDATION = (
    "Identify missing decisions, codebase evidence, documentation support, or review substance; "
    "ask relevant questions or perform targeted research before expanding prose to meet the depth target."
)
DEPTH_MODES = {"fast", "standard", "deep"}
DEPTH_WORD_TARGETS = {
    "fast": {
        "spec": 700,
        "research": 700,
        "plan": 900,
        "tdd": 450,
        "review": 500,
        "integration_notes": 500,
        "section_index": 350,
        "section": 250,
    },
    "standard": {
        "spec": 1200,
        "research": 1500,
        "plan": 2500,
        "tdd": 1200,
        "review": 1000,
        "integration_notes": 900,
        "section_index": 700,
        "section": 1000,
    },
    "deep": {
        "spec": 1800,
        "research": 2500,
        "plan": 5000,
        "tdd": 2000,
        "review": 1800,
        "integration_notes": 1500,
        "section_index": 900,
        "section": 1500,
    },
}
PLAN_DETAIL_TERMS = {
    "reader-orientation": ["reader note", "self-contained", "fresh implementer", "no prior context"],
    "current-state-evidence": ["current state", "existing", "verified", "grep", "found in"],
    "architecture-rationale": ["why", "rationale", "tradeoff", "decision", "alternative"],
    "contracts": ["contract", "schema", "interface", "api", "payload", "shape"],
    "file-tree": ["file tree", "directory layout", "file-by-file", "files"],
    "phase-plan": ["phase", "batch", "execution order", "sequenced", "dependency"],
    "test-matrix": ["test matrix", "unit", "integration", "e2e", "fixture"],
    "review-integration": ["review-integrated", "review", "iteration", "integration notes"],
}
SECTION_DETAIL_TERMS = {
    "goal": ["goal", "purpose"],
    "dependencies": ["dependencies", "depends on"],
    "background-context": ["background context", "why", "rationale", "architectural"],
    "file-tree": ["file tree", "files", "paths"],
    "tests-first": ["tests first", "expected failure", "test cases", "red"],
    "implementation-details": ["implementation details", "public api", "signature", "contract", "schema"],
    "acceptance": ["acceptance", "done when", "verification"],
    "risks": ["risk", "edge case", "failure mode", "security"],
}
QUALITY_PROFILES = {
    "solo": {
        "security": 1.0,
        "traceability": 0.8,
        "testing": 1.0,
        "scope": 1.0,
        "migration": 0.8,
        "readiness": 1.0,
        "general": 1.0,
    },
    "startup": {
        "security": 1.0,
        "traceability": 0.7,
        "testing": 0.9,
        "scope": 1.2,
        "migration": 0.8,
        "readiness": 1.1,
        "general": 1.0,
    },
    "enterprise": {
        "security": 1.3,
        "traceability": 1.2,
        "testing": 1.2,
        "scope": 1.0,
        "migration": 1.2,
        "readiness": 1.1,
        "general": 1.0,
    },
    "regulated": {
        "security": 1.6,
        "traceability": 1.6,
        "testing": 1.3,
        "scope": 1.0,
        "migration": 1.4,
        "readiness": 1.2,
        "general": 1.0,
    },
    "oss-maintainer": {
        "security": 1.1,
        "traceability": 1.0,
        "testing": 1.3,
        "scope": 1.2,
        "migration": 1.0,
        "readiness": 1.2,
        "general": 1.0,
    },
    "oss": {
        "security": 1.1,
        "traceability": 1.0,
        "testing": 1.3,
        "scope": 1.2,
        "migration": 1.0,
        "readiness": 1.2,
        "general": 1.0,
    },
    "incident-response": {
        "security": 1.5,
        "traceability": 1.1,
        "testing": 1.1,
        "scope": 1.4,
        "migration": 1.3,
        "readiness": 1.5,
        "general": 1.0,
    },
}
VAGUE_SECTION_NAMES = {"misc", "cleanup", "utils", "frontend", "backend", "api", "stuff", "polish"}
PROMPT_TYPES = {
    "codebase-researcher": "Research the existing codebase for relevant files, patterns, tests, risks, and commands. Return concise findings only.",
    "spec-reviewer": "Review the normalized spec for missing requirements, ambiguous acceptance criteria, scope drift, and unverified assumptions.",
    "security-reviewer": "Review the plan or implementation for auth, privacy, data exposure, injection, secrets, and abuse cases. Return severity-ranked findings.",
    "test-strategist": "Review test strategy. Identify missing tests, brittle fixtures, untestable design, and the smallest useful red/green path.",
    "section-writer": "Write one self-contained, reference-grade implementation section from the plan and TDD plan. Target 1,000+ words in standard mode, copy essential context, include tests first, file paths, dependencies, APIs/contracts, risks, rollback, and acceptance criteria.",
    "release-reviewer": "Review final readiness for rollout, rollback, docs, observability, migration safety, and residual risks.",
    "implementation-reviewer": "Review changed code against the section file. Prioritize correctness, security, scope drift, and missing tests.",
}
EVIDENCE_TERMS = {
    "file-evidence": ["current state", "existing", "verified", "found in", "file tree", "rg --files", "grep"],
    "command-evidence": ["rg ", "rg --files", "pytest", "npm test", "uv run", "cargo test", "go test", "pnpm", "yarn"],
    "test-discovery": ["existing test", "tests discovered", "test command", "test matrix", "fixtures"],
    "runtime-detection": ["package.json", "pyproject.toml", "go.mod", "cargo.toml", "runtime", "framework"],
    "assumption-ledger": ["assumption", "unknown", "open question", "stop-line", "stop line"],
}
EVIDENCE_IGNORE_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
COMMAND_CATALOG = [
    {
        "name": "project-setup",
        "phase": "project",
        "summary": "Start or resume project decomposition from a brief or requirements file.",
        "aliases": ["project", "zagrosi-project-setup", "deep-project-setup"],
        "examples": [
            "python3 scripts/zagrosi_skills.py project-setup --file planning/requirements.md",
            "python3 scripts/zagrosi_skills.py project-setup --brief 'Build auth and billing' --planning-dir planning/app",
        ],
    },
    {
        "name": "project-create-dirs",
        "phase": "project",
        "summary": "Create split directories from a project manifest.",
        "aliases": ["zagrosi-project-create-dirs", "deep-project-create-dirs"],
        "examples": ["python3 scripts/zagrosi_skills.py project-create-dirs --planning-dir planning/app"],
    },
    {
        "name": "plan-setup",
        "phase": "plan",
        "summary": "Start or resume a reviewed TDD plan from one spec file.",
        "aliases": ["plan", "zagrosi-plan-setup", "deep-plan-setup"],
        "examples": ["python3 scripts/zagrosi_skills.py plan-setup --file planning/01-auth/spec.md --plugin-root ."],
    },
    {
        "name": "plan-check-sections",
        "phase": "plan",
        "summary": "Inspect section index state and missing section files.",
        "aliases": ["zagrosi-plan-check-sections", "deep-plan-check-sections"],
        "examples": ["python3 scripts/zagrosi_skills.py plan-check-sections --planning-dir planning/01-auth"],
    },
    {
        "name": "plan-generate-section-prompts",
        "phase": "plan",
        "summary": "Generate bounded prompts for missing implementation sections.",
        "aliases": ["zagrosi-plan-generate-section-prompts", "deep-plan-generate-section-prompts"],
        "examples": ["python3 scripts/zagrosi_skills.py plan-generate-section-prompts --planning-dir planning/01-auth"],
    },
    {
        "name": "implement-setup",
        "phase": "implement",
        "summary": "Start or resume section implementation against a target repo.",
        "aliases": ["implement", "zagrosi-implement-setup", "deep-implement-setup"],
        "examples": ["python3 scripts/zagrosi_skills.py implement-setup --sections-dir planning/01-auth/sections --target-dir ."],
    },
    {
        "name": "implement-record-section",
        "phase": "implement",
        "summary": "Record a completed implementation section in Forge state.",
        "aliases": ["zagrosi-implement-record-section", "deep-implement-record-section"],
        "examples": ["python3 scripts/zagrosi_skills.py implement-record-section --sections-dir planning/01-auth/sections --section section-01-auth"],
    },
    {
        "name": "preflight",
        "phase": "all",
        "summary": "Run phase-aware readiness gates before workflow work.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py preflight --phase plan --file planning/01-auth/spec.md"],
    },
    {
        "name": "postflight",
        "phase": "all",
        "summary": "Run phase-aware completion gates after workflow work.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py postflight --phase plan --planning-dir planning/01-auth --strict"],
    },
    {
        "name": "status",
        "phase": "all",
        "summary": "Inspect workflow state and next action for a planning path.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py status --path planning/01-auth"],
    },
    {
        "name": "commands",
        "phase": "utility",
        "summary": "Show grouped command catalog metadata for Forge helpers.",
        "aliases": ["help-commands"],
        "examples": [
            "python3 scripts/zagrosi_skills.py commands --pretty",
            "python3 scripts/zagrosi_skills.py commands --phase plan",
        ],
    },
    {
        "name": "workflow-options",
        "phase": "utility",
        "summary": "Recommend interview, depth, git/privacy, and autonomy options for a Forge run.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py workflow-options --brief 'Improve this project'"],
    },
    {
        "name": "capability-inventory",
        "phase": "utility",
        "summary": "Inventory configured plugins, MCP servers, and local tools without leaking secrets.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py capability-inventory --plugin-root ."],
    },
    {
        "name": "review-capabilities",
        "phase": "utility",
        "summary": "Report mandatory Codex review fallback and opt-in external review candidates.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py review-capabilities --planning-dir planning/01-auth"],
    },
    {
        "name": "planning-consistency",
        "phase": "quality",
        "summary": "Detect late-request requirement drift across Forge planning artifacts.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py planning-consistency --planning-dir planning/01-auth --strict"],
    },
    {
        "name": "doctor",
        "phase": "release",
        "summary": "Validate package metadata, skill files, marketplace entry, and Python support.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py doctor --plugin-root ."],
    },
    {
        "name": "install-codex",
        "phase": "release",
        "summary": "Install or refresh the local Codex plugin config and cache.",
        "aliases": ["install", "install-plugin"],
        "examples": ["python3 scripts/zagrosi_skills.py install --plugin-root . --dry-run"],
    },
    {
        "name": "update-check",
        "phase": "utility",
        "summary": "Check whether the installed Codex plugin cache matches this local checkout.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py update-check --plugin-root ."],
    },
    {
        "name": "self-update",
        "phase": "release",
        "summary": "Refresh Codex config and the installed plugin cache using the installer path.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py self-update --plugin-root ."],
    },
    {
        "name": "codebase-evidence",
        "phase": "plan",
        "summary": "Capture runtime files, test files, and candidate commands for planning evidence.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py codebase-evidence --target-dir . --planning-dir planning/01-auth --write"],
    },
    {
        "name": "lint-plan",
        "phase": "quality",
        "summary": "Validate plan, spec, TDD, research, review, and governance depth.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py lint-plan --planning-dir planning/01-auth --depth standard --strict"],
    },
    {
        "name": "lint-sections",
        "phase": "quality",
        "summary": "Validate section index and implementation section readiness.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py lint-sections --planning-dir planning/01-auth --depth standard --strict"],
    },
    {
        "name": "lint-evidence",
        "phase": "quality",
        "summary": "Validate codebase evidence, commands, tests, runtime detection, and assumptions.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py lint-evidence --planning-dir planning/01-auth --strict"],
    },
    {
        "name": "lint-implementation-readiness",
        "phase": "quality",
        "summary": "Check section ownership, tests, contracts, rollback, and file count readiness.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py lint-implementation-readiness --planning-dir planning/01-auth --strict"],
    },
    {
        "name": "lint-plan-artifacts",
        "phase": "quality",
        "summary": "Require the full Forge planning record before implementation can start.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py lint-plan-artifacts --planning-dir planning/01-auth --strict"],
    },
    {
        "name": "traceability",
        "phase": "quality",
        "summary": "Trace REQ-* IDs through plan, TDD plan, and implementation sections.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py traceability --planning-dir planning/01-auth --strict"],
    },
    {
        "name": "forge-score",
        "phase": "quality",
        "summary": "Roll major planning gates into one Forge Score.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py forge-score --planning-dir planning/01-auth --depth standard"],
    },
    {
        "name": "eval-suite",
        "phase": "release",
        "summary": "Score example planning fixtures for benchmark health.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py eval-suite --examples-dir examples --check-snapshots"],
    },
    {
        "name": "release-check",
        "phase": "release",
        "summary": "Run package, install, example, and eval checks before release.",
        "aliases": [],
        "examples": ["python3 scripts/zagrosi_skills.py release-check --plugin-root ."],
    },
]
COMMAND_SUMMARIES = {item["name"]: item["summary"] for item in COMMAND_CATALOG}
READINESS_TERMS = {
    "tdd": ["tests first", "expected failure", "red", "fixture"],
    "contract": ["contract", "interface", "schema", "result", "shape", "public api"],
    "commands": ["test command", "verification", "npm test", "pytest", "cargo test", "go test"],
    "rollback": ["rollback", "disable", "revert", "back out"],
    "ownership": ["owns", "ownership", "file tree", "modify", "create"],
}
FORGE_COMPONENT_WEIGHTS = {
    "solo": {
        "plan_depth": 1.0,
        "section_readiness": 1.0,
        "traceability": 1.0,
        "evidence_quality": 1.0,
        "implementation_readiness": 1.0,
    },
    "startup": {
        "plan_depth": 0.9,
        "section_readiness": 1.2,
        "traceability": 0.9,
        "evidence_quality": 1.0,
        "implementation_readiness": 1.2,
    },
    "enterprise": {
        "plan_depth": 1.1,
        "section_readiness": 1.1,
        "traceability": 1.3,
        "evidence_quality": 1.2,
        "implementation_readiness": 1.2,
    },
    "regulated": {
        "plan_depth": 1.2,
        "section_readiness": 1.1,
        "traceability": 1.6,
        "evidence_quality": 1.4,
        "implementation_readiness": 1.3,
    },
    "oss-maintainer": {
        "plan_depth": 1.0,
        "section_readiness": 1.2,
        "traceability": 1.1,
        "evidence_quality": 1.0,
        "implementation_readiness": 1.3,
    },
    "oss": {
        "plan_depth": 1.0,
        "section_readiness": 1.2,
        "traceability": 1.1,
        "evidence_quality": 1.0,
        "implementation_readiness": 1.3,
    },
    "incident-response": {
        "plan_depth": 0.9,
        "section_readiness": 1.2,
        "traceability": 1.0,
        "evidence_quality": 1.2,
        "implementation_readiness": 1.6,
    },
}
PRETTY_OUTPUT = False


@dataclass(frozen=True, slots=True)
class Finding:
    severity: str
    code: str
    message: str
    path: str | None = None
    recommendation: str | None = None
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "category": self.category,
        }
        if self.path:
            payload["path"] = self.path
        if self.recommendation:
            payload["recommendation"] = self.recommendation
        return payload


@dataclass(frozen=True, slots=True)
class ProjectInput:
    planning_dir: Path
    input_file: Path | None
    input_mode: str
    generated_file: bool
    brief_word_count: int
    warnings: tuple[str, ...] = ()


def finding(
    severity: str,
    code: str,
    message: str,
    path: Path | str | None = None,
    recommendation: str | None = None,
    category: str | None = None,
) -> Finding:
    return Finding(
        severity=severity,
        code=code,
        message=message,
        path=str(path) if path else None,
        recommendation=recommendation,
        category=category or category_for_code(code),
    )


def category_for_code(code: str) -> str:
    if any(term in code for term in ("security", "privacy", "auth", "permission")):
        return "security"
    if any(term in code for term in ("traceability", "requirement", "orphan")):
        return "traceability"
    if any(term in code for term in ("test", "tdd")):
        return "testing"
    if any(term in code for term in ("scope", "section-too", "vague", "file-path")):
        return "scope"
    if any(term in code for term in ("migration", "rollout", "rollback")):
        return "migration"
    if any(term in code for term in ("readiness", "state", "missing")):
        return "readiness"
    return "general"


def quality_score(findings: list[Finding], profile: str = "solo") -> int:
    penalties = {"critical": 35, "high": 20, "medium": 10, "low": 4}
    profile_weights = QUALITY_PROFILES.get(profile, QUALITY_PROFILES["solo"])
    total_penalty = 0
    for item in findings:
        weight = profile_weights.get(item.category, profile_weights["general"])
        total_penalty += round(penalties.get(item.severity, 0) * weight)
    score = 100 - total_penalty
    return max(0, min(100, score))


def quality_payload(
    name: str,
    findings: list[Finding],
    extras: dict[str, Any] | None = None,
    profile: str = "solo",
    strict: bool = False,
) -> dict[str, Any]:
    score = quality_score(findings, profile)
    blocking_severities = {"critical", "high"}
    if strict:
        blocking_severities.add("medium")
    blocking = [item for item in findings if item.severity in blocking_severities]
    payload: dict[str, Any] = {
        "success": not blocking,
        "gate": name,
        "profile": profile,
        "strict": strict,
        "score": score,
        "finding_count": len(findings),
        "findings": [item.to_dict() for item in findings],
    }
    if extras:
        payload.update(extras)
    return payload


def write_findings_export(payload: dict[str, Any], output_path: Path, export_format: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    findings = payload.get("findings", [])
    if export_format == "jsonl":
        output_path.write_text(
            "\n".join(json.dumps(item, sort_keys=True) for item in findings) + ("\n" if findings else ""),
            encoding="utf-8",
        )
        return
    if export_format == "sarif":
        sarif = {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Zagrosi Forge",
                            "informationUri": "https://github.com/zagrosi-code/zagrosi-forge",
                        }
                    },
                    "results": [
                        {
                            "ruleId": item["code"],
                            "level": {
                                "critical": "error",
                                "high": "error",
                                "medium": "warning",
                                "low": "note",
                            }.get(item["severity"], "warning"),
                            "message": {"text": item["message"]},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": item.get("path", "")}
                                    }
                                }
                            ],
                        }
                        for item in findings
                    ],
                }
            ],
        }
        output_path.write_text(json.dumps(sarif, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return
    raise ValueError(f"Unsupported export format: {export_format}")


def emit_payload(payload: dict[str, Any], args: argparse.Namespace, exit_code: int | None = None) -> int:
    export_path = getattr(args, "export", None)
    if export_path:
        write_findings_export(payload, resolve_path(export_path), getattr(args, "export_format", "jsonl"))
    if exit_code is None:
        exit_code = 0 if payload.get("success", False) else 1
    return print_json(payload, exit_code)


def quality_from_args(
    name: str,
    findings: list[Finding],
    args: argparse.Namespace,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return quality_payload(
        name,
        findings,
        extras,
        profile=getattr(args, "profile", "solo"),
        strict=getattr(args, "strict", False),
    )


def emit_quality(
    name: str,
    findings: list[Finding],
    args: argparse.Namespace,
    extras: dict[str, Any] | None = None,
    exit_code: int | None = None,
) -> int:
    return emit_payload(quality_from_args(name, findings, args, extras), args, exit_code)


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def word_targets(depth: str) -> dict[str, int]:
    return DEPTH_WORD_TARGETS.get(depth, DEPTH_WORD_TARGETS["standard"])


def add_depth_finding(
    findings: list[Finding],
    actual_words: int,
    target_words: int,
    artifact_label: str,
    code: str,
    path: Path,
    hard_floor: int,
) -> None:
    if actual_words < hard_floor:
        findings.append(
            finding(
                "high",
                code,
                f"{artifact_label} has {actual_words} words; hard floor is {hard_floor}.",
                path,
                DEPTH_REMEDIATION_RECOMMENDATION,
            )
        )
    elif actual_words < target_words:
        findings.append(
            finding(
                "medium",
                code,
                f"{artifact_label} has {actual_words} words; target for this depth is {target_words}.",
                path,
                DEPTH_REMEDIATION_RECOMMENDATION,
            )
        )


def contains_any(text: str, terms: list[str]) -> bool:
    haystack = text.lower()
    return any(term.lower() in haystack for term in terms)


def requirement_ids(text: str) -> list[str]:
    return sorted(set(REQ_ID_RE.findall(text)))


def parse_forge_meta(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    raw = extract_block(text, FORGE_META_START, "END_FORGE_META")
    if raw is None:
        raw = extract_block(text, LEGACY_META_START, "END_DEEP_META")
    if raw is None:
        return None, ["Missing FORGE_META block"]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"Invalid FORGE_META JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, ["FORGE_META must contain a JSON object"]
    return payload, []


def parse_deep_meta(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    return parse_forge_meta(text)


def require_terms(
    findings: list[Finding],
    text: str,
    groups: dict[str, list[str]],
    path: Path,
    severity: str = "medium",
) -> None:
    for label, terms in groups.items():
        if not contains_any(text, terms):
            findings.append(
                finding(
                    severity,
                    f"missing-{label}",
                    f"Missing coverage for {label.replace('-', ' ')}.",
                    path,
                    f"Add a concrete {label.replace('-', ' ')} section or equivalent prose.",
                )
            )


def artifact(path: Path, names: list[str]) -> Path | None:
    for name in names:
        candidate = path / name
        if candidate.exists():
            return candidate
    return None


def default_governance_files(planning_dir: Path, depth: str = "standard") -> dict[str, Path]:
    return {
        "decisions": planning_dir / "decisions.md",
        "risks": planning_dir / "risk-register.md",
        "traceability": planning_dir / "traceability.md",
        "quality": planning_dir / "quality-gates.md",
    }


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def governance_templates(depth: str) -> dict[str, str]:
    return {
        "decisions": (
            "# Decision Log\n\n"
            f"Depth mode: {depth}\n\n"
            "| ID | Date | Decision | Alternatives | Rationale | Impact |\n"
            "|----|------|----------|--------------|-----------|--------|\n"
            "| DEC-001 | TBD | TBD | TBD | TBD | TBD |\n"
        ),
        "risks": (
            "# Risk Register\n\n"
            "| ID | Risk | Severity | Likelihood | Mitigation | Section | Verification |\n"
            "|----|------|----------|------------|------------|---------|--------------|\n"
            "| RISK-001 | TBD | TBD | TBD | TBD | TBD | TBD |\n"
        ),
        "traceability": (
            "# Traceability Matrix\n\n"
            "| Requirement | Plan Coverage | Section Coverage | Test Coverage | Status |\n"
            "|-------------|---------------|------------------|---------------|--------|\n"
            "| REQ-001 | TBD | TBD | TBD | TBD |\n"
        ),
        "quality": (
            "# Quality Gates\n\n"
            "Run these before moving stages:\n\n"
            "- `lint-project-manifest`\n"
            "- `lint-plan`\n"
            "- `lint-sections`\n"
            "- `lint-implementation-state`\n"
            "- `traceability`\n"
        ),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def plain_status(success: Any) -> str:
    return "PASS" if bool(success) else "FAIL"


def pretty_path(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value:
            return str(value)
    return None


def summarize_gate(gate: dict[str, Any]) -> str:
    payload = gate.get("payload", {}) if isinstance(gate.get("payload"), dict) else {}
    details: list[str] = []
    if "score" in payload:
        details.append(f"score {payload['score']}")
    if "forge_score" in payload:
        details.append(f"forge {payload['forge_score']}")
    if payload.get("finding_count"):
        details.append(f"{payload['finding_count']} finding(s)")
    if gate.get("required") is False:
        details.append("advisory")
    detail_text = f" ({', '.join(details)})" if details else ""
    return f"  [{plain_status(gate.get('success'))}] {gate.get('name', 'gate')}{detail_text}"


def pretty_findings(findings: list[dict[str, Any]], limit: int = 8) -> list[str]:
    lines: list[str] = []
    for item in findings[:limit]:
        location = f" - {item['path']}" if item.get("path") else ""
        lines.append(f"  - {item.get('severity', 'unknown')}: {item.get('code', 'finding')}: {item.get('message', '')}{location}")
    if len(findings) > limit:
        lines.append(f"  - ... {len(findings) - limit} more finding(s)")
    return lines


def format_flight(payload: dict[str, Any], indent: str = "") -> list[str]:
    title = f"ZAGROSI FORGE {payload.get('stage', 'flight').upper()}: {str(payload.get('phase', 'workflow')).upper()}"
    lines = [
        f"{indent}{title}",
        f"{indent}Status: {plain_status(payload.get('success'))}   Mode: {payload.get('mode', 'auto')}",
    ]
    for label, key in (
        ("Planning dir", "planning_dir"),
        ("Target dir", "target_dir"),
        ("Plugin root", "plugin_root"),
    ):
        value = payload.get(key)
        if value:
            lines.append(f"{indent}{label}: {value}")
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append(f"{indent}Warnings:")
        lines.extend(f"{indent}  - {warning}" for warning in warnings)
    gates = payload.get("gates") or []
    if gates:
        lines.append(f"{indent}Gates:")
        lines.extend(f"{indent}{summarize_gate(gate)}" for gate in gates)
    blocking = payload.get("blocking_gates") or []
    if blocking:
        lines.append(f"{indent}Blocking: {', '.join(blocking)}")
    return lines


def format_quality(payload: dict[str, Any]) -> list[str]:
    lines = [
        f"ZAGROSI FORGE GATE: {str(payload.get('gate', 'quality')).upper()}",
        f"Status: {plain_status(payload.get('success'))}   Score: {payload.get('score', 'n/a')}   Strict: {payload.get('strict', False)}",
    ]
    path = pretty_path(payload, "planning_dir", "plugin_root", "path")
    if path:
        lines.append(f"Path: {path}")
    findings = payload.get("findings") or []
    if findings:
        lines.append("Findings:")
        lines.extend(pretty_findings(findings))
    else:
        lines.append("Findings: none")
    return lines


def format_setup(payload: dict[str, Any]) -> list[str]:
    phase = "workflow"
    if "split_directories" in payload or "specs_complete" in payload:
        phase = "project"
    elif "review_mode" in payload or "section_progress" in payload and "files_found" in payload:
        phase = "plan"
    elif "sections_dir" in payload and "target_dir" in payload:
        phase = "implement"
    lines = [
        f"ZAGROSI FORGE: {phase.upper()}",
        f"Status: {plain_status(payload.get('success'))}   Mode: {payload.get('mode', 'n/a')}",
    ]
    for label, key in (
        ("Planning dir", "planning_dir"),
        ("Sections dir", "sections_dir"),
        ("Target dir", "target_dir"),
        ("State dir", "state_dir"),
        ("Config", "config_path"),
    ):
        value = payload.get(key)
        if value:
            lines.append(f"{label}: {value}")
    if "resume_label" in payload:
        resume_step = payload.get("resume_step")
        suffix = f" (step {resume_step})" if resume_step is not None else ""
        lines.append(f"Resume: {payload.get('resume_label')}{suffix}")
    if "next_section" in payload:
        lines.append(f"Next section: {payload.get('next_section') or 'none'}")
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in warnings)
    if isinstance(payload.get("preflight"), dict):
        lines.append("")
        lines.extend(format_flight(payload["preflight"]))
    if isinstance(payload.get("postflight"), dict):
        lines.append("")
        lines.extend(format_flight(payload["postflight"]))
    return lines


def format_pretty(payload: dict[str, Any]) -> str:
    if {"phase", "stage", "gates"}.issubset(payload):
        lines = format_flight(payload)
    elif payload.get("operation") == "update-check":
        lines = [
            "ZAGROSI FORGE UPDATE CHECK",
            f"Status: {plain_status(payload.get('success'))}   Restart required: {payload.get('restart_required', False)}",
            f"Config: {payload.get('config_path')}",
            f"Codex home: {payload.get('codex_home')}",
            f"Plugin root: {payload.get('plugin_root')}",
            f"Network policy: {payload.get('network_policy')}",
        ]
        cache = payload.get("cache") or {}
        if cache:
            lines.append(f"Cache: {cache.get('path')}   Current: {cache.get('current')}")
        config = payload.get("config") or {}
        if config:
            lines.append(f"Config current: {config.get('current')}")
        next_steps = payload.get("next_steps") or []
        if next_steps:
            lines.append("Next:")
            lines.extend(f"  - {step}" for step in next_steps)
    elif payload.get("operation") in {"install-codex", "self-update"}:
        lines = [
            "ZAGROSI FORGE SELF UPDATE" if payload.get("operation") == "self-update" else "ZAGROSI FORGE INSTALL",
            f"Status: {plain_status(payload.get('success'))}   Changed: {payload.get('changed', False)}",
            f"Config: {payload.get('config_path')}",
            f"Codex home: {payload.get('codex_home')}",
            f"Plugin root: {payload.get('plugin_root')}",
            f"Plugin: {payload.get('plugin')}",
        ]
        cache = payload.get("cache") or {}
        if cache:
            lines.append(f"Cache: {cache.get('path')}   Changed: {cache.get('changed')}")
        verification = payload.get("verification") or {}
        if verification:
            lines.append(f"Verification: {verification.get('status')}")
        if payload.get("backup_path"):
            lines.append(f"Backup: {payload.get('backup_path')}")
        if payload.get("dry_run"):
            lines.append("Mode: dry run")
        next_steps = payload.get("next_steps") or []
        if next_steps:
            lines.append("Next:")
            lines.extend(f"  - {step}" for step in next_steps)
    elif "forge_score" in payload:
        lines = [
            "ZAGROSI FORGE SCORE",
            f"Status: {plain_status(payload.get('success'))}   Score: {payload.get('forge_score')}   Grade: {payload.get('grade', 'n/a')}",
            f"Planning dir: {payload.get('planning_dir')}",
        ]
        components = payload.get("components") or {}
        if components:
            lines.append("Components:")
            lines.extend(f"  - {key}: {value}" for key, value in components.items())
    elif "commands" in payload and isinstance(payload.get("commands"), list):
        phase_filter = payload.get("phase_filter") or "all"
        lines = [
            "ZAGROSI FORGE COMMANDS",
            f"Phase: {phase_filter}",
        ]
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in payload.get("commands", []):
            grouped.setdefault(str(item.get("phase", "utility")), []).append(item)
        for phase in sorted(grouped):
            lines.append("")
            lines.append(phase.upper())
            for item in grouped[phase]:
                aliases = item.get("aliases") or []
                alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
                lines.append(f"  - {item.get('name')}{alias_text}: {item.get('summary', '')}")
    elif "gate" in payload:
        lines = format_quality(payload)
    elif "results" in payload and "plugin_root" in payload:
        lines = [
            "ZAGROSI FORGE RELEASE CHECK",
            f"Status: {plain_status(payload.get('success'))}",
            f"Plugin root: {payload.get('plugin_root')}",
            "Commands:",
        ]
        for result in payload.get("results", []):
            lines.append(f"  [{plain_status(result.get('returncode') == 0)}] {result.get('command')}")
    elif any(key in payload for key in ("preflight", "postflight", "resume_label", "next_section")):
        lines = format_setup(payload)
    elif "next_action" in payload:
        lines = [
            "ZAGROSI FORGE STATUS",
            f"Status: {plain_status(payload.get('success'))}",
            f"Planning dir: {payload.get('planning_dir')}",
            f"Next action: {payload.get('next_action')}",
        ]
        progress = payload.get("section_progress", {})
        if progress:
            lines.append(f"Sections: {progress.get('progress', 'n/a')} ({progress.get('state', 'unknown')})")
    else:
        lines = ["ZAGROSI FORGE", f"Status: {plain_status(payload.get('success', True))}"]
        for key in ("planning_dir", "output", "state_path", "path", "error"):
            if payload.get(key):
                lines.append(f"{key.replace('_', ' ').title()}: {payload[key]}")
    return "\n".join(lines)


def print_json(payload: dict[str, Any], exit_code: int = 0) -> int:
    if PRETTY_OUTPUT:
        print(format_pretty(payload))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def normalize_repeated(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def compact_values(values: list[str], label: str, limit: int = 2) -> str | None:
    if not values:
        return None
    shown = values[:limit]
    suffix = f", +{len(values) - limit} more" if len(values) > limit else ""
    rendered = ", ".join(f"`{Path(item).name if label == 'review' else item}`" for item in shown)
    return f"{label}: {rendered}{suffix}"


def update_json_locked(path: Path, default_factory, mutator, timeout_seconds: float = 5.0) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f"{path.name}.lock")
    start = time.monotonic()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, f"{os.getpid()} {now_iso()}\n".encode("utf-8"))
            finally:
                os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() - start >= timeout_seconds:
                raise TimeoutError(f"Timed out waiting for progress lock: {lock_path}")
            time.sleep(0.01)

    try:
        state = load_json(path) if path.exists() else default_factory()
        mutator(state)
        write_json(path, state)
        return state
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def ensure_markdown_file(path: Path, label: str) -> tuple[bool, str]:
    if not path.exists():
        return False, f"{label} not found: {path}"
    if not path.is_file():
        return False, f"Expected {label} file, got directory: {path}"
    if path.suffix.lower() != ".md":
        return False, f"Expected {label} to end with .md: {path}"
    if not read_text(path).strip():
        return False, f"{label} is empty: {path}"
    return True, ""


def unique_markdown_path(directory: Path, stem: str) -> Path:
    candidate = directory / f"{stem}.md"
    if not candidate.exists() or not read_text(candidate).strip():
        return candidate
    counter = 2
    while True:
        candidate = directory / f"{stem}-{counter}.md"
        if not candidate.exists() or not read_text(candidate).strip():
            return candidate
        counter += 1


def write_chat_requirements(planning_dir: Path, brief: str) -> tuple[Path, bool]:
    planning_dir.mkdir(parents=True, exist_ok=True)
    path = unique_markdown_path(planning_dir, "requirements")
    content = (
        "# Project Brief\n\n"
        "Source: chat brief captured by `$zagrosi-forge:zagrosi-project`.\n\n"
        f"{brief.strip()}\n\n"
        "## Interview Notes\n\n"
        "Detailed interview answers belong in `zagrosi_project_interview.md`.\n"
    )
    path.write_text(content, encoding="utf-8")
    return path, True


def existing_project_initial_file(planning_dir: Path) -> Path | None:
    for state_path in (planning_dir / ".zagrosi-project" / "session.json", planning_dir / ".deep-project" / "session.json"):
        if not state_path.exists():
            continue
        try:
            state = load_json(state_path)
        except (OSError, json.JSONDecodeError):
            continue
        initial_file = state.get("initial_file")
        if isinstance(initial_file, str):
            candidate = resolve_path(initial_file)
            if candidate.exists() and candidate.is_file():
                return candidate
    return None


def resolve_project_input(args: argparse.Namespace, *, materialize_chat: bool = True) -> tuple[ProjectInput | None, str | None]:
    file_arg = getattr(args, "file", None)
    brief = (getattr(args, "brief", None) or "").strip()
    planning_dir_arg = getattr(args, "planning_dir", None)

    if file_arg and brief:
        return None, "Use either --file or --brief for project setup, not both."

    if file_arg:
        input_file = resolve_path(file_arg)
        ok, error = ensure_markdown_file(input_file, "requirements file")
        if not ok:
            return None, error
        return ProjectInput(
            planning_dir=input_file.parent,
            input_file=input_file,
            input_mode="file",
            generated_file=False,
            brief_word_count=word_count(read_text(input_file)),
        ), None

    if not brief:
        return None, "Project setup needs either --file PATH or --brief TEXT from the chat."

    planning_dir = resolve_path(planning_dir_arg) if planning_dir_arg else Path.cwd().resolve()
    input_file: Path | None = None
    generated = False
    warnings: tuple[str, ...] = ()
    if materialize_chat:
        existing_file = existing_project_initial_file(planning_dir)
        if existing_file:
            input_file = existing_file
            warnings = ("Existing project session found; reusing its initial requirements file.",)
        else:
            input_file, generated = write_chat_requirements(planning_dir, brief)
    return ProjectInput(
        planning_dir=planning_dir,
        input_file=input_file,
        input_mode="chat",
        generated_file=generated,
        brief_word_count=word_count(brief),
        warnings=warnings,
    ), None


def extract_block(text: str, start: str, end: str) -> str | None:
    pattern = re.compile(rf"<!--\s*{re.escape(start)}\s*\n(.*?)\n{re.escape(end)}\s*-->", re.S)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def parse_numbered_manifest(text: str, block: str, item_re: re.Pattern[str], prefix: str = "") -> tuple[list[str], list[str]]:
    raw = extract_block(text, block, "END_MANIFEST")
    if raw is None:
        return [], [f"Missing {block} block"]

    items: list[str] = []
    errors: list[str] = []
    for line_no, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not item_re.match(line):
            errors.append(f"Line {line_no}: invalid item {line!r}")
            continue
        items.append(line)

    expected = 1
    for item in items:
        number_part = item.removeprefix(prefix).split("-", 1)[0]
        actual = int(number_part)
        if actual != expected:
            errors.append(f"Expected {expected:02d}, got {actual:02d} in {item}")
        expected += 1

    if not items and not errors:
        errors.append(f"{block} block is empty")
    return items, errors


def parse_project_config(text: str) -> tuple[dict[str, str], list[str]]:
    raw = extract_block(text, "PROJECT_CONFIG", "END_PROJECT_CONFIG")
    if raw is None:
        return {}, ["Missing PROJECT_CONFIG block"]

    config: dict[str, str] = {}
    errors: list[str] = []
    for line_no, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not CONFIG_RE.match(line):
            errors.append(f"Line {line_no}: invalid config entry {line!r}")
            continue
        key, value = line.split(":", 1)
        config[key.strip()] = value.strip()

    for key in ("runtime", "test_command"):
        if key not in config:
            errors.append(f"PROJECT_CONFIG missing required field: {key}")
    return config, errors


def resolve_path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def git_info(target_dir: Path) -> dict[str, Any]:
    root_result = git(["rev-parse", "--show-toplevel"], target_dir)
    if root_result.returncode != 0:
        return {"available": False, "root": None}

    root = Path(root_result.stdout.strip())
    branch_result = git(["branch", "--show-current"], root)
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    status_result = git(["status", "--porcelain"], root)
    dirty = [line for line in status_result.stdout.splitlines() if line.strip()] if status_result.returncode == 0 else []
    protected = branch in {"main", "master"} or branch.startswith(("release/", "release-", "hotfix/", "hotfix-"))

    return {
        "available": True,
        "root": str(root),
        "branch": branch or None,
        "is_protected_branch": protected,
        "working_tree_clean": not dirty,
        "dirty_files": dirty,
    }


def current_plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sanitize_gate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(payload)
    for key in ("content", "stdout_tail", "stderr_tail"):
        if key in cleaned and isinstance(cleaned[key], str) and len(cleaned[key]) > 500:
            cleaned[key] = cleaned[key][:500] + "...[truncated]"
    if "findings" in cleaned and isinstance(cleaned["findings"], list) and len(cleaned["findings"]) > 12:
        cleaned["findings"] = cleaned["findings"][:12]
        cleaned["findings_truncated"] = True
    return cleaned


def run_internal_gate(
    name: str,
    command: list[str],
    *,
    required: bool = True,
    cwd: Path | None = None,
) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *command],
        cwd=cwd or current_plugin_root(),
        capture_output=True,
        text=True,
    )
    payload: dict[str, Any]
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"stdout": result.stdout[-1000:]}
    command_success = result.returncode == 0 and payload.get("success", True) is not False
    return {
        "name": name,
        "required": required,
        "success": command_success,
        "returncode": result.returncode,
        "command": " ".join(command),
        "payload": sanitize_gate_payload(payload),
        "stderr_tail": result.stderr[-1000:],
    }


def direct_gate(name: str, success: bool, payload: dict[str, Any], *, required: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "required": required,
        "success": success,
        "returncode": 0 if success else 1,
        "command": "internal",
        "payload": sanitize_gate_payload(payload),
        "stderr_tail": "",
    }


def effective_flight_mode(args: argparse.Namespace) -> str:
    mode = getattr(args, "flight_mode", None) or getattr(args, "flight", None) or "auto"
    if mode == "strict" or getattr(args, "strict", False):
        return "strict"
    return mode


def append_strict(command: list[str], mode: str) -> list[str]:
    if mode == "strict" and "--strict" not in command:
        return [*command, "--strict"]
    return command


def flight_payload(
    *,
    phase: str,
    stage: str,
    mode: str,
    gates: list[dict[str, Any]],
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if mode == "off":
        return {
            "success": True,
            "phase": phase,
            "stage": stage,
            "mode": mode,
            "gates": [],
            "blocking_gates": [],
        }
    blocking = [
        gate["name"]
        for gate in gates
        if gate.get("required", True) and not gate.get("success", False) and mode != "advisory"
    ]
    payload: dict[str, Any] = {
        "success": not blocking,
        "phase": phase,
        "stage": stage,
        "mode": mode,
        "gates": gates,
        "blocking_gates": blocking,
    }
    if extras:
        payload.update(extras)
    return payload


def project_preflight_report(project_input: ProjectInput, args: argparse.Namespace) -> dict[str, Any]:
    mode = effective_flight_mode(args)
    if mode == "off":
        return flight_payload(phase="project", stage="preflight", mode=mode, gates=[])
    plugin_root = resolve_path(getattr(args, "plugin_root", None)) if getattr(args, "plugin_root", None) else current_plugin_root()
    planning_dir = project_input.planning_dir
    input_file = project_input.input_file

    if project_input.input_mode == "chat":
        ok = project_input.brief_word_count > 0 and (
            input_file is None or (input_file.exists() and bool(read_text(input_file).strip()))
        )
        input_payload = {
            "mode": "chat",
            "planning_dir": str(planning_dir),
            "materialized_file": str(input_file) if input_file else None,
            "brief_word_count": project_input.brief_word_count,
            "generated_file": project_input.generated_file,
            "error": None if ok else "chat brief is empty or could not be materialized",
        }
        input_gate = direct_gate("chat-brief", ok, input_payload)
    else:
        ok, error = ensure_markdown_file(input_file, "requirements file") if input_file else (False, "requirements file missing")
        input_gate = direct_gate(
            "requirements-file",
            ok,
            {"path": str(input_file) if input_file else None, "error": error if error else None},
        )

    gates = [
        input_gate,
        run_internal_gate("doctor", append_strict(["doctor", "--plugin-root", str(plugin_root)], mode)),
        run_internal_gate("status", ["status", "--path", str(planning_dir)], required=False),
    ]
    return flight_payload(
        phase="project",
        stage="preflight",
        mode=mode,
        gates=gates,
        extras={
            "planning_dir": str(planning_dir),
            "plugin_root": str(plugin_root),
            "input_mode": project_input.input_mode,
            "input_file": str(input_file) if input_file else None,
        },
    )


def project_postflight_report(planning_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    mode = effective_flight_mode(args)
    if mode == "off":
        return flight_payload(phase="project", stage="postflight", mode=mode, gates=[])
    gates = [
        run_internal_gate("lint-interview", append_strict(["lint-interview", "--phase", "project", "--planning-dir", str(planning_dir)], mode)),
        run_internal_gate("lint-project-manifest", append_strict(["lint-project-manifest", "--planning-dir", str(planning_dir)], mode)),
        run_internal_gate("status", ["status", "--path", str(planning_dir)], required=False),
    ]
    return flight_payload(phase="project", stage="postflight", mode=mode, gates=gates, extras={"planning_dir": str(planning_dir)})


def plan_preflight_report(spec_file: Path, args: argparse.Namespace) -> dict[str, Any]:
    mode = effective_flight_mode(args)
    if mode == "off":
        return flight_payload(phase="plan", stage="preflight", mode=mode, gates=[])
    plugin_root = resolve_path(getattr(args, "plugin_root", None)) if getattr(args, "plugin_root", None) else current_plugin_root()
    planning_dir = spec_file.parent
    target_dir = resolve_path(getattr(args, "target_dir", None)) if getattr(args, "target_dir", None) else Path.cwd()
    ok, error = ensure_markdown_file(spec_file, "spec file")
    evidence_command = ["codebase-evidence", "--target-dir", str(target_dir), "--planning-dir", str(planning_dir)]
    if getattr(args, "write_evidence", False):
        evidence_command.append("--write")
    gates = [
        direct_gate("spec-file", ok, {"path": str(spec_file), "error": error if error else None}),
        run_internal_gate("doctor", append_strict(["doctor", "--plugin-root", str(plugin_root)], mode)),
        run_internal_gate("codebase-evidence", evidence_command, required=False),
        run_internal_gate("status", ["status", "--path", str(planning_dir)], required=False),
    ]
    return flight_payload(
        phase="plan",
        stage="preflight",
        mode=mode,
        gates=gates,
        extras={"planning_dir": str(planning_dir), "plugin_root": str(plugin_root), "target_dir": str(target_dir)},
    )


def plan_postflight_report(planning_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    mode = effective_flight_mode(args)
    if mode == "off":
        return flight_payload(phase="plan", stage="postflight", mode=mode, gates=[])
    depth = getattr(args, "depth", "standard") or "standard"
    profile = getattr(args, "profile", "solo")
    gates = [
        run_internal_gate("lint-interview", append_strict(["lint-interview", "--phase", "plan", "--planning-dir", str(planning_dir), "--profile", profile], mode)),
        run_internal_gate("lint-plan", append_strict(["lint-plan", "--planning-dir", str(planning_dir), "--depth", depth, "--profile", profile], mode)),
        run_internal_gate("lint-evidence", append_strict(["lint-evidence", "--planning-dir", str(planning_dir), "--profile", profile], mode)),
        run_internal_gate("lint-artifact-schema", append_strict(["lint-artifact-schema", "--planning-dir", str(planning_dir), "--profile", profile], mode)),
    ]
    if (planning_dir / "reviews").exists() or (planning_dir / "codex-integration-notes.md").exists() or (planning_dir / "claude-integration-notes.md").exists():
        gates.append(run_internal_gate("lint-review-integration", append_strict(["lint-review-integration", "--planning-dir", str(planning_dir), "--profile", profile], mode)))
    if (planning_dir / "sections" / "index.md").exists():
        gates.extend(
            [
                run_internal_gate("lint-sections", append_strict(["lint-sections", "--planning-dir", str(planning_dir), "--depth", depth, "--profile", profile], mode)),
                run_internal_gate("traceability", append_strict(["traceability", "--planning-dir", str(planning_dir), "--profile", profile], mode)),
                run_internal_gate("lint-implementation-readiness", append_strict(["lint-implementation-readiness", "--planning-dir", str(planning_dir), "--profile", profile], mode)),
                run_internal_gate("forge-score", append_strict(["forge-score", "--planning-dir", str(planning_dir), "--depth", depth, "--profile", profile], mode)),
            ]
        )
        if getattr(args, "write_report", False):
            gates.append(run_internal_gate("report", ["report", "--planning-dir", str(planning_dir), "--depth", depth, "--profile", profile], required=False))
    gates.append(run_internal_gate("status", ["status", "--path", str(planning_dir)], required=False))
    return flight_payload(phase="plan", stage="postflight", mode=mode, gates=gates, extras={"planning_dir": str(planning_dir)})


def implement_preflight_report(sections_dir: Path, target_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    mode = effective_flight_mode(args)
    if mode == "off":
        return flight_payload(phase="implement", stage="preflight", mode=mode, gates=[])
    plugin_root = resolve_path(getattr(args, "plugin_root", None)) if getattr(args, "plugin_root", None) else current_plugin_root()
    planning_dir = sections_dir.parent
    depth = getattr(args, "depth", "standard") or "standard"
    profile = getattr(args, "profile", "solo")
    repo = git_info(target_dir) if target_dir.exists() else {"available": False, "root": None}
    gates = [
        direct_gate("sections-directory", sections_dir.exists() and sections_dir.is_dir(), {"sections_dir": str(sections_dir)}),
        direct_gate("target-directory", target_dir.exists() and target_dir.is_dir(), {"target_dir": str(target_dir)}),
        run_internal_gate("doctor", append_strict(["doctor", "--plugin-root", str(plugin_root)], mode)),
        run_internal_gate("lint-plan-artifacts", ["lint-plan-artifacts", "--planning-dir", str(planning_dir), "--profile", profile, "--strict"]),
        run_internal_gate("lint-sections", append_strict(["lint-sections", "--planning-dir", str(planning_dir), "--depth", depth, "--profile", profile], mode)),
        run_internal_gate("traceability", append_strict(["traceability", "--planning-dir", str(planning_dir), "--profile", profile], mode)),
        run_internal_gate("lint-implementation-readiness", append_strict(["lint-implementation-readiness", "--planning-dir", str(planning_dir), "--profile", profile], mode)),
        run_internal_gate("next-section", ["next-section", "--planning-dir", str(planning_dir)], required=False),
        run_internal_gate("suggest-section-splits", ["suggest-section-splits", "--planning-dir", str(planning_dir)], required=False),
    ]
    warnings: list[str] = []
    if repo.get("is_protected_branch"):
        warnings.append(f"Current branch is protected-looking: {repo.get('branch')}")
    if repo.get("available") and not repo.get("working_tree_clean"):
        warnings.append(f"Working tree has {len(repo.get('dirty_files', []))} uncommitted change(s)")
    return flight_payload(
        phase="implement",
        stage="preflight",
        mode=mode,
        gates=gates,
        extras={"planning_dir": str(planning_dir), "target_dir": str(target_dir), "git": repo, "warnings": warnings},
    )


def implement_postflight_report(planning_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    mode = effective_flight_mode(args)
    if mode == "off":
        return flight_payload(phase="implement", stage="postflight", mode=mode, gates=[])
    depth = getattr(args, "depth", "standard") or "standard"
    profile = getattr(args, "profile", "solo")
    sections_dir = resolve_path(getattr(args, "sections_dir", None)) if getattr(args, "sections_dir", None) else planning_dir / "sections"
    target_dir = resolve_path(getattr(args, "target_dir", None)) if getattr(args, "target_dir", None) else Path.cwd()
    recording_status = implementation_recording_status(planning_dir)
    final_state_gates = recording_status["sections_recorded_complete"]
    gates: list[dict[str, Any]] = []
    if getattr(args, "diff_file", None) or getattr(args, "staged", False):
        command = ["implementation-drift", "--planning-dir", str(planning_dir), "--repo", str(target_dir), "--profile", profile]
        if getattr(args, "diff_file", None):
            command.extend(["--diff-file", str(resolve_path(args.diff_file))])
        if getattr(args, "staged", False):
            command.append("--staged")
        gates.append(run_internal_gate("implementation-drift", append_strict(command, mode)))
    if getattr(args, "section_file", None):
        command = ["patch-scope", "--section-file", str(resolve_path(args.section_file)), "--repo", str(target_dir), "--profile", profile]
        if getattr(args, "diff_file", None):
            command.extend(["--diff-file", str(resolve_path(args.diff_file))])
        if getattr(args, "staged", False):
            command.append("--staged")
        gates.append(run_internal_gate("patch-scope", append_strict(command, mode)))
    progress_state = recording_status["section_progress"].get("state")
    if progress_state in {"invalid_index", "no_index"}:
        gates.append(
            direct_gate(
                "sections-index",
                False,
                {
                    "section_progress": recording_status["section_progress"],
                    "message": "Implementation postflight requires a valid sections/index.md.",
                },
            )
        )
    elif final_state_gates:
        gates.append(run_internal_gate("lint-implementation-state", append_strict(["lint-implementation-state", "--sections-dir", str(sections_dir), "--profile", profile], mode)))
    else:
        gates.append(
            direct_gate(
                "implementation-progress",
                True,
                {
                    "recording_state": recording_status["recording_state"],
                    "recorded_sections": recording_status["recorded_sections"],
                    "remaining_sections": recording_status["remaining_sections"],
                    "deferred_gate": "lint-implementation-state",
                    "message": "Implementation state lint is deferred until all sections are recorded complete.",
                },
                required=False,
            )
        )
    score_command = ["forge-score", "--planning-dir", str(planning_dir), "--depth", depth, "--profile", profile, "--write-history"]
    if final_state_gates:
        score_command = append_strict(score_command, mode)
    gates.append(run_internal_gate("forge-score", score_command, required=final_state_gates))
    if getattr(args, "write_report", False):
        gates.append(run_internal_gate("report", ["report", "--planning-dir", str(planning_dir), "--depth", depth, "--profile", profile], required=False))
    gates.append(run_internal_gate("status", ["status", "--path", str(planning_dir)], required=False))
    return flight_payload(
        phase="implement",
        stage="postflight",
        mode=mode,
        gates=gates,
        extras={"planning_dir": str(planning_dir), "target_dir": str(target_dir), **recording_status},
    )


def release_preflight_report(plugin_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    mode = effective_flight_mode(args)
    if mode == "off":
        return flight_payload(phase="release", stage="preflight", mode=mode, gates=[])
    gates = [
        run_internal_gate("doctor", append_strict(["doctor", "--plugin-root", str(plugin_root)], mode)),
        run_internal_gate("eval-suite", ["eval-suite", "--examples-dir", str(plugin_root / "examples")], required=False),
    ]
    return flight_payload(phase="release", stage="preflight", mode=mode, gates=gates, extras={"plugin_root": str(plugin_root)})


def release_postflight_report(plugin_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    mode = effective_flight_mode(args)
    if mode == "off":
        return flight_payload(phase="release", stage="postflight", mode=mode, gates=[])
    command = ["release-check", "--plugin-root", str(plugin_root)]
    if getattr(args, "run_tests", False):
        command.append("--run-tests")
    gates = [run_internal_gate("release-check", command)]
    return flight_payload(phase="release", stage="postflight", mode=mode, gates=gates, extras={"plugin_root": str(plugin_root)})


def preflight(args: argparse.Namespace) -> int:
    if args.phase == "project":
        project_input, error = resolve_project_input(args, materialize_chat=False)
        if error:
            return print_json({"success": False, "error": error}, 1)
        payload = project_preflight_report(project_input, args)
    elif args.phase == "plan":
        if not args.file:
            return print_json({"success": False, "error": "--file is required for plan preflight"}, 1)
        payload = plan_preflight_report(resolve_path(args.file), args)
    elif args.phase == "implement":
        if not args.sections_dir:
            return print_json({"success": False, "error": "--sections-dir is required for implement preflight"}, 1)
        payload = implement_preflight_report(resolve_path(args.sections_dir), resolve_path(args.target_dir or os.getcwd()), args)
    else:
        payload = release_preflight_report(resolve_path(args.plugin_root or current_plugin_root()), args)
    return print_json(payload, 0 if payload["success"] else 1)


def postflight(args: argparse.Namespace) -> int:
    if args.phase == "project":
        if not args.planning_dir:
            return print_json({"success": False, "error": "--planning-dir is required for project postflight"}, 1)
        payload = project_postflight_report(resolve_path(args.planning_dir), args)
    elif args.phase == "plan":
        if not args.planning_dir:
            return print_json({"success": False, "error": "--planning-dir is required for plan postflight"}, 1)
        payload = plan_postflight_report(resolve_path(args.planning_dir), args)
    elif args.phase == "implement":
        planning_dir = resolve_path(args.planning_dir) if args.planning_dir else (resolve_path(args.sections_dir).parent if args.sections_dir else None)
        if planning_dir is None:
            return print_json({"success": False, "error": "--planning-dir or --sections-dir is required for implement postflight"}, 1)
        payload = implement_postflight_report(planning_dir, args)
    else:
        payload = release_postflight_report(resolve_path(args.plugin_root or current_plugin_root()), args)
    return print_json(payload, 0 if payload["success"] else 1)


def deep_project_setup(args: argparse.Namespace) -> int:
    project_input, error = resolve_project_input(args)
    if error or project_input is None:
        return print_json({"success": False, "error": error}, 1)

    input_file = project_input.input_file
    planning_dir = project_input.planning_dir
    state_dir = planning_dir / ".zagrosi-project"
    state_path = state_dir / "session.json"
    legacy_state_path = planning_dir / ".deep-project" / "session.json"
    if not state_path.exists() and legacy_state_path.exists():
        state_path = legacy_state_path
        state_dir = legacy_state_path.parent
    mode = "resume" if state_path.exists() else "new"

    if state_path.exists():
        state = load_json(state_path)
    else:
        state = {
            "initial_file": str(input_file) if input_file else None,
            "initial_source": project_input.input_mode,
            "created_at": now_iso(),
            "depth_mode": args.depth,
            "workflow": "zagrosi-project",
        }
        write_json(state_path, state)

    warnings: list[str] = list(project_input.warnings)
    if input_file and state.get("initial_file") and state.get("initial_file") != str(input_file):
        warnings.append(f"Session was created for {state.get('initial_file')}, now using {input_file}")
    if state.get("initial_source") and state.get("initial_source") != project_input.input_mode:
        warnings.append(f"Session was created from {state.get('initial_source')}, now using {project_input.input_mode}")

    manifest_path = planning_dir / "project-manifest.md"
    split_dirs = [p for p in planning_dir.iterdir() if p.is_dir() and SPLIT_RE.match(p.name)]
    specs = [p for p in split_dirs if (p / "spec.md").exists() and read_text(p / "spec.md").strip()]

    if split_dirs and len(specs) == len(split_dirs):
        resume_step = 7
        resume_label = "complete"
    elif split_dirs:
        resume_step = 6
        resume_label = "spec_generation"
    elif manifest_path.exists():
        resume_step = 4
        resume_label = "confirmation_or_directory_creation"
    elif (planning_dir / "zagrosi_project_interview.md").exists() or (planning_dir / "deep_project_interview.md").exists():
        resume_step = 2
        resume_label = "split_analysis"
    else:
        resume_step = 1
        resume_label = "interview"

    if resume_step > 1 or interview_artifact(planning_dir, "project"):
        warnings.extend(interview_warning_messages(planning_dir, "project"))

    payload = {
        "success": True,
        "mode": mode,
        "planning_dir": str(planning_dir),
        "state_dir": str(state_dir),
        "initial_file": str(input_file) if input_file else None,
        "input_mode": project_input.input_mode,
        "generated_requirements_file": str(input_file) if project_input.generated_file and input_file else None,
        "brief_word_count": project_input.brief_word_count,
        "depth_mode": state.get("depth_mode", args.depth),
        "resume_step": resume_step,
        "resume_label": resume_label,
        "split_directories": [str(p) for p in sorted(split_dirs)],
        "specs_complete": [str(p / "spec.md") for p in sorted(specs)],
        "warnings": warnings,
    }
    if effective_flight_mode(args) != "off":
        payload["preflight"] = project_preflight_report(project_input, args)
    return print_json(payload)


def deep_project_create_dirs(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    manifest_path = planning_dir / "project-manifest.md"
    if not manifest_path.exists():
        return print_json({"success": False, "error": f"Missing manifest: {manifest_path}"}, 1)

    splits, errors = parse_numbered_manifest(read_text(manifest_path), "SPLIT_MANIFEST", SPLIT_RE)
    if errors:
        return print_json({"success": False, "errors": errors}, 1)

    created: list[str] = []
    existing: list[str] = []
    missing_specs: list[str] = []
    for split in splits:
        directory = planning_dir / split
        if directory.exists():
            existing.append(str(directory))
        else:
            directory.mkdir(parents=True)
            created.append(str(directory))
        spec_path = directory / "spec.md"
        if not spec_path.exists() or not read_text(spec_path).strip():
            missing_specs.append(str(spec_path))

    payload = {
        "success": True,
        "planning_dir": str(planning_dir),
        "splits": splits,
        "created": created,
        "existing": existing,
        "missing_specs": missing_specs,
    }
    if effective_flight_mode(args) != "off":
        payload["postflight"] = project_postflight_report(planning_dir, args)
    return print_json(payload)


def first_existing(planning_dir: Path, names: list[str]) -> Path | None:
    for name in names:
        path = planning_dir / name
        if path.exists():
            return path
    return None


INTERVIEW_FILES = {
    "project": ["zagrosi_project_interview.md", "deep_project_interview.md"],
    "plan": ["codex-interview.md", "claude-interview.md"],
}
INTERVIEW_PLACEHOLDER_RE = re.compile(
    r"\b(TBD|TODO|placeholder)\b|synthetic interview|generated without|not interviewed|no user interview|assumed answers?",
    re.I,
)


def interview_artifact(planning_dir: Path, phase: str) -> Path | None:
    return first_existing(planning_dir, INTERVIEW_FILES[phase])


def has_interview_exchange(text: str) -> bool:
    has_question = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:q|question)\s*[:|-]\s*\S", text) is not None
    has_answer = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:a|answer)\s*[:|-]\s*\S", text) is not None
    has_table = bool(re.search(r"(?im)^\s*\|\s*(?:question|q)\s*\|\s*(?:answer|a|decision)", text))
    return (has_question and has_answer) or has_table


def interview_findings(planning_dir: Path, phase: str) -> tuple[list[Finding], dict[str, Any]]:
    names = INTERVIEW_FILES[phase]
    path = interview_artifact(planning_dir, phase)
    expected_path = planning_dir / names[0]
    findings: list[Finding] = []
    if not path:
        findings.append(
            finding(
                "medium",
                "missing-interview",
                f"{phase} interview artifact is missing.",
                expected_path,
                f"Interview the user and write {names[0]}, or set interview_mode: skipped_with_reason with skip_reason.",
            )
        )
        return findings, {
            "planning_dir": str(planning_dir),
            "phase": phase,
            "interview": None,
            "user_interviewed": False,
            "interview_mode": None,
        }

    text = read_text(path)
    user_interviewed = re.search(r"(?im)^\s*user_interviewed\s*:\s*true\s*$", text) is not None
    skipped = re.search(r"(?im)^\s*interview_mode\s*:\s*skipped_with_reason\s*$", text) is not None
    reason_match = re.search(r"(?im)^\s*(?:skip_reason|reason)\s*:\s*(.+?)\s*$", text)
    skip_reason = reason_match.group(1).strip() if reason_match else ""

    if not text.strip():
        findings.append(finding("high", "empty-interview", "Interview artifact is empty.", path))
    if INTERVIEW_PLACEHOLDER_RE.search(text):
        findings.append(
            finding(
                "high",
                "placeholder-interview",
                "Interview artifact appears to be placeholder, fake, or synthetic.",
                path,
                "Replace it with actual user questions and answers, or explicitly skip with a concrete reason.",
            )
        )
    if user_interviewed and skipped:
        findings.append(
            finding(
                "medium",
                "conflicting-interview-mode",
                "Interview artifact says the user was interviewed and also says the interview was skipped.",
                path,
            )
        )
    if not user_interviewed and not skipped:
        findings.append(
            finding(
                "medium",
                "missing-interview-confirmation",
                "Interview artifact must include user_interviewed: true or interview_mode: skipped_with_reason.",
                path,
            )
        )
    if user_interviewed and not has_interview_exchange(text):
        findings.append(
            finding(
                "medium",
                "missing-interview-exchange",
                "Interview artifact marks user_interviewed: true but has no clear question/answer exchange.",
                path,
                "Record at least one Q:/A: pair or a Question/Answer table.",
            )
        )
    if skipped and (not skip_reason or INTERVIEW_PLACEHOLDER_RE.search(skip_reason)):
        findings.append(
            finding(
                "high",
                "missing-skip-reason",
                "Skipped interviews must include a concrete skip_reason.",
                path,
            )
        )

    return findings, {
        "planning_dir": str(planning_dir),
        "phase": phase,
        "interview": str(path),
        "user_interviewed": user_interviewed,
        "interview_mode": "skipped_with_reason" if skipped else ("completed" if user_interviewed else None),
        "skip_reason": skip_reason or None,
        "word_count": word_count(text),
    }


def interview_warning_messages(planning_dir: Path, phase: str) -> list[str]:
    findings, _ = interview_findings(planning_dir, phase)
    return [f"Interview gate: {item.code} - {item.message}" for item in findings if item.severity in {"critical", "high", "medium"}]


def check_section_progress(planning_dir: Path) -> dict[str, Any]:
    sections_dir = planning_dir / "sections"
    index_path = sections_dir / "index.md"
    if not index_path.exists():
        return {"state": "no_index", "sections_dir": str(sections_dir)}

    text = read_text(index_path)
    config, config_errors = parse_project_config(text)
    sections, manifest_errors = parse_numbered_manifest(text, "SECTION_MANIFEST", SECTION_RE, prefix="section-")
    errors = config_errors + manifest_errors
    if errors:
        return {"state": "invalid_index", "sections_dir": str(sections_dir), "errors": errors}

    missing: list[str] = []
    empty: list[str] = []
    complete: list[str] = []
    for section in sections:
        path = sections_dir / f"{section}.md"
        if not path.exists():
            missing.append(section)
        elif not read_text(path).strip():
            empty.append(section)
        else:
            complete.append(section)

    if not sections:
        state = "invalid_index"
    elif len(complete) == len(sections):
        state = "complete"
    elif complete or empty:
        state = "partial"
    else:
        state = "has_index"

    return {
        "state": state,
        "sections_dir": str(sections_dir),
        "project_config": config,
        "sections": sections,
        "complete": complete,
        "missing": missing,
        "empty": empty,
        "progress": f"{len(complete)}/{len(sections)}",
        "next_section": (missing + empty)[0] if (missing + empty) else None,
    }


def extract_file_paths(text: str) -> list[str]:
    paths = {match.group(0).strip("`").removeprefix("./") for match in FILE_PATH_RE.finditer(text)}
    return sorted(paths)


def parse_section_dependencies(index_text: str, sections: list[str]) -> dict[str, list[str]]:
    known = set(sections)
    dependencies = {section: [] for section in sections}

    def add_dependencies(section: str, deps: list[str]) -> None:
        if section not in known:
            return
        current = dependencies.setdefault(section, [])
        for dep in deps:
            if dep != section and dep not in current:
                current.append(dep)

    for line in index_text.splitlines():
        stripped = line.strip()
        if "|" in stripped:
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and cells[0] in known:
                depends_cell = cells[1] if len(cells) > 1 else ""
                add_dependencies(cells[0], SECTION_TOKEN_RE.findall(depends_cell))
            continue

        lower = stripped.lower()
        if "depends on" not in lower:
            continue
        before, after = re.split(r"\bdepends on\b", stripped, maxsplit=1, flags=re.IGNORECASE)
        dependent_candidates = SECTION_TOKEN_RE.findall(before)
        if not dependent_candidates:
            continue
        add_dependencies(dependent_candidates[0], SECTION_TOKEN_RE.findall(after))
    return dependencies


def dependency_graph(planning_dir: Path, progress: dict[str, Any] | None = None) -> dict[str, list[str]]:
    progress = progress or check_section_progress(planning_dir)
    if progress.get("state") in {"invalid_index", "no_index"}:
        return {}
    index_path = planning_dir / "sections" / "index.md"
    return parse_section_dependencies(read_text(index_path), progress.get("sections", []))


def completed_sections(planning_dir: Path) -> set[str]:
    state_path = implementation_state_path(planning_dir)
    if not state_path.exists():
        return set()
    state = load_json(state_path)
    completed = state.get("completed_sections", {})
    return set(completed) if isinstance(completed, dict) else set()


def implementation_recording_status(planning_dir: Path) -> dict[str, Any]:
    progress = check_section_progress(planning_dir)
    sections = progress.get("sections", []) if progress.get("state") not in {"invalid_index", "no_index"} else []
    known_sections = set(sections)
    recorded = completed_sections(planning_dir)
    recorded_known = sorted(section for section in recorded if section in known_sections)
    remaining = [section for section in sections if section not in recorded]
    sections_recorded_complete = bool(sections) and not remaining and progress.get("state") == "complete"
    if sections_recorded_complete:
        recording_state = "complete"
    elif recorded_known:
        recording_state = "partial"
    else:
        recording_state = "not_started"
    return {
        "section_progress": progress,
        "recording_state": recording_state,
        "sections_recorded_complete": sections_recorded_complete,
        "recorded_sections": recorded_known,
        "remaining_sections": remaining,
        "unknown_recorded_sections": sorted(section for section in recorded if section not in known_sections),
    }


def section_metrics(section: str, path: Path, dependencies: dict[str, list[str]]) -> dict[str, Any]:
    text = read_text(path) if path.exists() else ""
    files = extract_file_paths(text)
    words = word_count(text)
    dep_count = len(dependencies.get(section, []))
    risk_terms = ["security", "privacy", "auth", "permission", "migration", "data", "payment", "token", "secret"]
    risk_points = dep_count + (2 if contains_any(text, risk_terms) else 0) + (1 if len(files) > 5 else 0)
    effort_score = words + len(files) * 120 + dep_count * 180
    effort = "large" if effort_score >= 1800 else "medium" if effort_score >= 750 else "small"
    risk = "high" if risk_points >= 4 else "medium" if risk_points >= 2 else "low"
    return {
        "section": section,
        "path": str(path),
        "word_count": words,
        "file_count": len(files),
        "files": files,
        "dependency_count": dep_count,
        "dependencies": dependencies.get(section, []),
        "effort": effort,
        "risk": risk,
    }


def ready_sections(progress: dict[str, Any], dependencies: dict[str, list[str]], completed: set[str]) -> list[str]:
    sections = progress.get("sections", [])
    ready: list[str] = []
    for section in sections:
        if section in completed:
            continue
        if all(dep in completed for dep in dependencies.get(section, [])):
            ready.append(section)
    return ready


def deep_plan_setup(args: argparse.Namespace) -> int:
    spec_file = resolve_path(args.file)
    ok, error = ensure_markdown_file(spec_file, "spec file")
    if not ok:
        return print_json({"success": False, "error": error}, 1)

    planning_dir = spec_file.parent
    config_path = planning_dir / "zagrosi_plan_config.json"
    legacy_config_path = planning_dir / "deep_plan_config.json"
    if not config_path.exists() and legacy_config_path.exists():
        config_path = legacy_config_path
    mode = "resume" if config_path.exists() else "new"
    if config_path.exists():
        config = load_json(config_path)
    else:
        config = {
            "initial_file": str(spec_file),
            "planning_dir": str(planning_dir),
            "plugin_root": str(resolve_path(args.plugin_root)) if args.plugin_root else None,
            "review_mode": args.review_mode,
            "depth_mode": args.depth,
            "workflow": "zagrosi-plan",
            "created_at": now_iso(),
        }
        write_json(config_path, config)
        for name, path in default_governance_files(planning_dir, args.depth).items():
            write_if_missing(path, governance_templates(args.depth)[name])

    files = {
        "research": first_existing(planning_dir, ["codex-research.md", "claude-research.md"]),
        "interview": first_existing(planning_dir, ["codex-interview.md", "claude-interview.md"]),
        "spec": first_existing(planning_dir, ["codex-spec.md", "claude-spec.md"]),
        "plan": first_existing(planning_dir, ["codex-plan.md", "claude-plan.md"]),
        "integration_notes": first_existing(planning_dir, ["codex-integration-notes.md", "claude-integration-notes.md"]),
        "plan_tdd": first_existing(planning_dir, ["codex-plan-tdd.md", "claude-plan-tdd.md"]),
    }
    reviews_dir = planning_dir / "reviews"
    reviews = sorted(str(p) for p in reviews_dir.glob("*.md")) if reviews_dir.exists() else []
    section_progress = check_section_progress(planning_dir)

    if section_progress["state"] == "complete":
        resume_step = None
        resume_label = "complete"
    elif section_progress["state"] in {"has_index", "partial"}:
        resume_step = 19
        resume_label = "write_sections"
    elif files["plan_tdd"]:
        resume_step = 18
        resume_label = "create_section_index"
    elif files["integration_notes"]:
        resume_step = 16
        resume_label = "write_tdd_plan"
    elif reviews:
        resume_step = 14
        resume_label = "integrate_review"
    elif files["plan"]:
        resume_step = 13
        resume_label = "review_plan"
    elif files["spec"]:
        resume_step = 11
        resume_label = "write_plan"
    elif files["interview"]:
        resume_step = 10
        resume_label = "write_spec"
    elif files["research"]:
        resume_step = 8
        resume_label = "interview"
    else:
        resume_step = 6
        resume_label = "research_decision"

    warnings: list[str] = []
    if (resume_step is None or resume_step > 10) or files["interview"]:
        warnings.extend(interview_warning_messages(planning_dir, "plan"))

    payload = {
        "success": True,
        "mode": mode,
        "planning_dir": str(planning_dir),
        "config_path": str(config_path),
        "initial_file": str(spec_file),
        "review_mode": config.get("review_mode", args.review_mode),
        "depth_mode": config.get("depth_mode", args.depth),
        "resume_step": resume_step,
        "resume_label": resume_label,
        "files_found": {k: str(v) for k, v in files.items() if v},
        "reviews": reviews,
        "section_progress": section_progress,
        "warnings": warnings,
    }
    if effective_flight_mode(args) != "off":
        payload["preflight"] = plan_preflight_report(spec_file, args)
    return print_json(payload)


def deep_plan_check_sections(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    result = check_section_progress(planning_dir)
    result["success"] = result["state"] != "invalid_index"
    return print_json(result, 0 if result["success"] else 1)


SECTION_PROMPT = """Generate the implementation section `{section}`.

Read these planning files from `{planning_dir}`:
- `codex-plan.md` (or `claude-plan.md` if this is a migrated plan)
- `codex-plan-tdd.md` (or `claude-plan-tdd.md` if this is a migrated plan)
- `sections/index.md`

Write ONLY raw markdown for `{section}.md`.

Requirements:
- Make the section self-contained for a fresh implementer with no prior context.
- Target 1,000-3,500 words in standard mode, 1,500-4,500 words in deep mode.
- Start with the goal, explicit dependencies, and non-goals for this section.
- Include a Background Context section that copies the relevant architecture,
  contracts, data shapes, and rationale from the plan.
- Put Tests FIRST with concrete test files, test names or descriptions,
  fixtures, expected failures, and verification commands.
- Include exact file paths to create or modify, preferably as a file tree.
- Include implementation details, public APIs, function/class signatures,
  schema/migration snippets, and error shapes where those remove ambiguity.
- Include risks, edge cases, rollback notes, acceptance criteria, and final
  verification commands.
- Include dependencies on earlier sections, but do not duplicate their content.
- Do not include full production implementations unless absolutely necessary.
- Do not reference other planning files for essential context; copy the needed
  facts into this section.
"""


def deep_plan_generate_section_prompts(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    progress = check_section_progress(planning_dir)
    if progress["state"] in {"invalid_index", "no_index"}:
        return print_json({"success": False, "section_progress": progress}, 1)

    pending = progress["missing"] + progress["empty"]
    if args.all:
        pending = progress["sections"]
    batch = pending[: args.batch_size]
    prompts_dir = planning_dir / "sections" / ".prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    prompts: list[str] = []
    for section in batch:
        prompt_path = prompts_dir / f"{section}-prompt.md"
        prompt_path.write_text(SECTION_PROMPT.format(section=section, planning_dir=planning_dir), encoding="utf-8")
        prompts.append(str(prompt_path))

    return print_json(
        {
            "success": True,
            "planning_dir": str(planning_dir),
            "prompts_dir": str(prompts_dir),
            "batch_size": args.batch_size,
            "remaining": pending[args.batch_size :],
            "prompt_files": prompts,
        }
    )


def deep_implement_setup(args: argparse.Namespace) -> int:
    sections_dir = resolve_path(args.sections_dir)
    target_dir = resolve_path(args.target_dir or os.getcwd())
    if not sections_dir.exists() or not sections_dir.is_dir():
        return print_json({"success": False, "error": f"Sections directory not found: {sections_dir}"}, 1)
    if not target_dir.exists() or not target_dir.is_dir():
        return print_json({"success": False, "error": f"Target directory not found: {target_dir}"}, 1)

    planning_dir = sections_dir.parent
    progress = check_section_progress(planning_dir)
    if progress["state"] in {"invalid_index", "no_index"}:
        return print_json({"success": False, "section_progress": progress}, 1)

    artifact_payload = plan_artifacts_payload(planning_dir, argparse.Namespace(profile=args.profile, strict=True))
    if not artifact_payload["success"]:
        artifact_payload["error"] = "Forge planning process is incomplete; finish zagrosi-plan before implementation."
        return print_json(artifact_payload, 1)

    state_dir = planning_dir / "implementation"
    config_path = state_dir / "zagrosi_implement_config.json"
    state_path = state_dir / "zagrosi_implement_state.json"
    legacy_config_path = state_dir / "deep_implement_config.json"
    legacy_state_path = state_dir / "deep_implement_state.json"
    if not config_path.exists() and legacy_config_path.exists():
        config_path = legacy_config_path
    if not state_path.exists() and legacy_state_path.exists():
        state_path = legacy_state_path
    state_dir.mkdir(parents=True, exist_ok=True)

    if state_path.exists():
        state = load_json(state_path)
    else:
        state = {"completed_sections": {}, "created_at": now_iso()}
        write_json(state_path, state)

    config = {
        "sections_dir": str(sections_dir),
        "target_dir": str(target_dir),
        "planning_dir": str(planning_dir),
        "test_command": progress.get("project_config", {}).get("test_command"),
        "runtime": progress.get("project_config", {}).get("runtime"),
    }
    write_json(config_path, config)

    completed = sorted(state.get("completed_sections", {}).keys())
    next_section = next((section for section in progress["sections"] if section not in completed), None)
    repo = git_info(target_dir)
    warnings: list[str] = []
    if repo.get("is_protected_branch"):
        warnings.append(f"Current git branch is protected-looking: {repo.get('branch')}")
    if repo.get("available") and not repo.get("working_tree_clean"):
        warnings.append(f"Working tree has {len(repo.get('dirty_files', []))} uncommitted change(s)")

    payload = {
        "success": True,
        "sections_dir": str(sections_dir),
        "target_dir": str(target_dir),
        "state_dir": str(state_dir),
        "config_path": str(config_path),
        "state_path": str(state_path),
        "section_progress": progress,
        "completed_sections": completed,
        "next_section": next_section,
        "git": repo,
        "warnings": warnings,
    }
    if effective_flight_mode(args) != "off":
        payload["preflight"] = implement_preflight_report(sections_dir, target_dir, args)
    return print_json(payload)


def implementation_state_path(planning_dir: Path) -> Path:
    state_path = planning_dir / "implementation" / "zagrosi_implement_state.json"
    legacy_state_path = planning_dir / "implementation" / "deep_implement_state.json"
    if not state_path.exists() and legacy_state_path.exists():
        return legacy_state_path
    return state_path


def load_implementation_state(planning_dir: Path) -> dict[str, Any]:
    state_path = implementation_state_path(planning_dir)
    return load_json(state_path) if state_path.exists() else {"completed_sections": {}, "created_at": now_iso()}


def implementation_evidence_by_section(planning_dir: Path) -> dict[str, dict[str, Any]]:
    state = load_implementation_state(planning_dir)
    completed = state.get("completed_sections", {})
    return completed if isinstance(completed, dict) else {}


def compact_section_evidence(record: dict[str, Any]) -> str:
    parts: list[str] = []
    commit = record.get("commit")
    if commit:
        parts.append(f"commit `{commit}`")
    commit_status = record.get("commit_status")
    if commit_status and not commit:
        parts.append(f"commit status `{commit_status}`")
    for key, label in (
        ("files_changed", "files"),
        ("test_files", "tests"),
        ("review_artifacts", "review"),
        ("verification", "verification"),
    ):
        values = normalize_repeated(record.get(key, [])) if isinstance(record, dict) else []
        rendered = compact_values(values, label)
        if rendered:
            parts.append(rendered)
    return "; ".join(parts) if parts else "-"


def deep_implement_record_section(args: argparse.Namespace) -> int:
    sections_dir = resolve_path(args.sections_dir)
    planning_dir = sections_dir.parent
    artifact_payload = plan_artifacts_payload(planning_dir, argparse.Namespace(profile=args.profile, strict=True))
    if not artifact_payload["success"]:
        artifact_payload["error"] = "Forge planning process is incomplete; finish zagrosi-plan before recording implementation."
        return print_json(artifact_payload, 1)
    state_path = implementation_state_path(planning_dir)
    state = load_implementation_state(planning_dir)
    section_record = {
        "completed_at": now_iso(),
        "commit": args.commit,
        "notes": args.notes,
        "files_changed": normalize_repeated(args.files_changed),
        "test_files": normalize_repeated(args.test_files),
        "review_artifacts": normalize_repeated(args.review_artifacts),
        "verification": normalize_repeated(args.verification),
        "commit_status": args.commit_status or ("recorded" if args.commit else "not_recorded"),
    }
    state.setdefault("completed_sections", {})[args.section] = section_record
    write_json(state_path, state)
    traceability_path = refresh_traceability_matrix(planning_dir)
    payload = {
        "success": True,
        "state_path": str(state_path),
        "section": args.section,
        "record": section_record,
        "traceability_matrix": str(traceability_path) if traceability_path else None,
    }
    if effective_flight_mode(args) != "off":
        payload["postflight"] = implement_postflight_report(sections_dir.parent, args)
    return print_json(payload)


def lint_interview(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    findings, extras = interview_findings(planning_dir, args.phase)
    return emit_quality("interview", findings, args, extras)


def lint_project_manifest(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    manifest_path = planning_dir / "project-manifest.md"
    findings: list[Finding] = []
    splits: list[str] = []

    if not manifest_path.exists():
        findings.append(finding("critical", "missing-manifest", "project-manifest.md is missing.", manifest_path))
        return emit_quality("project-manifest", findings, args)

    interview_gate_findings, interview_extras = interview_findings(planning_dir, "project")
    findings.extend(interview_gate_findings)

    text = read_text(manifest_path)
    meta, meta_errors = parse_forge_meta(text)
    for error in meta_errors:
        findings.append(
            finding(
                "low",
                "metadata",
                error,
                manifest_path,
                "Add a FORGE_META JSON block with artifact_type, depth_mode, and source fields.",
            )
        )
    if meta and meta.get("artifact_type") != "project_manifest":
        findings.append(finding("medium", "metadata-type", "FORGE_META artifact_type should be project_manifest.", manifest_path))

    splits, manifest_errors = parse_numbered_manifest(text, "SPLIT_MANIFEST", SPLIT_RE)
    for error in manifest_errors:
        findings.append(finding("critical", "manifest-format", error, manifest_path))

    require_terms(
        findings,
        text,
        {
            "dependencies": ["dependency", "depends on", "blocks"],
            "execution-order": ["execution order", "run order", "sequence"],
            "parallelization": ["parallel", "concurrent"],
            "zagrosi-plan-commands": ["$zagrosi-plan", "zagrosi-plan", "$deep-plan", "deep-plan"],
            "cross-cutting-concerns": ["cross-cutting", "shared", "common"],
        },
        manifest_path,
    )

    for split in splits:
        split_dir = planning_dir / split
        spec_path = split_dir / "spec.md"
        if not split_dir.exists():
            findings.append(finding("medium", "missing-split-dir", f"Split directory is missing: {split}", split_dir))
            continue
        if not spec_path.exists() or not read_text(spec_path).strip():
            findings.append(finding("medium", "missing-split-spec", f"Split spec is missing or empty: {split}/spec.md", spec_path))
            continue
        spec_text = read_text(spec_path)
        require_terms(
            findings,
            spec_text,
            {
                "acceptance-criteria": ["acceptance criteria", "done when", "success criteria"],
                "scope": ["in scope", "out of scope", "non-goals"],
                "testing": ["test", "tests", "verification"],
                "open-questions": ["open question", "unknown", "assumption"],
            },
            spec_path,
            "low",
        )

    payload = quality_from_args(
        "project-manifest",
        findings,
        args,
        {"planning_dir": str(planning_dir), "manifest": str(manifest_path), "splits": splits, "interview": interview_extras},
    )
    return emit_payload(payload, args)


def lint_plan(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    depth = args.depth or "standard"
    targets = word_targets(depth)
    findings: list[Finding] = []

    spec_path = artifact(planning_dir, ["codex-spec.md", "claude-spec.md"])
    plan_path = artifact(planning_dir, ["codex-plan.md", "claude-plan.md"])
    tdd_path = artifact(planning_dir, ["codex-plan-tdd.md", "claude-plan-tdd.md"])

    if not plan_path:
        findings.append(finding("critical", "missing-plan", "Implementation plan is missing.", planning_dir / "codex-plan.md"))
        return emit_quality("plan", findings, args)

    interview_gate_findings, interview_extras = interview_findings(planning_dir, "plan")
    findings.extend(interview_gate_findings)

    plan_text = read_text(plan_path)
    meta, meta_errors = parse_forge_meta(plan_text)
    for error in meta_errors:
        findings.append(finding("low", "metadata", error, plan_path))
    if meta and meta.get("artifact_type") != "implementation_plan":
        findings.append(finding("medium", "metadata-type", "FORGE_META artifact_type should be implementation_plan.", plan_path))

    plan_words = word_count(plan_text)
    add_depth_finding(findings, plan_words, targets["plan"], "Implementation plan", "plan-too-thin", plan_path, 500)

    require_terms(
        findings,
        plan_text,
        {
            "goals": ["goal", "non-goal", "out of scope"],
            "architecture": ["architecture", "design", "approach"],
            "file-plan": ["file", "path", "module"],
            "testing": ["test", "tdd", "verification"],
            "security-privacy": ["security", "privacy", "permission", "auth"],
            "risk": ["risk", "edge case", "failure"],
            "migration": ["migration", "schema", "data migration", "backward", "compatibility"],
            "rollout": ["rollout", "release", "deploy", "ship", "feature flag"],
            "rollback": ["rollback", "revert", "disable", "back out"],
            "acceptance": ["acceptance", "done when", "success criteria"],
        },
        plan_path,
    )
    require_terms(findings, plan_text, PLAN_DETAIL_TERMS, plan_path, "medium")
    if not FILE_PATH_RE.search(plan_text):
        findings.append(finding("high", "no-file-paths", "Plan does not name concrete files or paths.", plan_path))

    if not spec_path:
        findings.append(finding("high", "missing-normalized-spec", "codex-spec.md is missing.", planning_dir / "codex-spec.md"))
        spec_ids: list[str] = []
        spec_words = 0
    else:
        spec_text = read_text(spec_path)
        spec_words = word_count(spec_text)
        add_depth_finding(findings, spec_words, targets["spec"], "Normalized spec", "spec-too-thin", spec_path, 250)
        spec_ids = requirement_ids(spec_text)
        if not spec_ids:
            findings.append(finding("medium", "no-requirement-ids", "Spec has no REQ-* identifiers.", spec_path))
        missing_in_plan = [req_id for req_id in spec_ids if req_id not in plan_text]
        if missing_in_plan:
            findings.append(
                finding(
                    "high",
                    "traceability-gap",
                    f"Requirement IDs missing from plan: {', '.join(missing_in_plan)}",
                    plan_path,
                )
            )

    if not tdd_path:
        findings.append(finding("high", "missing-tdd-plan", "codex-plan-tdd.md is missing.", planning_dir / "codex-plan-tdd.md"))
        tdd_words = 0
    else:
        tdd_text = read_text(tdd_path)
        tdd_words = word_count(tdd_text)
        add_depth_finding(findings, tdd_words, targets["tdd"], "TDD plan", "tdd-plan-too-thin", tdd_path, 200)
        if not contains_any(tdd_text, ["test_", "it(", "describe(", "pytest", "cargo test", "go test", "expected failure"]):
            findings.append(finding("medium", "thin-tdd-plan", "TDD plan does not include concrete test names or commands.", tdd_path))
        missing_in_tdd = [req_id for req_id in spec_ids if req_id not in tdd_text]
        if missing_in_tdd:
            findings.append(finding("medium", "tdd-traceability-gap", f"Requirement IDs missing from TDD plan: {', '.join(missing_in_tdd)}", tdd_path))

    research_path = artifact(planning_dir, ["codex-research.md", "claude-research.md"])
    research_words = None
    if research_path:
        research_words = word_count(read_text(research_path))
        add_depth_finding(findings, research_words, targets["research"], "Research artifact", "research-too-thin", research_path, 250)
    interview_path = artifact(planning_dir, ["codex-interview.md", "claude-interview.md"])
    integration_path = artifact(planning_dir, ["codex-integration-notes.md", "claude-integration-notes.md"])
    integration_words = None
    if integration_path:
        integration_words = word_count(read_text(integration_path))
        add_depth_finding(
            findings,
            integration_words,
            targets["integration_notes"],
            "Integration notes",
            "integration-notes-too-thin",
            integration_path,
            250,
        )

    review_files = sorted((planning_dir / "reviews").glob("*.md")) if (planning_dir / "reviews").exists() else []
    review_word_counts = {path.name: word_count(read_text(path)) for path in review_files}
    for review_path in review_files:
        add_depth_finding(
            findings,
            review_word_counts[review_path.name],
            targets["review"],
            f"Review file {review_path.name}",
            "review-too-thin",
            review_path,
            250,
        )

    for name, path in default_governance_files(planning_dir, depth).items():
        if not path.exists():
            findings.append(finding("medium", f"missing-{name}", f"{path.name} is missing.", path))

    if depth == "deep":
        review_file_stems = {path.stem for path in review_files}
        missing_reviews = [item for item in REVIEW_BOARD_PASSES if item not in review_file_stems]
        if missing_reviews:
            findings.append(
                finding(
                    "medium",
                    "missing-review-board-passes",
                    f"Deep mode review files missing: {', '.join(missing_reviews)}",
                    planning_dir / "reviews",
                )
            )

    payload = quality_from_args(
        "plan",
        findings,
        args,
        {
            "planning_dir": str(planning_dir),
            "plan": str(plan_path),
            "requirement_ids": spec_ids,
            "depth_mode": depth,
            "interview": interview_extras,
            "depth_targets": targets,
            "word_counts": {
                "spec": spec_words,
                "research": research_words,
                "interview": word_count(read_text(interview_path)) if interview_path else None,
                "plan": plan_words,
                "tdd": tdd_words,
                "integration_notes": integration_words,
                "reviews": review_word_counts,
            },
        },
    )
    return emit_payload(payload, args)


def lint_sections(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    depth = args.depth or "standard"
    targets = word_targets(depth)
    findings: list[Finding] = []
    progress = check_section_progress(planning_dir)
    if progress["state"] == "invalid_index":
        for error in progress.get("errors", []):
            findings.append(finding("critical", "invalid-section-index", error, planning_dir / "sections" / "index.md"))
        return emit_quality("sections", findings, args, {"section_progress": progress})
    if progress["state"] == "no_index":
        findings.append(finding("critical", "missing-section-index", "sections/index.md is missing.", planning_dir / "sections" / "index.md"))
        return emit_quality("sections", findings, args, {"section_progress": progress})

    index_path = planning_dir / "sections" / "index.md"
    index_text = read_text(index_path)
    index_words = word_count(index_text)
    add_depth_finding(
        findings,
        index_words,
        targets["section_index"],
        "Section index",
        "section-index-too-thin",
        index_path,
        150,
    )
    dependencies = parse_section_dependencies(index_text, progress["sections"])
    require_terms(
        findings,
        index_text,
        {
            "dependencies": ["dependency", "depends on", "blocks"],
            "execution-order": ["execution order", "sequence", "run order"],
            "parallelization": ["parallel", "concurrent"],
        },
        index_path,
    )

    spec_path = artifact(planning_dir, ["codex-spec.md", "claude-spec.md"])
    spec_ids = requirement_ids(read_text(spec_path)) if spec_path else []
    all_section_text = ""
    estimates: list[dict[str, Any]] = []

    for section, deps in dependencies.items():
        unknown = [dep for dep in deps if dep not in progress["sections"]]
        if unknown:
            findings.append(
                finding(
                    "high",
                    "unknown-section-dependency",
                    f"{section} depends on unknown section(s): {', '.join(unknown)}",
                    index_path,
                )
            )

    for section in progress["sections"]:
        section_path = planning_dir / "sections" / f"{section}.md"
        slug = section.split("-", 2)[2] if len(section.split("-", 2)) == 3 else section
        slug_tokens = set(slug.split("-"))
        if slug in VAGUE_SECTION_NAMES or slug_tokens.intersection(VAGUE_SECTION_NAMES):
            findings.append(
                finding(
                    "medium",
                    "vague-section-name",
                    f"{section} is too vague to be a strong implementation boundary.",
                    section_path,
                    "Rename the section around a capability, data model, integration, or risk boundary.",
                )
            )
        if not section_path.exists():
            findings.append(finding("critical", "missing-section-file", f"Section file missing: {section}.md", section_path))
            continue
        text = read_text(section_path)
        metrics = section_metrics(section, section_path, dependencies)
        estimates.append(metrics)
        all_section_text += "\n" + text
        add_depth_finding(
            findings,
            metrics["word_count"],
            targets["section"],
            section,
            "section-too-thin",
            section_path,
            150,
        )
        if metrics["word_count"] > 5000:
            findings.append(finding("low", "section-too-large", f"{section} may be too large for focused implementation.", section_path))
        if metrics["file_count"] > 12:
            findings.append(
                finding(
                    "high",
                    "section-too-many-files",
                    f"{section} names {metrics['file_count']} files; split or narrow the section.",
                    section_path,
                )
            )
        elif metrics["file_count"] > 7:
            findings.append(
                finding(
                    "medium",
                    "section-many-files",
                    f"{section} names {metrics['file_count']} files; verify this stays implementable in one pass.",
                    section_path,
                )
            )
        if metrics["dependency_count"] > 4:
            findings.append(
                finding(
                    "medium",
                    "section-many-dependencies",
                    f"{section} has {metrics['dependency_count']} dependencies.",
                    section_path,
                )
            )
        require_terms(
            findings,
            text,
            {
                "tests-first": ["test", "tests first", "expected failure", "red"],
                "implementation": ["implementation", "create", "modify", "file"],
                "acceptance": ["acceptance", "done when", "verification"],
            },
            section_path,
        )
        require_terms(findings, text, SECTION_DETAIL_TERMS, section_path, "medium")
        if not FILE_PATH_RE.search(text):
            findings.append(finding("medium", "section-no-file-paths", f"{section} does not name concrete files.", section_path))

    missing_requirements = [req_id for req_id in spec_ids if req_id not in all_section_text]
    if missing_requirements:
        findings.append(
            finding(
                "high",
                "section-traceability-gap",
                f"Requirement IDs missing from all sections: {', '.join(missing_requirements)}",
                planning_dir / "sections",
            )
        )

    payload = quality_from_args(
        "sections",
        findings,
        args,
        {
            "planning_dir": str(planning_dir),
            "depth_mode": depth,
            "depth_targets": targets,
            "section_progress": progress,
            "requirement_ids": spec_ids,
            "section_index_word_count": index_words,
            "section_estimates": estimates,
        },
    )
    return emit_payload(payload, args)


def lint_implementation_state(args: argparse.Namespace) -> int:
    sections_dir = resolve_path(args.sections_dir)
    planning_dir = sections_dir.parent
    findings: list[Finding] = []
    progress = check_section_progress(planning_dir)
    state_path = planning_dir / "implementation" / "zagrosi_implement_state.json"
    legacy_state_path = planning_dir / "implementation" / "deep_implement_state.json"
    if not state_path.exists() and legacy_state_path.exists():
        state_path = legacy_state_path
    code_review_dir = planning_dir / "implementation" / "code_review"
    usage_path = planning_dir / "implementation" / "usage.md"

    if progress["state"] in {"invalid_index", "no_index"}:
        findings.append(finding("critical", "invalid-sections", "Cannot validate implementation without valid sections/index.md.", sections_dir / "index.md"))
        return emit_quality("implementation-state", findings, args)

    if not state_path.exists():
        findings.append(finding("high", "missing-state", "zagrosi_implement_state.json is missing.", state_path))
        completed: dict[str, Any] = {}
    else:
        state = load_json(state_path)
        completed = state.get("completed_sections", {})
        if not isinstance(completed, dict):
            findings.append(finding("critical", "invalid-state", "completed_sections must be an object.", state_path))
            completed = {}

    for section in progress["sections"]:
        if section not in completed:
            findings.append(finding("medium", "section-not-recorded", f"{section} is not recorded complete.", state_path))
            continue
        record = completed[section]
        if not record.get("completed_at"):
            findings.append(finding("low", "missing-completed-at", f"{section} has no completed_at timestamp.", state_path))
        if not record.get("commit"):
            findings.append(finding("low", "missing-commit", f"{section} has no commit recorded.", state_path))
        review_path = code_review_dir / f"{section}-review.md"
        diff_path = code_review_dir / f"{section}-diff.md"
        decisions_path = code_review_dir / f"{section}-decisions.md"
        if not review_path.exists():
            findings.append(finding("medium", "missing-review", f"Review file missing for {section}.", review_path))
        if not diff_path.exists():
            findings.append(finding("low", "missing-diff", f"Diff file missing for {section}.", diff_path))
        if not decisions_path.exists():
            findings.append(
                finding(
                    "medium",
                    "missing-review-decisions",
                    f"Review decisions file missing for {section}.",
                    decisions_path,
                    "Write a decisions artifact that records accepted, rejected, and deferred review findings.",
                )
            )
        if "files_changed" in record and not record.get("files_changed"):
            findings.append(finding("low", "missing-file-evidence", f"{section} has no changed files recorded.", state_path))
        if "test_files" in record and not record.get("test_files"):
            findings.append(finding("low", "missing-test-evidence", f"{section} has no test files recorded.", state_path))
        if "review_artifacts" in record and not record.get("review_artifacts"):
            findings.append(finding("low", "missing-review-evidence", f"{section} has no review artifacts recorded.", state_path))

    if not usage_path.exists():
        findings.append(finding("medium", "missing-usage", "implementation/usage.md is missing.", usage_path))

    payload = quality_from_args(
        "implementation-state",
        findings,
        args,
        {
            "sections_dir": str(sections_dir),
            "state_path": str(state_path),
            "completed_sections": sorted(completed.keys()),
        },
    )
    return emit_payload(payload, args)


def local_tool_status(names: list[str] | None = None) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "available": bool(path := shutil.which(name)),
            "path": path,
        }
        for name in (names or LOCAL_TOOL_NAMES)
    }


def load_toml_config(path: Path | None) -> tuple[dict[str, Any], list[str], str | None]:
    if path is None:
        default = Path.home() / ".codex" / "config.toml"
        path = default if default.exists() else None
    if path is None:
        return {}, ["No Codex config file found."], None
    if not path.exists():
        return {}, [f"Config file not found: {path}"], str(path)
    try:
        data = tomllib.loads(read_text(path))
    except Exception as exc:  # pragma: no cover - exact parser errors vary by Python version.
        return {}, [f"Config file could not be parsed: {exc.__class__.__name__}"], str(path)
    return data if isinstance(data, dict) else {}, [], str(path)


def summarize_plugins(config: dict[str, Any]) -> list[dict[str, Any]]:
    plugins = config.get("plugins", {})
    if not isinstance(plugins, dict):
        return []
    rows: list[dict[str, Any]] = []
    for plugin_id, settings in sorted(plugins.items()):
        enabled = True
        if isinstance(settings, dict) and "enabled" in settings:
            enabled = bool(settings.get("enabled"))
        rows.append({"id": str(plugin_id), "enabled": enabled})
    return rows


def mcp_transport(settings: dict[str, Any]) -> str:
    if settings.get("url"):
        return "http"
    if settings.get("command"):
        return "stdio"
    return "unknown"


def has_sensitive_key(mapping: dict[str, Any]) -> bool:
    return any(SENSITIVE_KEY_RE.search(str(key)) for key in mapping)


def summarize_mcp_servers(config: dict[str, Any]) -> list[dict[str, Any]]:
    servers = config.get("mcp_servers", {})
    if not isinstance(servers, dict):
        return []
    rows: list[dict[str, Any]] = []
    for name, settings in sorted(servers.items()):
        server = settings if isinstance(settings, dict) else {}
        env = server.get("env", {})
        env_vars = server.get("env_vars", {})
        headers = server.get("http_headers", {})
        has_env = isinstance(env, dict) and bool(env)
        has_env_vars = isinstance(env_vars, (dict, list)) and bool(env_vars)
        has_http_headers = isinstance(headers, dict) and bool(headers)
        has_auth = (
            bool(server.get("bearer_token"))
            or bool(server.get("bearer_token_env_var"))
            or has_http_headers
            or (isinstance(env, dict) and has_sensitive_key(env))
            or (isinstance(env_vars, dict) and has_sensitive_key(env_vars))
        )
        rows.append(
            {
                "name": str(name),
                "transport": mcp_transport(server),
                "enabled": bool(server.get("enabled", True)),
                "has_env": has_env,
                "has_env_vars": has_env_vars,
                "has_http_headers": has_http_headers,
                "has_auth": has_auth,
            }
        )
    return rows


def capability_inventory(args: argparse.Namespace) -> int:
    plugin_root = resolve_path(args.plugin_root or ".")
    config_path = resolve_path(args.config) if args.config else None
    config, warnings, loaded_config = load_toml_config(config_path)
    tools = local_tool_status()
    plugins = summarize_plugins(config)
    mcp_servers = summarize_mcp_servers(config)
    recommendations: list[str] = []
    if any(server["name"] == "context7" and server["enabled"] for server in mcp_servers):
        recommendations.append("Use Context7 or configured documentation MCP for current library/API documentation when relevant.")
    if tools["gh"]["available"]:
        recommendations.append("GitHub CLI is available for opt-in PR and CI inspection workflows.")
    if tools["claude"]["available"]:
        recommendations.append("Claude CLI appears available as a possible external review candidate after explicit consent.")
    if not tools["gemini"]["available"]:
        recommendations.append("Gemini CLI was not detected; do not assume Gemini-based review is available.")
    payload = {
        "success": True,
        "gate": "capability-inventory",
        "plugin_root": str(plugin_root),
        "config_path": loaded_config,
        "warnings": warnings,
        "plugins": {"configured": plugins},
        "mcp_servers": {"configured": mcp_servers},
        "local_tools": tools,
        "recommendations": recommendations,
    }
    return print_json(payload)


def matched_workflow_terms(text: str) -> list[str]:
    haystack = text.lower()
    return [term for term in WORKFLOW_AMBIGUITY_TERMS if re.search(rf"\b{re.escape(term)}\b", haystack)]


def recommended_option(label: str, recommended: bool, rationale: str) -> dict[str, Any]:
    payload = {"label": label, "recommended": recommended, "rationale": rationale}
    if recommended:
        payload["recommended_label"] = f"{label} (Recommended)"
    return payload


def workflow_options(args: argparse.Namespace) -> int:
    brief_parts = [args.brief or ""]
    if args.spec_file:
        spec_path = resolve_path(args.spec_file)
        if not spec_path.exists():
            return print_json({"success": False, "gate": "workflow-options", "error": f"Spec file not found: {spec_path}"}, 1)
        brief_parts.append(read_text(spec_path))
    text = "\n".join(part for part in brief_parts if part)
    matched = matched_workflow_terms(text)
    explicit_depth = args.depth
    broad_prompt = len(matched) >= 1 or len(requirement_ids(text)) >= 3
    recommended_depth = explicit_depth or ("deep" if broad_prompt else "standard")
    depth_available = [
        {"value": "fast", "description": "Lightweight pass for narrow, low-risk changes."},
        {"value": "standard", "description": "Reviewed planning for ordinary implementation work."},
        {"value": "deep", "description": "Auditor-grade planning with review board and stronger traceability."},
    ]
    depth_rationale = (
        "The brief is broad or contains workflow decision terms: " + ", ".join(matched)
        if matched
        else "No broad workflow ambiguity was detected."
    )
    depth_options = [
        recommended_option("Deep", recommended_depth == "deep", depth_rationale if recommended_depth == "deep" else "Use for broad, high-impact, or ambiguous work."),
        recommended_option("Standard", recommended_depth == "standard", "Use for ordinary reviewed implementation with fewer governance decisions."),
        recommended_option("Fast", recommended_depth == "fast", "Use only for narrow, low-risk changes where detailed planning is unnecessary."),
    ]
    privacy_options = [
        recommended_option(
            "Local ignored planning",
            True,
            "Conservative default: planning artifacts stay local/ignored unless the user opts into publishing them.",
        ),
        recommended_option("Commit planning records", False, "Use only when the team wants planning records in repository history."),
    ]
    autonomy_options = [
        recommended_option("Manual", True, "Push, PR, CI watch, and fix loops require explicit opt-in."),
        recommended_option("Auto commit", False, "Only enable after user approval for local commit automation."),
        recommended_option("Auto PR and CI watch", False, "Requires remote credentials, branch policy, and explicit user approval."),
    ]
    payload = {
        "success": True,
        "gate": "workflow-options",
        "matched_terms": matched,
        "depth": {
            "selected": explicit_depth,
            "recommended": recommended_depth,
            "requires_confirmation": explicit_depth is None and broad_prompt,
            "available": depth_available,
            "reason": depth_rationale,
        },
        "interview": {
            "required": broad_prompt or recommended_depth == "deep",
            "use_structured_input_when_available": True,
            "fallback": "chat",
            "option_sets": [
                {"id": "depth", "question": "What Forge depth should this run use?", "options": depth_options},
                {"id": "planning_privacy", "question": "How should Forge planning artifacts be handled?", "options": privacy_options},
                {"id": "autonomy", "question": "How much git/PR/CI autonomy should Forge use?", "options": autonomy_options},
            ],
        },
        "git_privacy": {
            "planning_artifacts": "local_ignored",
            "mention_planning_docs": False,
            "offer_gitignore": True,
            "commit_style": "ask",
        },
        "autonomy": {
            "auto_commit": False,
            "auto_pr": False,
            "ci_watch": False,
            "fix_watch_loop": False,
            "requires_explicit_opt_in": True,
        },
        "recommendations": [
            "Ask or record material interview choices before planning.",
            "Use structured user input when available; otherwise ask in chat and record the answer.",
        ],
    }
    return print_json(payload)


def review_capabilities(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir) if args.planning_dir else None
    config: dict[str, Any] = {}
    warnings: list[str] = []
    config_path = resolve_path(args.config) if getattr(args, "config", None) else None
    if config_path:
        if config_path.exists():
            try:
                loaded = load_json(config_path)
                config = loaded if isinstance(loaded, dict) else {}
            except Exception as exc:  # pragma: no cover - exact JSON errors vary by Python version.
                warnings.append(f"Review config could not be parsed: {exc.__class__.__name__}")
        else:
            warnings.append(f"Review config file not found: {config_path}")
    elif planning_dir and (planning_dir / "zagrosi_plan_config.json").exists():
        config_path = planning_dir / "zagrosi_plan_config.json"
        config = load_json(config_path)
    configured_mode = config.get("review_mode", "codex_review")
    tools = local_tool_status(["claude", "gemini"])
    external = {
        name: {"available": item["available"], "path": item["path"], "execution": "opt_in" if item["available"] else "not_configured"}
        for name, item in tools.items()
    }
    recommendations = ["Run Codex review for every non-trivial plan and implementation section."]
    if configured_mode == "skip":
        recommendations.append("Review mode is skip; do not skip review for non-trivial or deep Forge work.")
    if configured_mode == "external_llm" and not any(item["available"] for item in external.values()):
        recommendations.append("External review mode is configured but no external CLI candidate was detected; use Codex review fallback.")
    elif configured_mode == "external_llm":
        recommendations.append("External review candidates are opt-in; run them only after explicit user consent.")
    payload = {
        "success": True,
        "gate": "review-capabilities",
        "planning_dir": str(planning_dir) if planning_dir else None,
        "config_path": str(config_path) if config_path else None,
        "configured_mode": configured_mode,
        "warnings": warnings,
        "baseline": {
            "codex_review": {
                "available": True,
                "mandatory": True,
                "execution": "agent_review",
            }
        },
        "external": external,
        "recommendations": recommendations,
    }
    return print_json(payload)


def artifact_requirement_ids(path: Path) -> tuple[list[str], list[str]]:
    text = read_text(path)
    ids = requirement_ids(text)
    meta_ids: list[str] = []
    if FORGE_META_START in text or LEGACY_META_START in text:
        meta, errors = parse_forge_meta(text)
        if not errors and isinstance(meta, dict) and isinstance(meta.get("requirement_ids"), list):
            meta_ids = [str(item) for item in meta["requirement_ids"]]
    return ids, meta_ids


def planning_consistency(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    source_path = artifact(planning_dir, ["codex-spec.md", "claude-spec.md", "spec.md"])
    findings: list[Finding] = []
    if not source_path:
        findings.append(finding("critical", "missing-requirement-source", "No normalized or split spec found.", planning_dir))
        return emit_quality("planning-consistency", findings, args, {"planning_dir": str(planning_dir)})
    source_ids = requirement_ids(read_text(source_path))
    required_artifact_names = [
        "codex-plan.md",
        "claude-plan.md",
        "codex-plan-tdd.md",
        "claude-plan-tdd.md",
        "codex-integration-notes.md",
        "claude-integration-notes.md",
        "codex-consistency-review.md",
        "traceability.md",
        "sections/index.md",
    ]
    review_artifact_names = [str(path.relative_to(planning_dir)) for path in sorted((planning_dir / "reviews").glob("*.md"))]
    artifact_names = required_artifact_names + review_artifact_names
    required_artifacts = set(required_artifact_names)
    checked: dict[str, Any] = {}
    recommendation = "Review planning docs for consistency and ask the user where clashes, replacements, or overlaps are unresolved."
    for name in artifact_names:
        path = planning_dir / name
        if not path.exists():
            continue
        ids, meta_ids = artifact_requirement_ids(path)
        missing = [req_id for req_id in source_ids if req_id not in ids]
        stale_meta = [req_id for req_id in source_ids if meta_ids and req_id not in meta_ids]
        checked[name] = {"requirement_ids": ids, "metadata_requirement_ids": meta_ids}
        if missing and name in required_artifacts:
            findings.append(
                finding(
                    "medium",
                    "missing-requirement-reference",
                    f"{name} is missing requirement references: {', '.join(missing)}",
                    path,
                    recommendation,
                )
            )
        if stale_meta and name in required_artifacts:
            findings.append(
                finding(
                    "medium",
                    "stale-requirement-metadata",
                    f"{name} metadata is missing requirement IDs: {', '.join(stale_meta)}",
                    path,
                    recommendation,
                )
            )
    payload = quality_from_args(
        "planning-consistency",
        findings,
        args,
        {"planning_dir": str(planning_dir), "source": str(source_path), "requirement_ids": source_ids, "checked_artifacts": checked},
    )
    return emit_payload(payload, args)


def status(args: argparse.Namespace) -> int:
    path = resolve_path(args.path)
    if path.is_file():
        planning_dir = path.parent
    elif path.name == "sections":
        planning_dir = path.parent
    else:
        planning_dir = path

    project_state = planning_dir / ".zagrosi-project" / "session.json"
    legacy_project_state = planning_dir / ".deep-project" / "session.json"
    if not project_state.exists() and legacy_project_state.exists():
        project_state = legacy_project_state
    plan_config = planning_dir / "zagrosi_plan_config.json"
    legacy_plan_config = planning_dir / "deep_plan_config.json"
    if not plan_config.exists() and legacy_plan_config.exists():
        plan_config = legacy_plan_config
    section_progress = check_section_progress(planning_dir)
    implementation_state = planning_dir / "implementation" / "zagrosi_implement_state.json"
    legacy_implementation_state = planning_dir / "implementation" / "deep_implement_state.json"
    if not implementation_state.exists() and legacy_implementation_state.exists():
        implementation_state = legacy_implementation_state
    files = {
        "project_manifest": str(planning_dir / "project-manifest.md") if (planning_dir / "project-manifest.md").exists() else None,
        "zagrosi_project_state": str(project_state) if project_state.exists() else None,
        "zagrosi_plan_config": str(plan_config) if plan_config.exists() else None,
        "implementation_state": str(implementation_state) if implementation_state.exists() else None,
    }
    files = {key: value for key, value in files.items() if value}
    plan_artifacts = plan_artifact_state(planning_dir) if plan_config.exists() else None
    plan_config_payload = load_json(plan_config) if plan_config.exists() else {}
    next_action = "start zagrosi-project or zagrosi-plan"
    if section_progress["state"] == "complete" and not implementation_state.exists():
        next_action = "run zagrosi-implement"
    elif implementation_state.exists():
        state = load_json(implementation_state)
        completed = set(state.get("completed_sections", {}))
        remaining = [section for section in section_progress.get("sections", []) if section not in completed]
        next_action = f"implement {remaining[0]}" if remaining else "final verification and summary"
    elif plan_config.exists():
        next_action = next_plan_action(plan_artifacts or {}, section_progress, plan_config_payload)
    elif project_state.exists():
        next_action = "finish project manifest/spec generation"

    payload: dict[str, Any] = {
        "success": True,
        "path": str(path),
        "planning_dir": str(planning_dir),
        "files": files,
        "section_progress": section_progress,
        "next_action": next_action,
    }
    if plan_artifacts is not None:
        payload["plan_artifacts"] = plan_artifact_payload(plan_artifacts)
    return print_json(payload)


def command_catalog(args: argparse.Namespace) -> int:
    phase = getattr(args, "phase", None)
    commands = [
        dict(item)
        for item in COMMAND_CATALOG
        if not phase or item["phase"] == phase or item["phase"] in {"all", "quality", "utility"}
    ]
    return print_json({"success": True, "phase_filter": phase, "commands": commands})


def traceability_analysis(planning_dir: Path) -> tuple[list[Finding], dict[str, Any]]:
    spec_path = artifact(planning_dir, ["codex-spec.md", "claude-spec.md"])
    plan_path = artifact(planning_dir, ["codex-plan.md", "claude-plan.md"])
    tdd_path = artifact(planning_dir, ["codex-plan-tdd.md", "claude-plan-tdd.md"])
    sections_dir = planning_dir / "sections"

    spec_text = read_text(spec_path) if spec_path else ""
    plan_text = read_text(plan_path) if plan_path else ""
    tdd_text = read_text(tdd_path) if tdd_path else ""
    section_files = sorted(sections_dir.glob("section-*.md")) if sections_dir.exists() else []
    section_text_by_file = {path.name: read_text(path) for path in section_files}
    req_ids = requirement_ids(spec_text)

    coverage: dict[str, Any] = {}
    for req_id in req_ids:
        sections = [name for name, text in section_text_by_file.items() if req_id in text]
        coverage[req_id] = {
            "in_plan": req_id in plan_text,
            "in_tdd": req_id in tdd_text,
            "sections": sections,
            "covered": bool(req_id in plan_text and req_id in tdd_text and sections),
        }

    uncovered = [req_id for req_id, item in coverage.items() if not item["covered"]]
    findings = [
        finding("high", "traceability-gap", f"{req_id} is not fully covered.", spec_path or planning_dir)
        for req_id in uncovered
    ]
    if not req_ids:
        findings.append(finding("medium", "no-requirement-ids", "No REQ-* IDs found in normalized spec.", spec_path or planning_dir))

    section_orphans = [
        name
        for name, text in section_text_by_file.items()
        if not set(requirement_ids(text)).intersection(req_ids)
    ]
    if section_orphans:
        findings.append(
            finding(
                "medium",
                "orphan-sections",
                f"Section files do not reference known requirements: {', '.join(section_orphans)}",
                sections_dir,
            )
        )

    tdd_req_ids = requirement_ids(tdd_text)
    test_orphans = []
    if tdd_text and contains_any(tdd_text, ["test_", "it(", "describe(", "pytest"]) and not tdd_req_ids:
        test_orphans.append(tdd_path.name if tdd_path else "codex-plan-tdd.md")
        findings.append(
            finding(
                "medium",
                "orphan-tests",
                "TDD plan names tests but does not tie them to REQ-* IDs.",
                tdd_path or planning_dir,
            )
        )

    extras = {
        "planning_dir": str(planning_dir),
        "requirement_ids": req_ids,
        "coverage": coverage,
        "implementation_evidence": implementation_evidence_by_section(planning_dir),
        "orphans": {
            "sections": section_orphans,
            "tests": test_orphans,
        },
    }
    return findings, extras


def existing_traceability_cells(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, str]] = {}
    header: list[str] | None = None
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        if header is None:
            header = cells
            continue
        if len(cells) != len(header) or not cells:
            continue
        row = dict(zip(header, cells, strict=False))
        requirement = row.get("Requirement")
        if requirement:
            rows[requirement] = row
    return rows


def requirement_implementation_status(item: dict[str, Any], completed: set[str]) -> str:
    if not item.get("covered"):
        return "Gap"
    section_names = {Path(section).stem for section in item.get("sections", [])}
    if section_names and section_names.issubset(completed):
        return "Implemented"
    if section_names.intersection(completed):
        return "Partially implemented"
    return "Planned"


def traceability_matrix_content(planning_dir: Path) -> str | None:
    findings, extras = traceability_analysis(planning_dir)
    coverage = extras.get("coverage", {})
    if not coverage:
        return None
    existing = existing_traceability_cells(planning_dir / "traceability.md")
    completed = completed_sections(planning_dir)
    evidence = implementation_evidence_by_section(planning_dir)
    lines = [
        "# Traceability Matrix",
        "",
        "| Requirement | Plan Coverage | Section Coverage | Test Coverage | Implementation Evidence | Status |",
        "|-------------|---------------|------------------|---------------|-------------------------|--------|",
    ]
    for req_id, item in coverage.items():
        previous = existing.get(req_id, {})
        plan_coverage = previous.get("Plan Coverage") or ("`codex-plan.md`" if item.get("in_plan") else "-")
        sections = "; ".join(f"`{section}`" for section in item.get("sections", [])) or previous.get("Section Coverage") or "-"
        test_coverage = previous.get("Test Coverage") or ("`codex-plan-tdd.md`" if item.get("in_tdd") else "-")
        evidence_items = [
            compact_section_evidence(evidence[Path(section).stem])
            for section in item.get("sections", [])
            if Path(section).stem in evidence
        ]
        implementation_evidence = "; ".join(item for item in evidence_items if item and item != "-") or previous.get("Implementation Evidence") or "-"
        status = requirement_implementation_status(item, completed)
        lines.append(f"| {req_id} | {plan_coverage} | {sections} | {test_coverage} | {implementation_evidence} | {status} |")
    if findings:
        lines.extend(["", "Open traceability findings:"])
        lines.extend(f"- {item.severity}: {item.code} - {item.message}" for item in findings)
    return "\n".join(lines) + "\n"


def refresh_traceability_matrix(planning_dir: Path) -> Path | None:
    content = traceability_matrix_content(planning_dir)
    if content is None:
        return None
    path = planning_dir / "traceability.md"
    path.write_text(content, encoding="utf-8")
    return path


def traceability(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    findings, extras = traceability_analysis(planning_dir)
    payload = quality_from_args(
        "traceability",
        findings,
        args,
        extras,
    )
    return emit_payload(payload, args)


def nonempty_artifact(planning_dir: Path, names: list[str]) -> Path | None:
    path = first_existing(planning_dir, names)
    if path and read_text(path).strip():
        return path
    return None


def plan_artifact_state(planning_dir: Path) -> dict[str, Path | None]:
    return {
        "research": nonempty_artifact(planning_dir, ["codex-research.md", "claude-research.md"]),
        "interview": nonempty_artifact(planning_dir, ["codex-interview.md", "claude-interview.md"]),
        "spec": nonempty_artifact(planning_dir, ["codex-spec.md", "claude-spec.md"]),
        "plan": nonempty_artifact(planning_dir, ["codex-plan.md", "claude-plan.md"]),
        "integration_notes": nonempty_artifact(
            planning_dir,
            ["codex-integration-notes.md", "claude-integration-notes.md"],
        ),
        "tdd": nonempty_artifact(planning_dir, ["codex-plan-tdd.md", "claude-plan-tdd.md"]),
        "section_index": nonempty_artifact(planning_dir / "sections", ["index.md"]),
    }


def plan_artifact_payload(state: dict[str, Path | None]) -> dict[str, str | None]:
    return {key: str(value) if value else None for key, value in state.items()}


def next_plan_action(
    artifacts: dict[str, Path | None],
    progress: dict[str, Any],
    config: dict[str, Any],
) -> str:
    if not artifacts["research"]:
        return "write codex-research.md"
    if not artifacts["interview"]:
        return "write codex-interview.md or record skipped interview"
    if not artifacts["spec"]:
        return "write codex-spec.md"
    if not artifacts["plan"]:
        return "write codex-plan.md"
    if config.get("review_mode") != "skip" and not artifacts["integration_notes"]:
        return "review plan and write codex-integration-notes.md"
    if not artifacts["tdd"]:
        return "write codex-plan-tdd.md"
    if not artifacts["section_index"]:
        return "create sections/index.md"
    if progress.get("state") in {"has_index", "partial"}:
        return "write missing section files"
    if progress.get("state") == "complete":
        return "run zagrosi-implement"
    return "run zagrosi-plan quality gates"


def write_governance_stubs(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    depth = args.depth
    created: list[str] = []
    skipped: list[str] = []
    templates = governance_templates(depth)
    for name, path in default_governance_files(planning_dir, depth).items():
        if write_if_missing(path, templates[name]):
            created.append(str(path))
        else:
            skipped.append(str(path))
    return print_json({"success": True, "planning_dir": str(planning_dir), "depth_mode": depth, "created": created, "skipped": skipped})


def review_board_prompts(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    prompts_dir = planning_dir / "reviews" / ".prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    prompts: list[str] = []
    for review_pass in REVIEW_BOARD_PASSES:
        path = prompts_dir / f"{review_pass}.md"
        path.write_text(
            (
                f"# {review_pass.replace('-', ' ').title()} Review\n\n"
                f"Review `{planning_dir}/codex-plan.md` from the perspective of {review_pass.replace('-', ' ')}.\n\n"
                "Return severity-ranked findings with evidence, file references, contract gaps, "
                "test gaps, migration/rollback concerns, and specific plan edits. Target 1,000+ "
                "words when the review surface is non-trivial. Do not rewrite the plan; identify "
                "what must change and why.\n"
            ),
            encoding="utf-8",
        )
        prompts.append(str(path))
    return print_json({"success": True, "planning_dir": str(planning_dir), "prompt_files": prompts})


def migrate(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    pairs = [
        ("claude-research.md", "codex-research.md"),
        ("claude-interview.md", "codex-interview.md"),
        ("claude-spec.md", "codex-spec.md"),
        ("claude-plan.md", "codex-plan.md"),
        ("claude-integration-notes.md", "codex-integration-notes.md"),
        ("claude-plan-tdd.md", "codex-plan-tdd.md"),
    ]
    migrated: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for old_name, new_name in pairs:
        old_path = planning_dir / old_name
        new_path = planning_dir / new_name
        if not old_path.exists():
            skipped.append({"source": str(old_path), "reason": "source_missing"})
            continue
        if new_path.exists() and not args.force:
            skipped.append({"source": str(old_path), "target": str(new_path), "reason": "target_exists"})
            continue
        new_path.write_text(read_text(old_path), encoding="utf-8")
        migrated.append({"source": str(old_path), "target": str(new_path)})

    if (planning_dir / "claude-plan.md").exists():
        templates = governance_templates(args.depth)
        for name, path in default_governance_files(planning_dir, args.depth).items():
            write_if_missing(path, templates[name])

    return print_json({"success": True, "planning_dir": str(planning_dir), "migrated": migrated, "skipped": skipped})


def doctor(args: argparse.Namespace) -> int:
    plugin_root = resolve_path(args.plugin_root) if args.plugin_root else Path(__file__).resolve().parents[1]
    findings: list[Finding] = []
    expected = [
        plugin_root / ".codex-plugin" / "plugin.json",
        plugin_root / ".agents" / "plugins" / "marketplace.json",
        plugin_root / "pyproject.toml",
        plugin_root / "scripts" / "zagrosi_skills.py",
        plugin_root / "scripts" / "deep_skills.py",
    ]
    for path in expected:
        if not path.exists():
            findings.append(finding("critical", "missing-package-file", f"Missing package file: {path}", path))

    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = load_json(manifest_path)
        except json.JSONDecodeError as exc:
            findings.append(finding("critical", "invalid-plugin-json", f"plugin.json is invalid JSON: {exc}", manifest_path))
    if manifest and manifest.get("name") != "zagrosi-forge":
        findings.append(finding("medium", "plugin-name", "Plugin package name should be zagrosi-forge.", manifest_path))

    marketplace_path = plugin_root / ".agents" / "plugins" / "marketplace.json"
    marketplace: dict[str, Any] = {}
    marketplace_entry: dict[str, Any] = {}
    if marketplace_path.exists():
        try:
            marketplace = load_json(marketplace_path)
        except json.JSONDecodeError as exc:
            findings.append(
                finding("critical", "invalid-marketplace-json", f"marketplace.json is invalid JSON: {exc}", marketplace_path)
            )
    if marketplace:
        if marketplace.get("name") != "zagrosi":
            findings.append(finding("medium", "marketplace-name", "Marketplace name should be zagrosi.", marketplace_path))
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list):
            findings.append(finding("high", "marketplace-plugins", "marketplace.json must contain a plugins array.", marketplace_path))
        else:
            for item in plugins:
                if isinstance(item, dict) and item.get("name") == "zagrosi-forge":
                    marketplace_entry = item
                    break
            if not marketplace_entry:
                findings.append(
                    finding("high", "marketplace-plugin-entry", "Marketplace must include zagrosi-forge.", marketplace_path)
                )
    if marketplace_entry:
        source = marketplace_entry.get("source")
        if not isinstance(source, dict) or source.get("source") != "local" or source.get("path") not in {".", "./"}:
            findings.append(
                finding(
                    "medium",
                    "marketplace-plugin-source",
                    "zagrosi-forge marketplace source should be local with path './'.",
                    marketplace_path,
                )
            )
        policy = marketplace_entry.get("policy")
        if not isinstance(policy, dict):
            findings.append(finding("high", "marketplace-plugin-policy", "Marketplace entry must include policy.", marketplace_path))
        else:
            if policy.get("installation") not in {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}:
                findings.append(
                    finding("high", "marketplace-installation-policy", "Invalid marketplace installation policy.", marketplace_path)
                )
            if policy.get("authentication") not in {"ON_INSTALL", "ON_USE"}:
                findings.append(
                    finding("high", "marketplace-authentication-policy", "Invalid marketplace authentication policy.", marketplace_path)
                )
        if not marketplace_entry.get("category"):
            findings.append(finding("low", "marketplace-category", "Marketplace entry should include a category.", marketplace_path))

    for skill_name in ("zagrosi-project", "zagrosi-plan", "zagrosi-implement"):
        skill_path = plugin_root / "skills" / skill_name / "SKILL.md"
        if not skill_path.exists():
            findings.append(finding("critical", "missing-skill", f"Missing skill: {skill_name}", skill_path))
            continue
        text = read_text(skill_path)
        if f"name: {skill_name}" not in text[:300]:
            findings.append(finding("high", "skill-frontmatter", f"{skill_name} frontmatter name is missing or stale.", skill_path))
        if "scripts/zagrosi_skills.py" not in text:
            findings.append(finding("medium", "skill-helper-reference", f"{skill_name} does not reference the Zagrosi helper script.", skill_path))

    if sys.version_info < (3, 11):
        findings.append(finding("critical", "python-version", "Python 3.11 or newer is required."))

    extras = {
        "plugin_root": str(plugin_root),
        "python": sys.version.split()[0],
        "marketplace": {
            "name": marketplace.get("name"),
            "plugin": "zagrosi-forge@zagrosi" if marketplace_entry else None,
            "path": str(marketplace_path),
        },
        "skills": ["zagrosi-project", "zagrosi-plan", "zagrosi-implement"],
        "plugin_scoped_skills": [
            "zagrosi-forge:zagrosi-project",
            "zagrosi-forge:zagrosi-plan",
            "zagrosi-forge:zagrosi-implement",
        ],
    }
    return emit_quality("doctor", findings, args, extras)


def section_estimates(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    progress = check_section_progress(planning_dir)
    if progress["state"] in {"invalid_index", "no_index"}:
        return print_json({"success": False, "section_progress": progress}, 1)
    deps = dependency_graph(planning_dir, progress)
    estimates = [
        section_metrics(section, planning_dir / "sections" / f"{section}.md", deps)
        for section in progress["sections"]
        if (planning_dir / "sections" / f"{section}.md").exists()
    ]
    return print_json(
        {
            "success": True,
            "planning_dir": str(planning_dir),
            "section_progress": progress,
            "estimates": estimates,
        }
    )


def next_section(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    progress = check_section_progress(planning_dir)
    if progress["state"] in {"invalid_index", "no_index"}:
        return print_json({"success": False, "section_progress": progress}, 1)
    deps = dependency_graph(planning_dir, progress)
    completed = completed_sections(planning_dir)
    ready = ready_sections(progress, deps, completed)
    remaining = [section for section in progress["sections"] if section not in completed]
    blocked = {
        section: [dep for dep in deps.get(section, []) if dep not in completed]
        for section in remaining
        if section not in ready
    }
    return print_json(
        {
            "success": bool(ready) or not remaining,
            "planning_dir": str(planning_dir),
            "next_section": ready[0] if ready else None,
            "ready_sections": ready,
            "remaining_sections": remaining,
            "blocked_sections": blocked,
            "completed_sections": sorted(completed),
        },
        0 if ready or not remaining else 1,
    )


def parallel_plan(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    progress = check_section_progress(planning_dir)
    if progress["state"] in {"invalid_index", "no_index"}:
        return print_json({"success": False, "section_progress": progress}, 1)
    deps = dependency_graph(planning_dir, progress)
    completed = completed_sections(planning_dir)
    known = set(progress["sections"])
    remaining = [section for section in progress["sections"] if section not in completed]
    available = set(completed)
    layers: list[list[str]] = []
    unresolved = set(remaining)

    while unresolved:
        layer = sorted(
            section
            for section in unresolved
            if all(dep in available for dep in deps.get(section, []))
        )
        if not layer:
            break
        layers.append(layer)
        available.update(layer)
        unresolved.difference_update(layer)

    unknown_dependencies = {
        section: [dep for dep in deps.get(section, []) if dep not in known]
        for section in progress["sections"]
        if any(dep not in known for dep in deps.get(section, []))
    }
    success = not unresolved and not unknown_dependencies
    return print_json(
        {
            "success": success,
            "planning_dir": str(planning_dir),
            "completed_sections": sorted(completed),
            "layers": layers,
            "blocked_or_cyclic": sorted(unresolved),
            "unknown_dependencies": unknown_dependencies,
        },
        0 if success else 1,
    )


def changed_files_from_diff(text: str) -> list[str]:
    files: set[str] = set()
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.add(parts[3].removeprefix("b/"))
        elif line.startswith("+++ b/"):
            files.add(line[6:].strip())
        else:
            stripped = line.strip().removeprefix("./")
            if FILE_PATH_RE.fullmatch(stripped):
                files.add(stripped.strip("`"))
    return sorted(file for file in files if file != "/dev/null")


def git_changed_files(repo: Path, staged: bool) -> tuple[list[str], str | None]:
    commands = [["diff", "--name-only", "--cached"]]
    if not staged:
        commands = [
            ["diff", "--name-only"],
            ["diff", "--name-only", "--cached"],
            ["ls-files", "--others", "--exclude-standard"],
        ]
    changed: set[str] = set()
    for command in commands:
        result = git(command, repo)
        if result.returncode != 0:
            return [], result.stderr.strip() or result.stdout.strip()
        changed.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return sorted(changed), None


def patch_scope(args: argparse.Namespace) -> int:
    section_file = resolve_path(args.section_file)
    if not section_file.exists():
        return print_json({"success": False, "error": f"Section file not found: {section_file}"}, 1)
    declared = set(extract_file_paths(read_text(section_file)))
    if args.diff_file:
        diff_path = resolve_path(args.diff_file)
        if not diff_path.exists():
            return print_json({"success": False, "error": f"Diff file not found: {diff_path}"}, 1)
        changed = set(changed_files_from_diff(read_text(diff_path)))
    else:
        changed_list, error = git_changed_files(resolve_path(args.repo), args.staged)
        if error:
            return print_json({"success": False, "error": error}, 1)
        changed = set(changed_list)

    out_of_scope = sorted(file for file in changed if file not in declared)
    missing_declared = sorted(file for file in declared if file not in changed)
    findings: list[Finding] = []
    for file in out_of_scope:
        findings.append(finding("high", "out-of-scope-file", f"Changed file is not declared in section: {file}", section_file))
    if missing_declared:
        findings.append(
            finding(
                "low",
                "declared-file-not-changed",
                f"Declared files not present in patch: {', '.join(missing_declared)}",
                section_file,
            )
        )
    payload = quality_from_args(
        "patch-scope",
        findings,
        args,
        {
            "section_file": str(section_file),
            "declared_files": sorted(declared),
            "changed_files": sorted(changed),
            "out_of_scope": out_of_scope,
            "missing_declared": missing_declared,
        },
    )
    return emit_payload(payload, args)


def commit_message(args: argparse.Namespace) -> int:
    section_file = resolve_path(args.section_file)
    if not section_file.exists():
        return print_json({"success": False, "error": f"Section file not found: {section_file}"}, 1)
    section = section_file.stem
    label = section.removeprefix("section-").replace("-", " ")
    if args.style == "conventional":
        subject = f"feat: implement {label}"
    else:
        subject = f"Implement {label}"
    text = read_text(section_file)
    req_ids = requirement_ids(text)
    files = extract_file_paths(text)
    body_lines = []
    if req_ids:
        body_lines.append(f"Requirements: {', '.join(req_ids)}")
    if files:
        body_lines.append(f"Scope: {', '.join(files[:8])}" + (" ..." if len(files) > 8 else ""))
    body_lines.append("Tests and review follow the section plan.")
    return print_json(
        {
            "success": True,
            "section_file": str(section_file),
            "subject": subject[:72],
            "body": "\n".join(body_lines),
            "message": subject[:72] + "\n\n" + "\n".join(body_lines),
        }
    )


def requirement_candidate(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith(("-", "*")):
        return False
    if "REQ-" in stripped:
        return False
    return contains_any(
        stripped,
        ["must", "should", "shall", "allow", "support", "enable", "provide", "user can", "system can", "needs to"],
    )


def extract_requirements(args: argparse.Namespace) -> int:
    path = resolve_path(args.file)
    if not path.exists():
        return print_json({"success": False, "error": f"File not found: {path}"}, 1)
    text = read_text(path)
    existing = requirement_ids(text)
    next_number = 1
    if existing:
        numeric = [int(match.group(1)) for req in existing if (match := re.match(r"REQ-(\d+)$", req))]
        next_number = max(numeric, default=0) + 1

    requirements: list[dict[str, str]] = []
    rewritten: list[str] = []
    for line in text.splitlines():
        if requirement_candidate(line):
            req_id = f"REQ-{next_number:03d}"
            next_number += 1
            prefix, body = line.split(maxsplit=1)
            rewritten_line = f"{prefix} {req_id}: {body}"
            requirements.append({"id": req_id, "text": body.strip(), "line": rewritten_line})
            rewritten.append(rewritten_line)
        else:
            rewritten.append(line)

    if args.write and requirements:
        path.write_text("\n".join(rewritten) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")

    return print_json(
        {
            "success": True,
            "file": str(path),
            "requirements": requirements,
            "updated": bool(args.write and requirements),
            "content": "\n".join(rewritten),
        }
    )


def trace_export(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    findings, extras = traceability_analysis(planning_dir)
    payload = quality_from_args("traceability", findings, args, extras)
    rows = [
        {
            "requirement": req_id,
            "in_plan": str(item["in_plan"]).lower(),
            "in_tdd": str(item["in_tdd"]).lower(),
            "sections": ";".join(item["sections"]),
            "covered": str(item["covered"]).lower(),
        }
        for req_id, item in payload["coverage"].items()
    ]

    if args.format == "json":
        content = json.dumps({"rows": rows, "orphans": payload["orphans"]}, indent=2, sort_keys=True) + "\n"
    elif args.format == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["requirement", "in_plan", "in_tdd", "sections", "covered"])
        writer.writeheader()
        writer.writerows(rows)
        content = buffer.getvalue()
    else:
        lines = ["| Requirement | In Plan | In TDD | Sections | Covered |", "|-------------|---------|--------|----------|---------|"]
        for row in rows:
            lines.append(
                f"| {row['requirement']} | {row['in_plan']} | {row['in_tdd']} | {row['sections'] or '-'} | {row['covered']} |"
            )
        content = "\n".join(lines) + "\n"

    if args.output:
        output = resolve_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        payload["output"] = str(output)
    else:
        payload["content"] = content
    return emit_payload(payload, args)


def agent_prompts(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    prompt_names = sorted(PROMPT_TYPES) if args.type == "all" else [args.type]
    prompts_dir = planning_dir / ".prompts" / "agents"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name in prompt_names:
        path = prompts_dir / f"{name}.md"
        path.write_text(
            (
                f"# {name.replace('-', ' ').title()}\n\n"
                f"{PROMPT_TYPES[name]}\n\n"
                f"Planning directory: `{planning_dir}`\n\n"
                "Use only evidence from the repository and named planning artifacts. "
                "Return concise findings with paths, risks, and recommended next actions.\n"
            ),
            encoding="utf-8",
        )
        written.append(str(path))
    return print_json({"success": True, "planning_dir": str(planning_dir), "prompt_files": written})


def context_budget(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    candidates = [
        path
        for path in [
            artifact(planning_dir, ["codex-spec.md", "claude-spec.md"]),
            artifact(planning_dir, ["codex-plan.md", "claude-plan.md"]),
            artifact(planning_dir, ["codex-plan-tdd.md", "claude-plan-tdd.md"]),
            planning_dir / "decisions.md",
            planning_dir / "risk-register.md",
            planning_dir / "traceability.md",
            planning_dir / "quality-gates.md",
        ]
        if path and path.exists()
    ]
    sections_dir = planning_dir / "sections"
    if sections_dir.exists():
        candidates.extend(sorted(sections_dir.glob("*.md")))

    files = [{"path": str(path), "word_count": word_count(read_text(path))} for path in candidates]
    total_words = sum(item["word_count"] for item in files)
    findings: list[Finding] = []
    if total_words > args.max_words:
        findings.append(
            finding(
                "medium",
                "context-budget-exceeded",
                f"Planning artifacts total {total_words} words, above budget {args.max_words}.",
                planning_dir,
                "Prefer section-specific context, summaries, and trace exports before implementation.",
            )
        )
    largest = sorted(files, key=lambda item: item["word_count"], reverse=True)[:5]
    return emit_quality(
        "context-budget",
        findings,
        args,
        {
            "planning_dir": str(planning_dir),
            "max_words": args.max_words,
            "total_words": total_words,
            "largest_files": largest,
        },
    )


def planning_artifacts(planning_dir: Path) -> dict[str, Path | None]:
    return {
        "spec": artifact(planning_dir, ["codex-spec.md", "claude-spec.md"]),
        "research": artifact(planning_dir, ["codex-research.md", "claude-research.md"]),
        "interview": artifact(planning_dir, ["codex-interview.md", "claude-interview.md"]),
        "plan": artifact(planning_dir, ["codex-plan.md", "claude-plan.md"]),
        "integration_notes": artifact(planning_dir, ["codex-integration-notes.md", "claude-integration-notes.md"]),
        "tdd": artifact(planning_dir, ["codex-plan-tdd.md", "claude-plan-tdd.md"]),
        "evidence": planning_dir / "codex-evidence.md",
        "decisions": planning_dir / "decisions.md",
        "risks": planning_dir / "risk-register.md",
        "traceability": planning_dir / "traceability.md",
        "quality": planning_dir / "quality-gates.md",
    }


def plan_artifact_findings(planning_dir: Path) -> tuple[list[Finding], dict[str, Any]]:
    artifacts = planning_artifacts(planning_dir)
    required = {
        "research": "research notes",
        "evidence": "codebase evidence",
        "interview": "interview record",
        "spec": "normalized spec",
        "plan": "implementation plan",
        "integration_notes": "review integration notes",
        "tdd": "TDD plan",
        "decisions": "decision log",
        "risks": "risk register",
        "traceability": "traceability matrix",
        "quality": "quality gates",
    }
    expected_names = {
        "research": "codex-research.md",
        "evidence": "codex-evidence.md",
        "interview": "codex-interview.md",
        "spec": "codex-spec.md",
        "plan": "codex-plan.md",
        "integration_notes": "codex-integration-notes.md",
        "tdd": "codex-plan-tdd.md",
        "decisions": "decisions.md",
        "risks": "risk-register.md",
        "traceability": "traceability.md",
        "quality": "quality-gates.md",
    }
    findings: list[Finding] = []
    present: dict[str, str] = {}
    def has_placeholder_cell(text: str) -> bool:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.lower() in {"tbd", "todo"} or stripped.lower().startswith("[todo:"):
                return True
            if "|" not in stripped:
                continue
            cells = [cell.strip().lower() for cell in stripped.strip("|").split("|")]
            if any(cell in {"tbd", "todo"} or cell.startswith("[todo:") for cell in cells):
                return True
        return False

    for key, label in required.items():
        path = artifacts.get(key)
        expected = path or planning_dir / expected_names[key]
        if not path or not path.exists():
            findings.append(
                finding(
                    "critical",
                    f"missing-{key}",
                    f"Missing Forge {label}. Complete zagrosi-plan before implementation.",
                    expected,
                )
            )
            continue
        text = read_text(path)
        if not text.strip():
            findings.append(
                finding(
                    "critical",
                    f"empty-{key}",
                    f"Forge {label} is empty. Complete zagrosi-plan before implementation.",
                    path,
                )
            )
            continue
        present[key] = str(path)
        if has_placeholder_cell(text):
            findings.append(
                finding(
                    "critical",
                    f"placeholder-{key}",
                    f"Forge {label} still contains placeholder text.",
                    path,
                    "Replace setup stubs with the completed planning artifact before implementation.",
                )
            )

    reviews_dir = planning_dir / "reviews"
    review_files = sorted(path for path in reviews_dir.glob("*.md") if path.is_file()) if reviews_dir.exists() else []
    nonempty_review_files = [path for path in review_files if read_text(path).strip()]
    if not nonempty_review_files:
        findings.append(
            finding(
                "critical",
                "missing-review",
                "Missing Forge plan review file under reviews/.",
                reviews_dir,
                "Run the review step and write at least one concrete review artifact before implementation.",
            )
        )
    else:
        present["reviews"] = [str(path) for path in nonempty_review_files]

    progress = check_section_progress(planning_dir)
    if progress.get("state") == "no_index":
        findings.append(
            finding(
                "critical",
                "missing-section-index",
                "Missing sections/index.md. Complete sectioning before implementation.",
                planning_dir / "sections" / "index.md",
            )
        )
    elif progress.get("state") != "complete":
        findings.append(
            finding(
                "critical",
                "incomplete-sections",
                f"Section files are not complete: {progress.get('progress', 'unknown progress')}.",
                planning_dir / "sections",
                "Write every section in SECTION_MANIFEST before implementation.",
            )
        )

    return findings, {
        "planning_dir": str(planning_dir),
        "required_artifacts": sorted(required),
        "present_artifacts": present,
        "section_progress": progress,
    }


def plan_artifacts_payload(planning_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    findings, extras = plan_artifact_findings(planning_dir)
    return quality_from_args("plan-artifacts", findings, args, extras)


def existing_artifact_texts(planning_dir: Path) -> dict[str, str]:
    return {
        name: read_text(path)
        for name, path in planning_artifacts(planning_dir).items()
        if path and path.exists()
    }


def markdown_headings(text: str) -> list[str]:
    return [line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")]


def test_names(text: str) -> list[str]:
    found: set[str] = set()
    for pattern in (
        r"\btest_[A-Za-z0-9_]+\b(?!\.)",
        r"`([a-z][a-z0-9_]*_[a-z0-9_]+)`",
        r"\bit\([\"']([^\"']+)[\"']\)",
        r"\bdescribe\([\"']([^\"']+)[\"']\)",
    ):
        for match in re.finditer(pattern, text):
            found.add(match.group(1) if match.groups() else match.group(0))
    return sorted(found)


def add_term_findings(findings: list[Finding], text: str, groups: dict[str, list[str]], path: Path, severity: str) -> None:
    for label, terms in groups.items():
        if not contains_any(text, terms):
            findings.append(
                finding(
                    severity,
                    f"missing-{label}",
                    f"Missing {label.replace('-', ' ')} evidence.",
                    path,
                    f"Add concrete {label.replace('-', ' ')} details backed by files, commands, contracts, or tests.",
                )
            )


def lint_evidence(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    texts = existing_artifact_texts(planning_dir)
    plan_path = planning_artifacts(planning_dir)["plan"] or planning_dir / "codex-plan.md"
    combined = "\n\n".join(texts.values())
    findings: list[Finding] = []
    if not texts.get("plan"):
        findings.append(finding("critical", "missing-plan", "Implementation plan is missing.", plan_path))
    add_term_findings(findings, combined, EVIDENCE_TERMS, plan_path, "medium")
    paths = extract_file_paths(combined)
    if len(paths) < args.min_files:
        findings.append(
            finding(
                "medium",
                "thin-file-evidence",
                f"Only {len(paths)} concrete file paths found; expected at least {args.min_files}.",
                plan_path,
                "Name inspected files, tests, config files, and implementation targets.",
            )
        )
    req_ids = requirement_ids(combined)
    if not req_ids:
        findings.append(finding("medium", "no-requirement-ids", "No REQ-* IDs found in evidence surface.", plan_path))
    assumptions = [
        line.strip()
        for line in combined.splitlines()
        if contains_any(line, ["assumption", "unknown", "open question", "stop-line", "stop line"])
    ]
    payload = quality_from_args(
        "evidence",
        findings,
        args,
        {
            "planning_dir": str(planning_dir),
            "artifacts": sorted(path.name for path in planning_artifacts(planning_dir).values() if path and path.exists()),
            "files": paths,
            "file_count": len(paths),
            "requirement_ids": req_ids,
            "assumption_lines": assumptions[:25],
            "artifact_word_counts": {name: word_count(text) for name, text in texts.items()},
        },
    )
    return emit_payload(payload, args)


def lint_implementation_readiness(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    progress = check_section_progress(planning_dir)
    findings: list[Finding] = []
    if progress["state"] in {"invalid_index", "no_index"}:
        findings.append(finding("critical", "invalid-sections", "Readiness requires a valid sections/index.md.", planning_dir / "sections" / "index.md"))
        return emit_quality("implementation-readiness", findings, args, {"section_progress": progress})

    deps = dependency_graph(planning_dir, progress)
    section_payloads: list[dict[str, Any]] = []
    for section in progress["sections"]:
        path = planning_dir / "sections" / f"{section}.md"
        if not path.exists():
            findings.append(finding("critical", "missing-section-file", f"{section}.md is missing.", path))
            continue
        text = read_text(path)
        metrics = section_metrics(section, path, deps)
        section_payloads.append(metrics)
        add_term_findings(findings, text, READINESS_TERMS, path, "medium")
        if metrics["file_count"] == 0:
            findings.append(finding("medium", "no-file-ownership", f"{section} names no implementation files.", path))
        if metrics["file_count"] > args.max_files:
            findings.append(
                finding(
                    "high",
                    "too-many-owned-files",
                    f"{section} owns {metrics['file_count']} files; max readiness threshold is {args.max_files}.",
                    path,
                    "Split the section or narrow file ownership before implementation.",
                )
            )
        if not test_names(text):
            findings.append(finding("medium", "no-test-names", f"{section} names no concrete tests.", path))

    return emit_quality(
        "implementation-readiness",
        findings,
        args,
        {
            "planning_dir": str(planning_dir),
            "section_progress": progress,
            "sections": section_payloads,
        },
    )


def forge_score(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    pseudo_args = argparse.Namespace(
        planning_dir=str(planning_dir),
        depth=args.depth,
        profile=args.profile,
        strict=False,
        export=None,
        export_format="jsonl",
        max_files=args.max_files,
        min_files=args.min_files,
    )
    plan_findings, plan_extras = plan_findings_for_score(planning_dir, args.depth)
    section_findings, section_extras = section_findings_for_score(planning_dir, args.depth)
    trace_findings, trace_extras = traceability_analysis(planning_dir)
    evidence_payload = quality_from_args("evidence", evidence_findings_for_score(planning_dir, args.min_files), pseudo_args)
    readiness_payload = quality_from_args(
        "implementation-readiness",
        readiness_findings_for_score(planning_dir, args.max_files),
        pseudo_args,
    )
    components = {
        "plan_depth": quality_payload("plan", plan_findings, plan_extras, profile=args.profile)["score"],
        "section_readiness": quality_payload("sections", section_findings, section_extras, profile=args.profile)["score"],
        "traceability": quality_payload("traceability", trace_findings, trace_extras, profile=args.profile)["score"],
        "evidence_quality": evidence_payload["score"],
        "implementation_readiness": readiness_payload["score"],
    }
    findings = plan_findings + section_findings + trace_findings
    findings.extend(evidence_findings_for_score(planning_dir, args.min_files))
    findings.extend(readiness_findings_for_score(planning_dir, args.max_files))
    weights = FORGE_COMPONENT_WEIGHTS.get(args.profile, FORGE_COMPONENT_WEIGHTS["solo"])
    weight_total = sum(weights.get(key, 1.0) for key in components)
    score = round(sum(value * weights.get(key, 1.0) for key, value in components.items()) / weight_total)
    blocking_findings = [item for item in findings if item.severity in {"critical", "high"}]
    advisory_findings = [item for item in findings if item.severity in {"medium", "low"}]
    blocking_score = quality_score(blocking_findings, args.profile)
    advisory_score = quality_score(advisory_findings, args.profile)
    trend = None
    history_path = planning_dir / ".forge" / "scores" / "history.jsonl"
    if history_path.exists():
        previous_rows = [json.loads(line) for line in read_text(history_path).splitlines() if line.strip()]
        if previous_rows:
            trend = score - int(previous_rows[-1].get("forge_score", score))
    payload = quality_payload(
        "forge-score",
        findings,
        {
            "planning_dir": str(planning_dir),
            "depth_mode": args.depth,
            "components": components,
            "component_weights": weights,
            "forge_score": score,
            "blocking_score": blocking_score,
            "advisory_score": advisory_score,
            "trend_delta": trend,
            "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D",
        },
        profile=args.profile,
        strict=args.strict,
    )
    payload["score"] = score
    if args.write_history:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp": now_iso(),
            "depth_mode": args.depth,
            "profile": args.profile,
            "forge_score": score,
            "components": components,
            "blocking_score": blocking_score,
            "advisory_score": advisory_score,
        }
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        payload["history_path"] = str(history_path)
    return emit_payload(payload, args)


def plan_findings_for_score(planning_dir: Path, depth: str) -> tuple[list[Finding], dict[str, Any]]:
    args = argparse.Namespace(planning_dir=str(planning_dir), depth=depth, profile="solo", strict=False, export=None, export_format="jsonl")
    original_emit = emit_payload
    captured: dict[str, Any] = {}

    def capture(payload: dict[str, Any], _args: argparse.Namespace, exit_code: int | None = None) -> int:
        captured.update(payload)
        return 0

    globals()["emit_payload"] = capture
    try:
        lint_plan(args)
    finally:
        globals()["emit_payload"] = original_emit
    findings = [Finding(item["severity"], item["code"], item["message"], item.get("path"), item.get("recommendation"), item.get("category", "general")) for item in captured.get("findings", [])]
    return findings, {key: value for key, value in captured.items() if key not in {"findings", "success", "score", "finding_count"}}


def section_findings_for_score(planning_dir: Path, depth: str) -> tuple[list[Finding], dict[str, Any]]:
    args = argparse.Namespace(planning_dir=str(planning_dir), depth=depth, profile="solo", strict=False, export=None, export_format="jsonl")
    original_emit = emit_payload
    captured: dict[str, Any] = {}

    def capture(payload: dict[str, Any], _args: argparse.Namespace, exit_code: int | None = None) -> int:
        captured.update(payload)
        return 0

    globals()["emit_payload"] = capture
    try:
        lint_sections(args)
    finally:
        globals()["emit_payload"] = original_emit
    findings = [Finding(item["severity"], item["code"], item["message"], item.get("path"), item.get("recommendation"), item.get("category", "general")) for item in captured.get("findings", [])]
    return findings, {key: value for key, value in captured.items() if key not in {"findings", "success", "score", "finding_count"}}


def evidence_findings_for_score(planning_dir: Path, min_files: int) -> list[Finding]:
    texts = existing_artifact_texts(planning_dir)
    combined = "\n\n".join(texts.values())
    path = planning_artifacts(planning_dir)["plan"] or planning_dir / "codex-plan.md"
    findings: list[Finding] = []
    add_term_findings(findings, combined, EVIDENCE_TERMS, path, "medium")
    if len(extract_file_paths(combined)) < min_files:
        findings.append(finding("medium", "thin-file-evidence", f"Fewer than {min_files} concrete file paths found.", path))
    return findings


def readiness_findings_for_score(planning_dir: Path, max_files: int) -> list[Finding]:
    progress = check_section_progress(planning_dir)
    if progress["state"] in {"invalid_index", "no_index"}:
        return [finding("critical", "invalid-sections", "Readiness requires valid sections.", planning_dir / "sections" / "index.md")]
    deps = dependency_graph(planning_dir, progress)
    findings: list[Finding] = []
    for section in progress["sections"]:
        path = planning_dir / "sections" / f"{section}.md"
        if not path.exists():
            findings.append(finding("critical", "missing-section-file", f"{section}.md is missing.", path))
            continue
        text = read_text(path)
        metrics = section_metrics(section, path, deps)
        add_term_findings(findings, text, READINESS_TERMS, path, "medium")
        if metrics["file_count"] > max_files:
            findings.append(finding("high", "too-many-owned-files", f"{section} owns too many files.", path))
        if not test_names(text):
            findings.append(finding("medium", "no-test-names", f"{section} names no concrete tests.", path))
    return findings


def assumption_ledger(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    texts = existing_artifact_texts(planning_dir)
    rows: list[dict[str, str]] = []
    labels = {
        "assumption": ["assumption", "assume", "assumes"],
        "open_question": ["open question", "unknown", "unclear"],
        "stop_line": ["stop-line", "stop line", "stop and"],
    }
    for name, text in texts.items():
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip("- ").strip()
            if not stripped:
                continue
            for label, terms in labels.items():
                if contains_any(stripped, terms):
                    rows.append({"type": label, "artifact": name, "line": str(line_no), "text": stripped})
                    break
    content = "# Assumption Ledger\n\n| Type | Artifact | Line | Text |\n|------|----------|------|------|\n"
    for row in rows:
        safe_text = row["text"].replace("|", "\\|")
        content += f"| {row['type']} | {row['artifact']} | {row['line']} | {safe_text} |\n"
    output = None
    if args.write:
        output = planning_dir / "assumption-ledger.md"
        output.write_text(content, encoding="utf-8")
    return print_json({"success": True, "planning_dir": str(planning_dir), "count": len(rows), "rows": rows, "output": str(output) if output else None, "content": content if not output else None})


def implementation_packet(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    section = args.section
    section_path = planning_dir / "sections" / f"{section}.md"
    if not section_path.exists():
        return print_json({"success": False, "error": f"Section file not found: {section_path}"}, 1)
    artifacts = planning_artifacts(planning_dir)
    tdd_text = read_text(artifacts["tdd"]) if artifacts["tdd"] and artifacts["tdd"].exists() else ""
    trace_findings, trace = traceability_analysis(planning_dir)
    section_text = read_text(section_path)
    reqs = requirement_ids(section_text)
    tests = test_names(section_text + "\n" + tdd_text)
    files = extract_file_paths(section_text)
    content = (
        f"# Implementation Packet: {section}\n\n"
        f"Planning directory: `{planning_dir}`\n\n"
        f"## Requirements\n\n{', '.join(reqs) if reqs else 'No requirement IDs found.'}\n\n"
        f"## Owned Files\n\n" + "\n".join(f"- `{file}`" for file in files) + "\n\n"
        f"## Tests\n\n" + "\n".join(f"- `{name}`" for name in tests) + "\n\n"
        f"## Traceability\n\n```json\n{json.dumps(trace.get('coverage', {}), indent=2, sort_keys=True)}\n```\n\n"
        f"## Section\n\n{section_text}\n"
    )
    output_dir = resolve_path(args.output_dir) if args.output_dir else planning_dir / ".forge" / "packets"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{section}-packet.md"
    output.write_text(content, encoding="utf-8")
    return print_json({"success": not trace_findings, "planning_dir": str(planning_dir), "section": section, "output": str(output), "requirements": reqs, "files": files, "tests": tests})


def context_brief(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    section_path = planning_dir / "sections" / f"{args.section}.md" if args.section else None
    artifacts = planning_artifacts(planning_dir)
    parts = ["# Context Brief\n"]
    for name in ("spec", "plan", "tdd", "decisions", "risks", "traceability"):
        path = artifacts.get(name)
        if path and path.exists():
            text = read_text(path)
            parts.append(f"## {name.replace('_', ' ').title()}\n")
            parts.append("\n".join(text.splitlines()[: args.lines_per_artifact]))
            parts.append("\n")
    if section_path and section_path.exists():
        parts.append(f"## Section: {args.section}\n")
        parts.append(read_text(section_path))
    content = "\n".join(parts)
    output = None
    if args.output:
        output = resolve_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    return print_json({"success": True, "planning_dir": str(planning_dir), "section": args.section, "word_count": word_count(content), "output": str(output) if output else None, "content": None if output else content})


def tdd_skeletons(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    artifacts = planning_artifacts(planning_dir)
    if not artifacts["tdd"] or not artifacts["tdd"].exists():
        return print_json({"success": False, "error": "codex-plan-tdd.md is missing"}, 1)
    text = read_text(artifacts["tdd"])
    tests = test_names(text)
    output_dir = resolve_path(args.output_dir) if args.output_dir else planning_dir / ".forge" / "tdd-skeletons"
    output_dir.mkdir(parents=True, exist_ok=True)
    ext = {"pytest": "py", "vitest": "ts", "go": "go", "rust": "rs"}[args.framework]
    output = output_dir / f"test_skeleton.{ext}"
    if args.framework == "pytest":
        body = "\n\n".join(f"def {name}():\n    \"\"\"Generated from Forge TDD plan. Replace with real red test.\"\"\"\n    raise AssertionError(\"red test not implemented\")" for name in tests if name.startswith("test_"))
    elif args.framework == "vitest":
        body = "import { describe, it, expect } from 'vitest';\n\n" + "\n\n".join(f"it('{name}', () => {{\n  expect.fail('red test not implemented');\n}});" for name in tests)
    elif args.framework == "go":
        body = "package tests\n\nimport \"testing\"\n\n" + "\n\n".join(f"func Test{re.sub(r'[^A-Za-z0-9]', '', name.title())}(t *testing.T) {{\n\tt.Fatal(\"red test not implemented\")\n}}" for name in tests)
    else:
        body = "\n\n".join(f"#[test]\nfn {re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())}() {{\n    panic!(\"red test not implemented\");\n}}" for name in tests)
    output.write_text(body + "\n", encoding="utf-8")
    return print_json({"success": True, "planning_dir": str(planning_dir), "framework": args.framework, "tests": tests, "output": str(output)})


def plan_diff(args: argparse.Namespace) -> int:
    before = resolve_path(args.before)
    after = resolve_path(args.after)
    if not before.exists() or not after.exists():
        return print_json({"success": False, "error": "Both --before and --after must exist."}, 1)
    before_text = read_text(before)
    after_text = read_text(after)
    result = {
        "success": True,
        "before": str(before),
        "after": str(after),
        "word_delta": word_count(after_text) - word_count(before_text),
        "requirements_added": sorted(set(requirement_ids(after_text)) - set(requirement_ids(before_text))),
        "requirements_removed": sorted(set(requirement_ids(before_text)) - set(requirement_ids(after_text))),
        "headings_added": sorted(set(markdown_headings(after_text)) - set(markdown_headings(before_text))),
        "headings_removed": sorted(set(markdown_headings(before_text)) - set(markdown_headings(after_text))),
        "files_added": sorted(set(extract_file_paths(after_text)) - set(extract_file_paths(before_text))),
        "files_removed": sorted(set(extract_file_paths(before_text)) - set(extract_file_paths(after_text))),
    }
    return print_json(result)


def lint_review_integration(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    findings: list[Finding] = []
    reviews_dir = planning_dir / "reviews"
    integration = planning_artifacts(planning_dir)["integration_notes"]
    plan = planning_artifacts(planning_dir)["plan"]
    review_files = sorted(reviews_dir.glob("*.md")) if reviews_dir.exists() else []
    if not review_files:
        findings.append(finding("medium", "missing-reviews", "No review files found.", reviews_dir))
    if not integration or not integration.exists():
        findings.append(finding("medium", "missing-integration-notes", "Integration notes are missing.", planning_dir / "codex-integration-notes.md"))
        integration_text = ""
    else:
        integration_text = read_text(integration)
        add_term_findings(
            findings,
            integration_text,
            {
                "accepted-review-items": ["accepted", "integrated", "changed", "updated"],
                "rejected-review-items": ["rejected", "deferred", "not accepted", "rationale"],
                "plan-edits": ["plan", "codex-plan.md", "section", "tdd"],
            },
            integration,
            "medium",
        )
    if plan and plan.exists() and review_files and not contains_any(read_text(plan), ["review integration", "review-integrated", "accepted review"]):
        findings.append(finding("medium", "plan-missing-review-integration", "Plan does not mention review integration.", plan))
    return emit_quality(
        "review-integration",
        findings,
        args,
        {
            "planning_dir": str(planning_dir),
            "review_files": [str(path) for path in review_files],
            "integration_notes": str(integration) if integration else None,
            "integration_word_count": word_count(integration_text),
        },
    )


def implement_progress(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    state_dir = planning_dir / "implementation"
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "forge-progress.json"
    event = {
        "timestamp": now_iso(),
        "section": args.section,
        "stage": args.stage,
        "command": args.command,
        "result": args.result,
        "notes": args.notes,
    }

    def default_state() -> dict[str, Any]:
        return {"events": [], "created_at": now_iso()}

    def append_event(state: dict[str, Any]) -> None:
        state.setdefault("events", []).append(event)

    try:
        state = update_json_locked(path, default_state, append_event)
    except TimeoutError as exc:
        return print_json({"success": False, "planning_dir": str(planning_dir), "state_path": str(path), "error": str(exc)}, 1)
    return print_json({"success": True, "planning_dir": str(planning_dir), "state_path": str(path), "event": event, "event_count": len(state["events"])})


def grade_for_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "D"


def forge_score_row(planning_dir: Path, *, name: str, depth: str, profile: str) -> dict[str, Any]:
    plan_findings, _ = plan_findings_for_score(planning_dir, depth)
    section_findings, _ = section_findings_for_score(planning_dir, depth)
    trace_findings, _ = traceability_analysis(planning_dir)
    evidence_findings = evidence_findings_for_score(planning_dir, 3)
    readiness_findings = readiness_findings_for_score(planning_dir, 8)
    components = {
        "plan_depth": quality_score(plan_findings, profile),
        "section_readiness": quality_score(section_findings, profile),
        "traceability": quality_score(trace_findings, profile),
        "evidence_quality": quality_score(evidence_findings, profile),
        "implementation_readiness": quality_score(readiness_findings, profile),
    }
    weights = FORGE_COMPONENT_WEIGHTS.get(profile, FORGE_COMPONENT_WEIGHTS["solo"])
    weight_total = sum(weights.get(key, 1.0) for key in components)
    score = round(sum(value * weights.get(key, 1.0) for key, value in components.items()) / weight_total)
    return {
        "name": name,
        "planning_dir": str(planning_dir),
        "depth_mode": depth,
        "forge_score": score,
        "grade": grade_for_score(score),
        "components": components,
        "findings": sum(len(items) for items in [plan_findings, section_findings, trace_findings, evidence_findings, readiness_findings]),
    }


def snapshot_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "planning_dir_name": Path(row["planning_dir"]).name,
        "forge_score": row["forge_score"],
        "grade": row["grade"],
        "components": row["components"],
    }


def snapshot_filename(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", name).strip("-") or "benchmark"
    return f"{slug}-forge-score.json"


def eval_suite_benchmarks(root: Path, default_depth: str) -> tuple[str, Path | None, Path | None, list[dict[str, Any]], list[dict[str, str]]]:
    if not root.exists():
        return "missing", None, None, [], [{"name": root.name or "examples", "error": "examples_dir does not exist"}]
    if not root.is_dir():
        return "missing", None, None, [], [{"name": root.name or "examples", "error": "examples_dir is not a directory"}]

    suite_path = root / "evals" / "suite.json"
    if not suite_path.exists():
        benchmarks = [
            {
                "name": plan_path.parent.name,
                "planning_dir": plan_path.parent,
                "depth": default_depth,
            }
            for plan_path in sorted(root.glob("**/codex-plan.md"))
            if "invalid" not in plan_path.relative_to(root).parts
        ]
        if not benchmarks:
            return "glob", None, None, [], [{"name": root.name or "examples", "error": "No benchmark planning fixtures found"}]
        return "glob", None, None, benchmarks, []

    try:
        suite = load_json(suite_path)
    except json.JSONDecodeError as exc:
        return "suite", suite_path, None, [], [{"name": "suite.json", "error": f"Invalid JSON: {exc}"}]

    snapshots_dir = suite_path.parent / suite.get("snapshots_dir", "golden")
    raw_benchmarks = suite.get("benchmarks")
    if not isinstance(raw_benchmarks, list):
        return "suite", suite_path, snapshots_dir, [], [{"name": "suite.json", "error": "benchmarks must be a list"}]

    benchmarks: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for index, raw in enumerate(raw_benchmarks, start=1):
        if not isinstance(raw, dict):
            errors.append({"name": f"benchmark-{index}", "error": "benchmark row must be an object"})
            continue
        name = str(raw.get("name") or f"benchmark-{index}")
        planning_value = raw.get("planning_dir")
        if not isinstance(planning_value, str) or not planning_value.strip():
            errors.append({"name": name, "error": "planning_dir is required"})
            continue
        planning_dir = (suite_path.parent / planning_value).resolve()
        if not planning_dir.exists() or not (planning_dir / "codex-plan.md").exists():
            errors.append({"name": name, "planning_dir": str(planning_dir), "error": "planning_dir does not contain codex-plan.md"})
            continue
        benchmarks.append(
            {
                "name": name,
                "planning_dir": planning_dir,
                "depth": str(raw.get("depth") or default_depth),
            }
        )
    if not benchmarks and not errors:
        errors.append({"name": "suite.json", "error": "benchmarks list is empty"})
    return "suite", suite_path, snapshots_dir, benchmarks, errors


def evaluate_snapshots(rows: list[dict[str, Any]], snapshots_dir: Path | None, *, check: bool, update: bool) -> tuple[dict[str, Any], bool]:
    summary: dict[str, Any] = {
        "checked": [],
        "matched": [],
        "missing": [],
        "drifted": [],
        "updated": [],
    }
    if not check and not update:
        return summary, True
    if snapshots_dir is None:
        return summary, True
    if update:
        snapshots_dir.mkdir(parents=True, exist_ok=True)
    ok = True
    for row in rows:
        name = str(row["name"])
        snapshot = snapshots_dir / snapshot_filename(name)
        expected = snapshot_payload(row)
        if update:
            snapshot.write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            summary["updated"].append(name)
            continue
        summary["checked"].append(name)
        if not snapshot.exists():
            summary["missing"].append({"name": name, "snapshot": str(snapshot)})
            ok = False
            continue
        try:
            actual = load_json(snapshot)
        except json.JSONDecodeError as exc:
            summary["drifted"].append({"name": name, "snapshot": str(snapshot), "error": f"Invalid JSON: {exc}"})
            ok = False
            continue
        if actual != expected:
            summary["drifted"].append({"name": name, "snapshot": str(snapshot), "expected": expected, "actual": actual})
            ok = False
        else:
            summary["matched"].append(name)
    return summary, ok


def eval_suite(args: argparse.Namespace) -> int:
    root = resolve_path(args.examples_dir)
    discovery_mode, suite_path, snapshots_dir, benchmarks, errors = eval_suite_benchmarks(root, args.depth)
    if errors:
        return print_json(
            {
                "success": False,
                "examples_dir": str(root),
                "depth_mode": args.depth,
                "profile": args.profile,
                "discovery_mode": discovery_mode,
                "suite_path": str(suite_path) if suite_path else None,
                "suite_errors": errors,
                "rows": [],
            },
            1,
        )

    rows = [
        forge_score_row(item["planning_dir"], name=item["name"], depth=item["depth"], profile=args.profile)
        for item in benchmarks
    ]
    snapshot_summary, snapshots_ok = evaluate_snapshots(
        rows,
        snapshots_dir,
        check=getattr(args, "check_snapshots", False),
        update=getattr(args, "update_snapshots", False),
    )
    payload = {
        "success": snapshots_ok,
        "examples_dir": str(root),
        "depth_mode": args.depth,
        "profile": args.profile,
        "discovery_mode": discovery_mode,
        "suite_path": str(suite_path) if suite_path else None,
        "snapshots_dir": str(snapshots_dir) if snapshots_dir else None,
        "snapshot_summary": snapshot_summary,
        "rows": rows,
    }
    if args.output:
        output = resolve_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["output"] = str(output)
    return print_json(payload, 0 if snapshots_ok else 1)


def markdown_tables(text: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
                continue
            current.append(cells)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def table_has_columns(tables: list[list[list[str]]], required: list[str]) -> bool:
    required_lower = [item.lower() for item in required]
    for table in tables:
        if not table:
            continue
        header = [cell.lower() for cell in table[0]]
        if all(item in header for item in required_lower):
            return True
    return False


def lint_artifact_schema(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    findings: list[Finding] = []
    artifacts = planning_artifacts(planning_dir)
    checks = [
        ("decisions", ["ID", "Date", "Decision", "Alternatives", "Rationale", "Impact"]),
        ("risks", ["ID", "Risk", "Severity", "Likelihood", "Mitigation", "Section", "Verification"]),
        ("traceability", ["Requirement", "Plan Coverage", "Section Coverage", "Test Coverage", "Status"]),
    ]
    for name, required in checks:
        path = artifacts[name]
        if not path or not path.exists():
            findings.append(finding("medium", f"missing-{name}", f"{name} artifact is missing.", path or planning_dir / f"{name}.md"))
            continue
        text = read_text(path)
        tables = markdown_tables(text)
        if not table_has_columns(tables, required):
            findings.append(
                finding(
                    "medium",
                    f"invalid-{name}-table",
                    f"{path.name} does not contain the required columns: {', '.join(required)}.",
                    path,
                    "Use the Forge governance table schema so automated checks can reason over the artifact.",
                )
            )
    sections_state = check_section_progress(planning_dir)
    if sections_state["state"] == "invalid_index":
        findings.append(finding("critical", "invalid-section-index", "sections/index.md does not parse.", planning_dir / "sections" / "index.md"))
    return emit_quality(
        "artifact-schema",
        findings,
        args,
        {"planning_dir": str(planning_dir), "section_progress": sections_state},
    )


def lint_plan_artifacts(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    payload = plan_artifacts_payload(planning_dir, args)
    return emit_payload(payload, args)


def suggest_section_splits(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    progress = check_section_progress(planning_dir)
    if progress["state"] in {"invalid_index", "no_index"}:
        return print_json({"success": False, "section_progress": progress}, 1)
    deps = dependency_graph(planning_dir, progress)
    suggestions: list[dict[str, Any]] = []
    for section in progress["sections"]:
        path = planning_dir / "sections" / f"{section}.md"
        if not path.exists():
            continue
        metrics = section_metrics(section, path, deps)
        if metrics["file_count"] <= args.max_files and metrics["word_count"] <= args.max_words:
            continue
        groups: dict[str, list[str]] = {}
        for file in metrics["files"]:
            parts = Path(file).parts
            key = parts[1] if len(parts) > 2 and parts[0] in {"src", "app", "lib", "tests"} else parts[0]
            groups.setdefault(key, []).append(file)
        proposed = []
        base_number = int(section.split("-", 2)[1]) if len(section.split("-", 2)) >= 2 and section.split("-", 2)[1].isdigit() else 1
        for offset, (label, files) in enumerate(sorted(groups.items()), start=0):
            slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "part"
            proposed.append(
                {
                    "section": f"section-{base_number + offset:02d}-{slug}",
                    "files": files,
                    "reason": "Grouped by top-level implementation area.",
                }
            )
        suggestions.append(
            {
                "section": section,
                "word_count": metrics["word_count"],
                "file_count": metrics["file_count"],
                "recommendation": "Split before implementation.",
                "proposed_sections": proposed,
            }
        )
    return print_json({"success": True, "planning_dir": str(planning_dir), "suggestions": suggestions})


def implementation_drift(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    progress = check_section_progress(planning_dir)
    findings: list[Finding] = []
    if progress["state"] in {"invalid_index", "no_index"}:
        findings.append(finding("critical", "invalid-sections", "Drift detection requires valid sections.", planning_dir / "sections" / "index.md"))
        return emit_quality("implementation-drift", findings, args, {"section_progress": progress})
    if args.diff_file:
        diff_path = resolve_path(args.diff_file)
        changed = set(changed_files_from_diff(read_text(diff_path)))
    else:
        changed_list, error = git_changed_files(resolve_path(args.repo), args.staged)
        if error:
            return print_json({"success": False, "error": error}, 1)
        changed = set(changed_list)

    section_files = sorted((planning_dir / "sections").glob("section-*.md"))
    planned_files = set()
    planned_tests = set()
    for section_path in section_files:
        files = extract_file_paths(read_text(section_path))
        planned_files.update(files)
        planned_tests.update(file for file in files if contains_any(file, ["test", "spec"]))
    changed_tests = {file for file in changed if contains_any(file, ["test", "spec"])}
    out_of_scope = sorted(file for file in changed if file not in planned_files)
    missing_planned_tests = sorted(file for file in planned_tests if file not in changed_tests)
    for file in out_of_scope:
        findings.append(finding("high", "implementation-drift-file", f"Changed file was not planned: {file}", planning_dir))
    if planned_tests and not changed_tests:
        findings.append(finding("medium", "planned-tests-not-changed", "No changed test files match planned test ownership.", planning_dir))
    return emit_quality(
        "implementation-drift",
        findings,
        args,
        {
            "planning_dir": str(planning_dir),
            "planned_files": sorted(planned_files),
            "changed_files": sorted(changed),
            "out_of_scope": out_of_scope,
            "planned_tests": sorted(planned_tests),
            "changed_tests": sorted(changed_tests),
            "missing_planned_tests": missing_planned_tests,
        },
    )


def evidence_path_ignored(relative_path: Path) -> bool:
    parts = set(relative_path.parts)
    if parts.intersection(EVIDENCE_IGNORE_PARTS):
        return True
    if ".codex" in parts and "cache" in parts:
        return True
    if ".agents" in parts and "plugins" in parts and "cache" in parts:
        return True
    return False


def evidence_files(target_dir: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(target_dir):
        directory = Path(dirpath)
        relative_dir = directory.relative_to(target_dir)
        dirnames[:] = [
            name
            for name in dirnames
            if not evidence_path_ignored((relative_dir / name) if relative_dir.parts else Path(name))
        ]
        for filename in filenames:
            relative = (relative_dir / filename) if relative_dir.parts else Path(filename)
            if not evidence_path_ignored(relative):
                files.append(relative)
    return sorted(files, key=lambda item: item.as_posix())


def cap_paths(paths: list[str], limit: int = 80) -> tuple[list[str], int]:
    ordered = sorted(dict.fromkeys(paths))
    return ordered[:limit], max(0, len(ordered) - limit)


def markdown_path_list(paths: list[str]) -> str:
    return "\n".join(f"- `{path}`" for path in paths) if paths else "- None found"


def codebase_evidence(args: argparse.Namespace) -> int:
    target_dir = resolve_path(args.target_dir)
    planning_dir = resolve_path(args.planning_dir) if args.planning_dir else target_dir
    all_files = evidence_files(target_dir)
    interesting = [
        "package.json",
        "pyproject.toml",
        "go.mod",
        "Cargo.toml",
        "Gemfile",
        "requirements.txt",
        "pnpm-lock.yaml",
        "yarn.lock",
        "uv.lock",
    ]
    found_files = [path.as_posix() for path in all_files if path.name in interesting]
    test_files = [
        path.as_posix()
        for path in all_files
        if contains_any(path.name, ["test", "spec"])
        and path.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".rb"}
    ][: args.max_tests]
    source_files, source_truncated = cap_paths(
        [
            path.as_posix()
            for path in all_files
            if path.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".rb", ".sh"}
            and (path.parts[0] in {"scripts", "src", "lib", "app", "bin"} or path.name == "zagrosi_skills.py")
        ]
    )
    skill_files, skill_truncated = cap_paths(
        [path.as_posix() for path in all_files if len(path.parts) >= 3 and path.parts[0] == "skills" and path.name == "SKILL.md"]
    )
    plugin_metadata, plugin_truncated = cap_paths(
        [
            path.as_posix()
            for path in all_files
            if path.as_posix() in {".codex-plugin/plugin.json", ".agents/plugins/marketplace.json", "pyproject.toml"}
            or path.parts[:2] == (".codex-plugin", "skills")
        ]
    )
    ci_files, ci_truncated = cap_paths([path.as_posix() for path in all_files if len(path.parts) >= 3 and path.parts[:2] == (".github", "workflows")])
    example_files, example_truncated = cap_paths(
        [
            path.as_posix()
            for path in all_files
            if path.parts and path.parts[0] == "examples" and path.suffix in {".md", ".json", ".toml", ".yml", ".yaml"}
        ]
    )
    commands: list[str] = []
    package_json = target_dir / "package.json"
    if package_json.exists():
        try:
            package = load_json(package_json)
            scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
            commands.extend(f"npm run {name}" for name in sorted(scripts) if contains_any(name, ["test", "lint", "typecheck", "check"]))
        except json.JSONDecodeError:
            pass
    if (target_dir / "pyproject.toml").exists():
        commands.extend(["uv run pytest", "python -m pytest"])
    if (target_dir / "go.mod").exists():
        commands.append("go test ./...")
    if (target_dir / "Cargo.toml").exists():
        commands.append("cargo test")
    candidate_commands = sorted(set(commands))
    content = (
        "# Codebase Evidence\n\n"
        f"Target: `{target_dir}`\n\n"
        "## Current State\n\n"
        "Existing file tree evidence was verified from relative paths only; source contents were not copied.\n\n"
        "## Runtime And Package Files\n\n"
        + markdown_path_list(sorted(found_files))
        + "\n\n## Tests Discovered\n\n"
        + markdown_path_list(sorted(test_files))
        + "\n\n## Forge Source Files\n\n"
        + markdown_path_list(source_files)
        + "\n\n## Skills\n\n"
        + markdown_path_list(skill_files)
        + "\n\n## Plugin Metadata\n\n"
        + markdown_path_list(plugin_metadata)
        + "\n\n## CI Files\n\n"
        + markdown_path_list(ci_files)
        + "\n\n## Example And Eval Files\n\n"
        + markdown_path_list(example_files)
        + "\n\n## Candidate Commands\n\n"
        + ("\n".join(f"- `{command}`" for command in candidate_commands) or "- None inferred")
        + "\n\n## Assumptions / Open Questions\n\n"
        "- Assumption: generated evidence is bounded planning input, not a complete repository index.\n"
        "- Open question: confirm any omitted generated files before using evidence for release decisions.\n"
    )
    output = None
    if args.write:
        output = planning_dir / "codex-evidence.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    return print_json(
        {
            "success": True,
            "target_dir": str(target_dir),
            "planning_dir": str(planning_dir),
            "runtime_files": sorted(found_files),
            "test_files": sorted(test_files),
            "source_files": source_files,
            "skill_files": skill_files,
            "plugin_metadata": plugin_metadata,
            "ci_files": ci_files,
            "example_files": example_files,
            "truncated": {
                "source_files": source_truncated,
                "skill_files": skill_truncated,
                "plugin_metadata": plugin_truncated,
                "ci_files": ci_truncated,
                "example_files": example_truncated,
            },
            "candidate_commands": candidate_commands,
            "output": str(output) if output else None,
            "content": None if output else content,
        }
    )


def html_report(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    score_args = argparse.Namespace(
        planning_dir=str(planning_dir),
        depth=args.depth,
        profile=args.profile,
        strict=False,
        export=None,
        export_format="jsonl",
        min_files=3,
        max_files=8,
        write_history=False,
    )
    plan_findings, _ = plan_findings_for_score(planning_dir, args.depth)
    section_findings, section_extras = section_findings_for_score(planning_dir, args.depth)
    trace_findings, trace = traceability_analysis(planning_dir)
    all_findings = plan_findings + section_findings + trace_findings + evidence_findings_for_score(planning_dir, 3) + readiness_findings_for_score(planning_dir, 8)
    components = {
        "Plan": quality_score(plan_findings, args.profile),
        "Sections": quality_score(section_findings, args.profile),
        "Traceability": quality_score(trace_findings, args.profile),
        "Evidence": quality_score(evidence_findings_for_score(planning_dir, 3), args.profile),
        "Readiness": quality_score(readiness_findings_for_score(planning_dir, 8), args.profile),
    }
    score = round(sum(components.values()) / len(components))
    rows = "".join(f"<tr><th>{html.escape(name)}</th><td>{value}</td></tr>" for name, value in components.items())
    findings_html = "".join(
        f"<li><strong>{html.escape(item.severity)}</strong> {html.escape(item.code)}: {html.escape(item.message)}</li>"
        for item in all_findings
    ) or "<li>No findings.</li>"
    coverage_html = "".join(
        f"<tr><td>{html.escape(req)}</td><td>{html.escape(str(data['covered']))}</td><td>{html.escape(', '.join(data['sections']))}</td></tr>"
        for req, data in trace.get("coverage", {}).items()
    )
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Zagrosi Forge Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
    .score {{ font-size: 2rem; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>Zagrosi Forge Report</h1>
  <p>Planning directory: <code>{html.escape(str(planning_dir))}</code></p>
  <p class="score">Forge Score: {score}</p>
  <h2>Components</h2>
  <table>{rows}</table>
  <h2>Traceability</h2>
  <table><tr><th>Requirement</th><th>Covered</th><th>Sections</th></tr>{coverage_html}</table>
  <h2>Findings</h2>
  <ul>{findings_html}</ul>
</body>
</html>
"""
    output = resolve_path(args.output) if args.output else planning_dir / ".forge" / "report.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return print_json({"success": True, "planning_dir": str(planning_dir), "output": str(output), "forge_score": score})


def e2e_trial_record(args: argparse.Namespace) -> int:
    planning_dir = resolve_path(args.planning_dir)
    status_args = argparse.Namespace(path=str(planning_dir))
    progress = check_section_progress(planning_dir)
    score_findings = (
        plan_findings_for_score(planning_dir, args.depth)[0]
        + section_findings_for_score(planning_dir, args.depth)[0]
        + traceability_analysis(planning_dir)[0]
        + evidence_findings_for_score(planning_dir, 3)
        + readiness_findings_for_score(planning_dir, 8)
    )
    score = quality_score(score_findings, args.profile)
    record = {
        "timestamp": now_iso(),
        "trial_name": args.name,
        "planning_dir": str(planning_dir),
        "target_repo": args.target_repo,
        "depth_mode": args.depth,
        "profile": args.profile,
        "forge_score": score,
        "section_progress": progress.get("progress"),
        "notes": args.notes,
        "metrics": {
            "time_to_plan_minutes": args.time_to_plan_minutes,
            "implementation_success": args.implementation_success,
            "rework_notes": args.rework_notes,
        },
    }
    output_dir = resolve_path(args.output_dir) if args.output_dir else planning_dir / ".forge" / "trials"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{re.sub(r'[^a-zA-Z0-9_.-]+', '-', args.name).strip('-') or 'trial'}.json"
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return print_json({"success": True, "output": str(output), "record": record})


def release_check(args: argparse.Namespace) -> int:
    plugin_root = resolve_path(args.plugin_root)
    commands = [
        [sys.executable, "-m", "py_compile", str(plugin_root / "scripts" / "zagrosi_skills.py")],
        [sys.executable, "-m", "json.tool", str(plugin_root / ".codex-plugin" / "plugin.json")],
        [sys.executable, "-m", "json.tool", str(plugin_root / ".agents" / "plugins" / "marketplace.json")],
        [sys.executable, str(plugin_root / "scripts" / "zagrosi_skills.py"), "doctor", "--plugin-root", str(plugin_root), "--strict"],
        [
            sys.executable,
            str(plugin_root / "scripts" / "zagrosi_skills.py"),
            "install",
            "--plugin-root",
            str(plugin_root),
            "--config",
            str(plugin_root / ".release-check" / "config.toml"),
            "--dry-run",
        ],
    ]
    examples_dir = plugin_root / "examples"
    if examples_dir.exists():
        commands.extend(
            [
                [sys.executable, "-m", "json.tool", str(examples_dir / "evals" / "suite.json")],
                [sys.executable, str(plugin_root / "scripts" / "zagrosi_skills.py"), "lint-project-manifest", "--planning-dir", str(examples_dir / "saas"), "--strict"],
                [sys.executable, str(plugin_root / "scripts" / "zagrosi_skills.py"), "lint-project-manifest", "--planning-dir", str(examples_dir / "typescript-app"), "--strict"],
                [sys.executable, str(plugin_root / "scripts" / "zagrosi_skills.py"), "eval-suite", "--examples-dir", str(examples_dir), "--check-snapshots"],
            ]
        )
    if args.run_tests:
        commands.append(["uv", "run", "--with", "pytest", "python", "-m", "pytest"])
    results = []
    success = True
    for command in commands:
        result = subprocess.run(command, cwd=plugin_root, capture_output=True, text=True)
        results.append(
            {
                "command": " ".join(command),
                "returncode": result.returncode,
                "stdout_tail": result.stdout[-1000:],
                "stderr_tail": result.stderr[-1000:],
            }
        )
        if result.returncode != 0:
            success = False
    return print_json({"success": success, "plugin_root": str(plugin_root), "results": results}, 0 if success else 1)


def default_codex_config_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "config.toml"
    return Path.home() / ".codex" / "config.toml"


def toml_string(value: str) -> str:
    return json.dumps(value)


def toml_header_token(line: str) -> str | None:
    match = re.match(r"^\s*(\[\[?.*?\]\]?)\s*(?:#.*)?$", line)
    return match.group(1) if match else None


def find_toml_section(lines: list[str], header: str) -> tuple[int, int] | None:
    start: int | None = None
    for index, line in enumerate(lines):
        token = toml_header_token(line)
        if token is None:
            continue
        if token == header:
            start = index
            continue
        if start is not None:
            return start, index
    if start is None:
        return None
    return start, len(lines)


def upsert_toml_section(text: str, header: str, entries: dict[str, str]) -> tuple[str, list[str]]:
    lines = text.splitlines()
    changes: list[str] = []
    section = find_toml_section(lines, header)
    if section is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(header)
        for key, value in entries.items():
            lines.append(f"{key} = {value}")
        changes.append(f"added {header}")
        return "\n".join(lines).rstrip() + "\n", changes

    start, end = section
    for key, value in entries.items():
        replacement = f"{key} = {value}"
        key_re = re.compile(rf"^\s*{re.escape(key)}\s*=.*$")
        found = False
        for index in range(start + 1, end):
            if key_re.match(lines[index]):
                found = True
                if lines[index].strip() != replacement:
                    lines[index] = replacement
                    changes.append(f"updated {header}.{key}")
                break
        if not found:
            lines.insert(end, replacement)
            end += 1
            changes.append(f"added {header}.{key}")
    return "\n".join(lines).rstrip() + "\n", changes


PLUGIN_CACHE_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "planning",
}
PLUGIN_CACHE_IGNORE_FILES = {".DS_Store"}


def codex_home_for_config(config_path: Path, explicit_config: bool) -> Path:
    if explicit_config:
        return config_path.expanduser().resolve().parent
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser()
    return config_path.expanduser().resolve().parent


def package_manifest(plugin_root: Path) -> dict[str, Any]:
    manifest = load_json(plugin_root / ".codex-plugin" / "plugin.json")
    if not isinstance(manifest, dict):
        raise ValueError("plugin.json must contain a JSON object")
    return manifest


def plugin_cache_path(codex_home: Path, marketplace: str, plugin_name: str, version: str) -> Path:
    return codex_home / "plugins" / "cache" / marketplace / plugin_name / version


def should_skip_cache_path(path: Path) -> bool:
    return any(part in PLUGIN_CACHE_IGNORE_DIRS for part in path.parts) or path.name in PLUGIN_CACHE_IGNORE_FILES


def plugin_tree_fingerprint(root: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    if not root.exists():
        return ""
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if should_skip_cache_path(relative):
            continue
        digest.update(str(relative).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def copy_ignore(_: str, names: list[str]) -> set[str]:
    return {name for name in names if name in PLUGIN_CACHE_IGNORE_DIRS or name in PLUGIN_CACHE_IGNORE_FILES}


def materialize_plugin_cache(plugin_root: Path, cache_path: Path, dry_run: bool) -> dict[str, Any]:
    source_fingerprint = plugin_tree_fingerprint(plugin_root)
    cached_fingerprint = plugin_tree_fingerprint(cache_path)
    cache_changed = source_fingerprint != cached_fingerprint
    payload: dict[str, Any] = {
        "path": str(cache_path),
        "changed": cache_changed,
        "source_fingerprint": source_fingerprint,
        "cached_fingerprint": cached_fingerprint or None,
    }
    if dry_run:
        payload["dry_run"] = True
        return payload
    if not cache_changed:
        payload["dry_run"] = False
        return payload

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    temporary = cache_path.parent / f".{cache_path.name}.tmp-{stamp}"
    if temporary.exists():
        shutil.rmtree(temporary)
    shutil.copytree(plugin_root, temporary, ignore=copy_ignore)
    if cache_path.exists():
        shutil.rmtree(cache_path)
    temporary.rename(cache_path)
    payload["dry_run"] = False
    return payload


def expected_codex_config(existing: str, plugin_root: Path) -> tuple[str, list[str]]:
    updated, marketplace_changes = upsert_toml_section(
        existing,
        "[marketplaces.zagrosi]",
        {
            "source_type": toml_string("local"),
            "source": toml_string(str(plugin_root)),
        },
    )
    updated, plugin_changes = upsert_toml_section(
        updated,
        '[plugins."zagrosi-forge@zagrosi"]',
        {"enabled": "true"},
    )
    return updated, marketplace_changes + plugin_changes


def update_check(args: argparse.Namespace) -> int:
    plugin_root = resolve_path(args.plugin_root)
    config_path = resolve_path(args.config) if args.config else default_codex_config_path()
    codex_home = codex_home_for_config(config_path, bool(args.config))
    try:
        manifest = package_manifest(plugin_root)
    except (json.JSONDecodeError, ValueError) as exc:
        return print_json(
            {
                "success": False,
                "operation": "update-check",
                "plugin_root": str(plugin_root),
                "config_path": str(config_path),
                "error": f"Could not read plugin manifest: {exc}",
            },
            1,
        )

    plugin_name = str(manifest.get("name") or "zagrosi-forge")
    plugin_version = str(manifest.get("version") or "0.0.0")
    cache_path = plugin_cache_path(codex_home, "zagrosi", plugin_name, plugin_version)
    source_fingerprint = plugin_tree_fingerprint(plugin_root)
    cached_fingerprint = plugin_tree_fingerprint(cache_path)
    cache_exists = cache_path.exists()
    cache_current = cache_exists and source_fingerprint == cached_fingerprint

    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    expected_config, config_changes = expected_codex_config(existing, plugin_root)
    config_current = expected_config == existing
    restart_required = not cache_current or not config_current
    next_steps: list[str] = []
    if restart_required:
        next_steps.append("Run python3 scripts/zagrosi_skills.py self-update --plugin-root . to refresh Codex config and plugin cache.")
        next_steps.append("Restart Codex after self-update reports changed cache or config.")
    else:
        next_steps.append("Codex config and Zagrosi Forge plugin cache are already current.")
    next_steps.append("This check is local-only; update the git checkout separately when you want newer remote source.")

    payload = {
        "success": True,
        "operation": "update-check",
        "plugin_root": str(plugin_root),
        "config_path": str(config_path),
        "codex_home": str(codex_home),
        "plugin": "zagrosi-forge@zagrosi",
        "plugin_name": plugin_name,
        "plugin_version": plugin_version,
        "network_policy": "local-only",
        "remote_checked": False,
        "cache": {
            "path": str(cache_path),
            "exists": cache_exists,
            "current": cache_current,
            "changed": not cache_current,
            "source_fingerprint": source_fingerprint,
            "cached_fingerprint": cached_fingerprint or None,
        },
        "config": {
            "current": config_current,
            "changed": not config_current,
            "changes": config_changes,
        },
        "restart_required": restart_required,
        "next_steps": next_steps,
    }
    return print_json(payload)


def verify_codex_install(codex_home: Path, require_codex: bool) -> dict[str, Any]:
    codex = shutil.which("codex")
    if not codex:
        payload = {
            "status": "failed" if require_codex else "skipped",
            "success": not require_codex,
            "reason": "codex executable was not found on PATH",
            "required_skills": [
                "zagrosi-forge:zagrosi-project",
                "zagrosi-forge:zagrosi-plan",
                "zagrosi-forge:zagrosi-implement",
            ],
        }
        return payload

    command = [codex, "debug", "prompt-input", "Use $zagrosi-forge:zagrosi-project"]
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    required = [
        "zagrosi-forge:zagrosi-project",
        "zagrosi-forge:zagrosi-plan",
        "zagrosi-forge:zagrosi-implement",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=45)
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "failed",
            "success": False,
            "command": " ".join(command),
            "codex_home": str(codex_home),
            "reason": f"codex debug prompt-input timed out after {exc.timeout} seconds",
            "required_skills": required,
        }

    output = f"{result.stdout}\n{result.stderr}"
    missing = [skill for skill in required if skill not in output]
    success = result.returncode == 0 and not missing
    return {
        "status": "passed" if success else "failed",
        "success": success,
        "command": " ".join(command),
        "codex_home": str(codex_home),
        "returncode": result.returncode,
        "missing": missing,
        "required_skills": required,
        "stdout_tail": result.stdout[-1000:],
        "stderr_tail": result.stderr[-1000:],
    }


def install_codex(args: argparse.Namespace) -> int:
    plugin_root = resolve_path(args.plugin_root)
    config_path = resolve_path(args.config) if args.config else default_codex_config_path()
    codex_home = codex_home_for_config(config_path, bool(args.config))
    plugin_id = "zagrosi-forge@zagrosi"
    operation = "self-update" if getattr(args, "command", "") == "self-update" else "install-codex"
    if args.verify_codex and args.no_verify_codex:
        return print_json(
            {
                "success": False,
                "operation": operation,
                "plugin_root": str(plugin_root),
                "config_path": str(config_path),
                "plugin": plugin_id,
                "error": "Use either --verify-codex or --no-verify-codex, not both.",
            },
            2,
        )
    required = [
        plugin_root / ".codex-plugin" / "plugin.json",
        plugin_root / ".agents" / "plugins" / "marketplace.json",
        plugin_root / "skills" / "zagrosi-project" / "SKILL.md",
        plugin_root / "skills" / "zagrosi-plan" / "SKILL.md",
        plugin_root / "skills" / "zagrosi-implement" / "SKILL.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return print_json(
            {
                "success": False,
                "operation": operation,
                "plugin_root": str(plugin_root),
                "config_path": str(config_path),
                "plugin": plugin_id,
                "missing": missing,
                "error": "Plugin root is missing required package files.",
            },
            1,
        )

    doctor_result = subprocess.run(
        [sys.executable, str(plugin_root / "scripts" / "zagrosi_skills.py"), "doctor", "--plugin-root", str(plugin_root), "--strict"],
        cwd=plugin_root,
        capture_output=True,
        text=True,
    )
    try:
        doctor_payload: Any = json.loads(doctor_result.stdout) if doctor_result.stdout.strip() else {}
    except json.JSONDecodeError:
        doctor_payload = {"stdout": doctor_result.stdout[-1000:], "stderr": doctor_result.stderr[-1000:]}
    if doctor_result.returncode != 0:
        return print_json(
            {
                "success": False,
                "operation": operation,
                "plugin_root": str(plugin_root),
                "config_path": str(config_path),
                "plugin": plugin_id,
                "doctor": doctor_payload,
                "error": "Package doctor failed; fix the plugin before installing.",
            },
            1,
        )

    try:
        manifest = package_manifest(plugin_root)
    except (json.JSONDecodeError, ValueError) as exc:
        return print_json(
            {
                "success": False,
                "operation": operation,
                "plugin_root": str(plugin_root),
                "config_path": str(config_path),
                "plugin": plugin_id,
                "error": f"Could not read plugin manifest: {exc}",
            },
            1,
        )
    plugin_name = str(manifest.get("name") or "zagrosi-forge")
    plugin_version = str(manifest.get("version") or "0.0.0")
    cache_path = plugin_cache_path(codex_home, "zagrosi", plugin_name, plugin_version)
    cache = materialize_plugin_cache(plugin_root, cache_path, args.dry_run)

    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    updated, changes = expected_codex_config(existing, plugin_root)
    changed = updated != existing or bool(cache.get("changed"))
    backup_path: Path | None = None

    config_changed = updated != existing
    if config_changed and not args.dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if config_path.exists() and not args.no_backup:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            backup_path = config_path.with_name(f"{config_path.name}.bak-{stamp}")
            backup_path.write_text(existing, encoding="utf-8")
        config_path.write_text(updated, encoding="utf-8")

    verification: dict[str, Any]
    if args.dry_run or args.no_verify_codex:
        verification = {
            "status": "skipped",
            "success": True,
            "reason": "dry run" if args.dry_run else "disabled by --no-verify-codex",
            "required_skills": [
                "zagrosi-forge:zagrosi-project",
                "zagrosi-forge:zagrosi-plan",
                "zagrosi-forge:zagrosi-implement",
            ],
        }
    else:
        verification = verify_codex_install(codex_home, args.verify_codex)
        if not verification.get("success"):
            return print_json(
                {
                    "success": False,
                    "operation": operation,
                    "changed": changed,
                    "dry_run": args.dry_run,
                    "config_path": str(config_path),
                    "codex_home": str(codex_home),
                    "plugin_root": str(plugin_root),
                    "plugin": plugin_id,
                    "marketplace": "zagrosi",
                    "cache": cache,
                    "backup_path": str(backup_path) if backup_path else None,
                    "changes": changes,
                    "verification": verification,
                    "error": "Codex did not report the Zagrosi Forge skills after install.",
                },
                1,
            )

    next_steps = []
    if args.dry_run:
        next_steps.append("Run the same command without --dry-run to update Codex config.")
    elif changed:
        next_steps.append("Restart Codex so the plugin cache and marketplace are reloaded.")
    else:
        next_steps.append("Codex config and Zagrosi Forge plugin cache are already current.")
    next_steps.append(
        "Use $zagrosi-forge:zagrosi-project, $zagrosi-forge:zagrosi-plan, or $zagrosi-forge:zagrosi-implement in Codex."
    )

    payload = {
        "success": True,
        "operation": operation,
        "changed": changed,
        "config_changed": config_changed,
        "dry_run": args.dry_run,
        "config_path": str(config_path),
        "codex_home": str(codex_home),
        "plugin_root": str(plugin_root),
        "plugin": plugin_id,
        "plugin_version": plugin_version,
        "marketplace": "zagrosi",
        "cache": cache,
        "backup_path": str(backup_path) if backup_path else None,
        "changes": changes,
        "verification": verification,
        "restart_required": bool(changed and not args.dry_run),
        "next_steps": next_steps,
    }
    if args.dry_run:
        payload["config_preview"] = updated
    return print_json(payload)


def add_quality_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", choices=sorted(QUALITY_PROFILES), default="solo")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--export")
    parser.add_argument("--export-format", choices=["jsonl", "sarif"], default="jsonl")


def add_flight_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--flight",
        dest="flight_mode",
        choices=["auto", "strict", "advisory", "off"],
        default="auto",
        help="Run phase-aware flight gates automatically.",
    )


def command_help(name: str) -> str | None:
    return COMMAND_SUMMARIES.get(name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Helpers for Zagrosi Forge Codex skills")
    parser.add_argument("--pretty", action="store_true", help="Print a human-readable report instead of JSON.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("project-setup", aliases=["project", "zagrosi-project-setup", "deep-project-setup"], help=command_help("project-setup"))
    p.add_argument("--file", help="Markdown requirements file. Optional when --brief is provided.")
    p.add_argument("--brief", help="Chat-supplied project brief to materialize into requirements.md.")
    p.add_argument("--planning-dir", help="Directory for generated project artifacts when using --brief.")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--plugin-root")
    add_flight_args(p)
    p.set_defaults(func=deep_project_setup)

    p = sub.add_parser("project-create-dirs", aliases=["zagrosi-project-create-dirs", "deep-project-create-dirs"], help=command_help("project-create-dirs"))
    p.add_argument("--planning-dir", required=True)
    add_flight_args(p)
    p.set_defaults(func=deep_project_create_dirs)

    p = sub.add_parser("plan-setup", aliases=["plan", "zagrosi-plan-setup", "deep-plan-setup"], help=command_help("plan-setup"))
    p.add_argument("--file", required=True)
    p.add_argument("--plugin-root")
    p.add_argument("--target-dir")
    p.add_argument("--write-evidence", action="store_true")
    p.add_argument("--review-mode", choices=["codex_review", "external_llm", "skip"], default="codex_review")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    add_flight_args(p)
    p.set_defaults(func=deep_plan_setup)

    p = sub.add_parser("plan-check-sections", aliases=["zagrosi-plan-check-sections", "deep-plan-check-sections"], help=command_help("plan-check-sections"))
    p.add_argument("--planning-dir", required=True)
    p.set_defaults(func=deep_plan_check_sections)

    p = sub.add_parser(
        "plan-generate-section-prompts",
        aliases=["zagrosi-plan-generate-section-prompts", "deep-plan-generate-section-prompts"],
        help=command_help("plan-generate-section-prompts"),
    )
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--all", action="store_true")
    p.set_defaults(func=deep_plan_generate_section_prompts)

    p = sub.add_parser("implement-setup", aliases=["implement", "zagrosi-implement-setup", "deep-implement-setup"], help=command_help("implement-setup"))
    p.add_argument("--sections-dir", required=True)
    p.add_argument("--target-dir")
    p.add_argument("--plugin-root")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--profile", choices=sorted(QUALITY_PROFILES), default="solo")
    add_flight_args(p)
    p.set_defaults(func=deep_implement_setup)

    p = sub.add_parser(
        "implement-record-section",
        aliases=["zagrosi-implement-record-section", "deep-implement-record-section"],
        help=command_help("implement-record-section"),
    )
    p.add_argument("--sections-dir", required=True)
    p.add_argument("--section", required=True)
    p.add_argument("--commit")
    p.add_argument("--notes")
    p.add_argument("--file", action="append", dest="files_changed", default=[])
    p.add_argument("--test-file", action="append", dest="test_files", default=[])
    p.add_argument("--review-artifact", action="append", dest="review_artifacts", default=[])
    p.add_argument("--verification", action="append", default=[])
    p.add_argument("--commit-status")
    p.add_argument("--target-dir")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--profile", choices=sorted(QUALITY_PROFILES), default="solo")
    p.add_argument("--write-report", action="store_true")
    add_flight_args(p)
    p.set_defaults(func=deep_implement_record_section)

    p = sub.add_parser("preflight", help=command_help("preflight"))
    p.add_argument("--phase", choices=["project", "plan", "implement", "release"], required=True)
    p.add_argument("--file")
    p.add_argument("--brief")
    p.add_argument("--planning-dir")
    p.add_argument("--sections-dir")
    p.add_argument("--target-dir")
    p.add_argument("--plugin-root")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--write-evidence", action="store_true")
    p.add_argument("--run-tests", action="store_true")
    add_quality_args(p)
    add_flight_args(p)
    p.set_defaults(func=preflight)

    p = sub.add_parser("postflight", help=command_help("postflight"))
    p.add_argument("--phase", choices=["project", "plan", "implement", "release"], required=True)
    p.add_argument("--file")
    p.add_argument("--planning-dir")
    p.add_argument("--sections-dir")
    p.add_argument("--target-dir")
    p.add_argument("--plugin-root")
    p.add_argument("--section-file")
    p.add_argument("--diff-file")
    p.add_argument("--staged", action="store_true")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--write-report", action="store_true")
    p.add_argument("--run-tests", action="store_true")
    add_quality_args(p)
    add_flight_args(p)
    p.set_defaults(func=postflight)

    p = sub.add_parser("lint-project-manifest")
    p.add_argument("--planning-dir", required=True)
    add_quality_args(p)
    p.set_defaults(func=lint_project_manifest)

    p = sub.add_parser("lint-plan", help=command_help("lint-plan"))
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--depth", choices=sorted(DEPTH_MODES))
    add_quality_args(p)
    p.set_defaults(func=lint_plan)

    p = sub.add_parser("lint-sections", help=command_help("lint-sections"))
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--depth", choices=sorted(DEPTH_MODES))
    add_quality_args(p)
    p.set_defaults(func=lint_sections)

    p = sub.add_parser("lint-implementation-state")
    p.add_argument("--sections-dir", required=True)
    add_quality_args(p)
    p.set_defaults(func=lint_implementation_state)

    p = sub.add_parser("status", help=command_help("status"))
    p.add_argument("--path", required=True)
    p.set_defaults(func=status)

    p = sub.add_parser("commands", aliases=["help-commands"], help=command_help("commands"))
    p.add_argument("--phase", choices=sorted({item["phase"] for item in COMMAND_CATALOG}))
    p.set_defaults(func=command_catalog)

    p = sub.add_parser("workflow-options", help=command_help("workflow-options"))
    p.add_argument("--brief")
    p.add_argument("--spec-file")
    p.add_argument("--planning-dir")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES))
    p.add_argument("--profile", choices=sorted(QUALITY_PROFILES), default="solo")
    p.set_defaults(func=workflow_options)

    p = sub.add_parser("capability-inventory", help=command_help("capability-inventory"))
    p.add_argument("--plugin-root")
    p.add_argument("--config")
    p.add_argument("--planning-dir")
    p.set_defaults(func=capability_inventory)

    p = sub.add_parser("review-capabilities", help=command_help("review-capabilities"))
    p.add_argument("--planning-dir")
    p.add_argument("--config")
    p.set_defaults(func=review_capabilities)

    p = sub.add_parser("planning-consistency", help=command_help("planning-consistency"))
    p.add_argument("--planning-dir", required=True)
    add_quality_args(p)
    p.set_defaults(func=planning_consistency)

    p = sub.add_parser("traceability", help=command_help("traceability"))
    p.add_argument("--planning-dir", required=True)
    add_quality_args(p)
    p.set_defaults(func=traceability)

    p = sub.add_parser("doctor", help=command_help("doctor"))
    p.add_argument("--plugin-root")
    add_quality_args(p)
    p.set_defaults(func=doctor)

    p = sub.add_parser("lint-interview")
    p.add_argument("--phase", choices=["project", "plan"], required=True)
    p.add_argument("--planning-dir", required=True)
    add_quality_args(p)
    p.set_defaults(func=lint_interview)

    p = sub.add_parser("update-check", help=command_help("update-check"))
    p.add_argument("--plugin-root", default=".")
    p.add_argument("--config")
    p.set_defaults(func=update_check)

    p = sub.add_parser("install-codex", aliases=["install", "install-plugin"], help=command_help("install-codex"))
    p.add_argument("--plugin-root", default=".")
    p.add_argument("--config")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-backup", action="store_true")
    p.add_argument(
        "--verify-codex",
        action="store_true",
        help="Fail if the codex CLI is unavailable or the installed skills are not visible.",
    )
    p.add_argument("--no-verify-codex", action="store_true", help="Skip codex debug prompt-input verification.")
    p.set_defaults(func=install_codex)

    p = sub.add_parser("self-update", help=command_help("self-update"))
    p.add_argument("--plugin-root", default=".")
    p.add_argument("--config")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-backup", action="store_true")
    p.add_argument(
        "--verify-codex",
        action="store_true",
        help="Fail if the codex CLI is unavailable or the installed skills are not visible.",
    )
    p.add_argument("--no-verify-codex", action="store_true", help="Skip codex debug prompt-input verification.")
    p.set_defaults(func=install_codex)

    p = sub.add_parser("section-estimates")
    p.add_argument("--planning-dir", required=True)
    p.set_defaults(func=section_estimates)

    p = sub.add_parser("next-section")
    p.add_argument("--planning-dir", required=True)
    p.set_defaults(func=next_section)

    p = sub.add_parser("parallel-plan")
    p.add_argument("--planning-dir", required=True)
    p.set_defaults(func=parallel_plan)

    p = sub.add_parser("patch-scope")
    p.add_argument("--section-file", required=True)
    p.add_argument("--repo", default=".")
    p.add_argument("--diff-file")
    p.add_argument("--staged", action="store_true")
    add_quality_args(p)
    p.set_defaults(func=patch_scope)

    p = sub.add_parser("commit-message")
    p.add_argument("--section-file", required=True)
    p.add_argument("--style", choices=["conventional", "simple"], default="conventional")
    p.set_defaults(func=commit_message)

    p = sub.add_parser("extract-requirements")
    p.add_argument("--file", required=True)
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=extract_requirements)

    p = sub.add_parser("trace-export")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--format", choices=["json", "csv", "md"], default="json")
    p.add_argument("--output")
    add_quality_args(p)
    p.set_defaults(func=trace_export)

    p = sub.add_parser("agent-prompts")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--type", choices=["all", *sorted(PROMPT_TYPES)], default="all")
    p.set_defaults(func=agent_prompts)

    p = sub.add_parser("context-budget")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--max-words", type=int, default=12000)
    add_quality_args(p)
    p.set_defaults(func=context_budget)

    p = sub.add_parser("forge-score", help=command_help("forge-score"))
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--min-files", type=int, default=3)
    p.add_argument("--max-files", type=int, default=8)
    p.add_argument("--write-history", action="store_true")
    add_quality_args(p)
    p.set_defaults(func=forge_score)

    p = sub.add_parser("lint-evidence", help=command_help("lint-evidence"))
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--min-files", type=int, default=3)
    add_quality_args(p)
    p.set_defaults(func=lint_evidence)

    p = sub.add_parser("lint-implementation-readiness", help=command_help("lint-implementation-readiness"))
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--max-files", type=int, default=8)
    add_quality_args(p)
    p.set_defaults(func=lint_implementation_readiness)

    p = sub.add_parser("lint-review-integration")
    p.add_argument("--planning-dir", required=True)
    add_quality_args(p)
    p.set_defaults(func=lint_review_integration)

    p = sub.add_parser("lint-artifact-schema")
    p.add_argument("--planning-dir", required=True)
    add_quality_args(p)
    p.set_defaults(func=lint_artifact_schema)

    p = sub.add_parser("lint-plan-artifacts")
    p.add_argument("--planning-dir", required=True)
    add_quality_args(p)
    p.set_defaults(func=lint_plan_artifacts)

    p = sub.add_parser("suggest-section-splits")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--max-files", type=int, default=8)
    p.add_argument("--max-words", type=int, default=3500)
    p.set_defaults(func=suggest_section_splits)

    p = sub.add_parser("implementation-drift")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--repo", default=".")
    p.add_argument("--diff-file")
    p.add_argument("--staged", action="store_true")
    add_quality_args(p)
    p.set_defaults(func=implementation_drift)

    p = sub.add_parser("codebase-evidence", help=command_help("codebase-evidence"))
    p.add_argument("--target-dir", default=".")
    p.add_argument("--planning-dir")
    p.add_argument("--max-tests", type=int, default=80)
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=codebase_evidence)

    p = sub.add_parser("assumption-ledger")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=assumption_ledger)

    p = sub.add_parser("implementation-packet")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--section", required=True)
    p.add_argument("--output-dir")
    p.set_defaults(func=implementation_packet)

    p = sub.add_parser("context-brief")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--section")
    p.add_argument("--lines-per-artifact", type=int, default=80)
    p.add_argument("--output")
    p.set_defaults(func=context_brief)

    p = sub.add_parser("tdd-skeletons")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--framework", choices=["pytest", "vitest", "go", "rust"], default="pytest")
    p.add_argument("--output-dir")
    p.set_defaults(func=tdd_skeletons)

    p = sub.add_parser("plan-diff")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.set_defaults(func=plan_diff)

    p = sub.add_parser("implement-progress")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--section", required=True)
    p.add_argument("--stage", choices=["started", "red", "green", "refactor", "review", "verified", "recorded"], required=True)
    p.add_argument("--command")
    p.add_argument("--result")
    p.add_argument("--notes")
    p.set_defaults(func=implement_progress)

    p = sub.add_parser("report")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--profile", choices=sorted(QUALITY_PROFILES), default="solo")
    p.add_argument("--output")
    p.set_defaults(func=html_report)

    p = sub.add_parser("e2e-trial-record")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--target-repo")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--profile", choices=sorted(QUALITY_PROFILES), default="solo")
    p.add_argument("--time-to-plan-minutes", type=float)
    p.add_argument("--implementation-success", choices=["unknown", "yes", "no", "partial"], default="unknown")
    p.add_argument("--rework-notes")
    p.add_argument("--notes")
    p.add_argument("--output-dir")
    p.set_defaults(func=e2e_trial_record)

    p = sub.add_parser("eval-suite", help=command_help("eval-suite"))
    p.add_argument("--examples-dir", default="examples")
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--profile", choices=sorted(QUALITY_PROFILES), default="solo")
    p.add_argument("--output")
    p.add_argument("--check-snapshots", action="store_true")
    p.add_argument("--update-snapshots", action="store_true")
    p.set_defaults(func=eval_suite)

    p = sub.add_parser("release-check", help=command_help("release-check"))
    p.add_argument("--plugin-root", default=".")
    p.add_argument("--run-tests", action="store_true")
    p.set_defaults(func=release_check)

    p = sub.add_parser("write-governance-stubs")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.set_defaults(func=write_governance_stubs)

    p = sub.add_parser("review-board-prompts")
    p.add_argument("--planning-dir", required=True)
    p.set_defaults(func=review_board_prompts)

    p = sub.add_parser("migrate")
    p.add_argument("--planning-dir", required=True)
    p.add_argument("--depth", choices=sorted(DEPTH_MODES), default="standard")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=migrate)

    return parser


def main(argv: list[str] | None = None) -> int:
    global PRETTY_OUTPUT
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if "--pretty" in raw_args:
        PRETTY_OUTPUT = True
        raw_args = [item for item in raw_args if item != "--pretty"]
    parser = build_parser()
    args = parser.parse_args(raw_args)
    if getattr(args, "pretty", False):
        PRETTY_OUTPUT = True
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
