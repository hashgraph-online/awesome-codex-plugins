#!/usr/bin/env python3
"""Codex Quota Optimizer local CLI.

Zero-network, zero-dependency helper for optional task-level budgeting and auditing.
It never intercepts Codex execution and never requires an additional model call.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "0.2.2"

HIGH_RISK_TERMS = {
    "security", "auth", "authentication", "authorization", "permission",
    "payment", "billing", "migration", "migrate", "database schema",
    "encryption", "secret", "credential", "production", "data loss",
    "rollback", "compliance",
    "安全", "鉴权", "认证", "权限", "支付", "账单", "迁移", "数据库",
    "加密", "密钥", "凭证", "生产", "数据丢失", "回滚", "合规",
}
COMPLEX_TERMS = {
    "architecture", "redesign", "cross-cutting", "distributed", "concurrency",
    "race condition", "performance", "refactor", "multi-service", "multi system",
    "multi-system", "end-to-end", "e2e", "framework", "protocol",
    "架构", "重设计", "跨模块", "分布式", "并发", "竞态", "性能", "重构",
    "多服务", "多系统", "端到端", "框架", "协议",
}
DEBUG_TERMS = {
    "debug", "flaky", "intermittent", "root cause", "reproduce", "regression",
    "memory leak", "deadlock",
    "调试", "偶发", "根因", "复现", "回归", "内存泄漏", "死锁",
}
MECHANICAL_TERMS = {
    "rename", "typo", "copy change", "text change", "comment", "formatting",
    "format only", "documentation", "docs only", "readme",
    "重命名", "错别字", "文案修改", "文本修改", "注释", "格式化", "文档",
}

SIZE_ORDER = ("XS", "S", "M", "L", "XL")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cqo_home() -> Path:
    return Path(os.environ.get("CQO_HOME", "~/.cqo")).expanduser()


def current_path() -> Path:
    return cqo_home() / "current.json"


def history_path() -> Path:
    return cqo_home() / "history.jsonl"


def ensure_home() -> None:
    cqo_home().mkdir(parents=True, exist_ok=True)


def contains_any(text: str, terms: set[str]) -> bool:
    low = text.lower()
    return any(term in low for term in terms)


def git_info(cwd: str | None = None) -> dict[str, Any]:
    """Return a tiny local git snapshot. Fail closed and never block for long."""
    result: dict[str, Any] = {
        "root": None,
        "branch": None,
        "changed_files": [],
    }

    def run(args: list[str]) -> str | None:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        return completed.stdout.strip()

    root = run(["rev-parse", "--show-toplevel"])
    if not root:
        return result

    result["root"] = root
    result["branch"] = run(["branch", "--show-current"]) or None
    changed = run(["status", "--porcelain=v1", "-uno"])
    if changed:
        paths: list[str] = []
        for line in changed.splitlines():
            payload = line[3:] if len(line) > 3 else ""
            if " -> " in payload:
                payload = payload.split(" -> ", 1)[1]
            if payload:
                paths.append(payload.strip('"'))
        result["changed_files"] = sorted(set(paths))
    return result


def classify_task(task: str, repo: dict[str, Any] | None = None) -> dict[str, str]:
    """Classify locally with simple heuristics; no model call."""
    text = (task or "").strip()
    words = len(text.split())
    changed_count = len((repo or {}).get("changed_files") or [])

    score = 1 if text else 0
    if changed_count:
        if changed_count == 1:
            score += 1
        elif changed_count <= 3:
            score += 2
        elif changed_count <= 7:
            score += 4
        elif changed_count <= 12:
            score += 6
        else:
            score += 8

    high_risk = contains_any(text, HIGH_RISK_TERMS)
    complex_task = contains_any(text, COMPLEX_TERMS)
    debug_task = contains_any(text, DEBUG_TERMS)
    mechanical = contains_any(text, MECHANICAL_TERMS)

    if high_risk:
        score += 5
    if complex_task:
        score += 3
    if debug_task:
        score += 2
    if words > 80:
        score += 1
    if words > 220:
        score += 2
    if mechanical and not (high_risk or complex_task or debug_task):
        score -= 1

    if score <= 0:
        size = "XS"
    elif score <= 2:
        size = "S"
    elif score <= 5:
        size = "M"
    elif score <= 8:
        size = "L"
    else:
        size = "XL"

    if high_risk:
        risk = "high"
    elif complex_task or debug_task or size in {"L", "XL"}:
        risk = "medium"
    else:
        risk = "low"

    return {"size": size, "risk": risk}


def make_budget(size: str, mode: str) -> dict[str, str | int]:
    """Return soft guidance only; these are not execution gates."""
    mode = mode.lower()
    if mode not in {"economy", "balanced", "emergency"}:
        raise ValueError(f"Unsupported mode: {mode}")

    size_index = SIZE_ORDER.index(size)

    discovery_by_mode = {
        "economy": [
            "1-2 targeted files",
            "2-4 targeted files",
            "4-7 targeted files",
            "6-10 targeted files",
            "targeted only; expand on evidence",
        ],
        "balanced": [
            "1-3 targeted files",
            "3-5 targeted files",
            "5-8 targeted files",
            "8-12 targeted files",
            "targeted first; expand on evidence",
        ],
        "emergency": ["minimum targeted context"] * 5,
    }
    verification_by_size = [
        "Level 1",
        "Level 2",
        "Level 2-3",
        "Level 3",
        "Level 3-4",
    ]
    reasoning_by_size = ["low", "low", "low/medium", "medium", "medium/high"]
    model_role_by_size = ["economy", "economy", "balanced", "balanced/deep", "deep"]

    if mode == "emergency":
        verification = "focused only unless safety-critical"
        reasoning = "lowest adequate"
        model_role = "economy first"
        subagents = "no"
    else:
        verification = verification_by_size[size_index]
        reasoning = reasoning_by_size[size_index]
        model_role = model_role_by_size[size_index]
        subagents = "no" if size_index <= 2 else "only for independent parallel work"

    return {
        "discovery": discovery_by_mode[mode][size_index],
        "implementation_paths": 1,
        "verification": verification,
        "reasoning": reasoning,
        "model_role": model_role,
        "subagents": subagents,
        "budget_type": "soft",
    }


def read_current() -> dict[str, Any] | None:
    try:
        return json.loads(current_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_current(data: dict[str, Any]) -> None:
    ensure_home()
    tmp = current_path().with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(current_path())


def append_history(data: dict[str, Any]) -> None:
    ensure_home()
    with history_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")


def archive_superseded(session: dict[str, Any]) -> None:
    item = dict(session)
    item["status"] = "superseded"
    item["finished_at"] = now_iso()
    append_history(item)


def start_session(task: str, mode: str, cwd: str | None = None) -> dict[str, Any]:
    previous = read_current()
    if previous:
        archive_superseded(previous)

    repo = git_info(cwd)
    classification = classify_task(task, repo)
    budget = make_budget(classification["size"], mode)

    session = {
        "id": uuid.uuid4().hex[:8],
        "version": VERSION,
        "status": "active",
        "started_at": now_iso(),
        "task": task.strip() or "(unspecified task)",
        "mode": mode,
        "size": classification["size"],
        "risk": classification["risk"],
        "budget": budget,
        "repo": {
            "root": repo.get("root"),
            "branch": repo.get("branch"),
            "changed_files_at_start": repo.get("changed_files") or [],
        },
        "cqo_overhead_policy": {
            "network_requests": 0,
            "blocking_gates": 0,
            "automatic_model_calls": 0,
            "automatic_subagents": 0,
        },
    }
    write_current(session)
    return session


def audit_session(
    note: str | None = None,
    cwd: str | None = None,
) -> dict[str, Any] | None:
    session = read_current()
    if not session:
        return None

    repo = git_info(cwd or session.get("repo", {}).get("root"))
    audit = dict(session)
    audit["status"] = "completed"
    audit["finished_at"] = now_iso()
    audit["repo_at_audit"] = {
        "root": repo.get("root"),
        "branch": repo.get("branch"),
        "changed_files": repo.get("changed_files") or [],
        "changed_file_count": len(repo.get("changed_files") or []),
    }
    audit["policy_guardrails"] = [
        "CQO did not force a repository-wide scan.",
        "CQO did not force a full test suite.",
        "CQO did not spawn subagents.",
        "CQO did not request a model escalation.",
    ]
    if note:
        audit["note"] = note

    append_history(audit)
    try:
        current_path().unlink()
    except FileNotFoundError:
        pass
    return audit


def load_history(limit: int = 10) -> list[dict[str, Any]]:
    try:
        lines = history_path().read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    items: list[dict[str, Any]] = []
    for line in lines[-max(limit, 1):]:
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_start(session: dict[str, Any]) -> None:
    budget = session["budget"]
    print(f"CQO session {session['id']}")
    print(f"Task: {session['size']} · Risk: {session['risk']} · Mode: {session['mode']}")
    print(
        "Soft budget: "
        f"discovery {budget['discovery']}; "
        f"paths {budget['implementation_paths']}; "
        f"reasoning {budget['reasoning']}; "
        f"verification {budget['verification']}; "
        f"subagents {budget['subagents']}"
    )
    print("Zero-friction policy: no network, no blocking gate, no automatic model call.")


def print_status(session: dict[str, Any] | None) -> None:
    if not session:
        print("No active CQO session.")
        return
    budget = session["budget"]
    print(f"CQO session {session['id']} · active")
    print(f"{session['size']} · {session['risk']} risk · {session['mode']}")
    print(f"Task: {session['task']}")
    print(f"Discovery: {budget['discovery']}")
    print(f"Verification: {budget['verification']}")
    print(f"Model role: {budget['model_role']} · Reasoning: {budget['reasoning']}")
    print(f"Subagents: {budget['subagents']}")


def print_audit(audit: dict[str, Any] | None) -> None:
    if not audit:
        print("No active CQO session. Run cqo start <task> first.")
        return
    repo = audit["repo_at_audit"]
    print(f"CQO audit {audit['id']} · completed")
    print(f"Task: {audit['size']} · Risk: {audit['risk']} · Mode: {audit['mode']}")
    print("Observed:")
    print(f"- Local repository change surface: {repo['changed_file_count']} file(s)")
    if repo.get("branch"):
        print(f"- Branch: {repo['branch']}")
    print("CQO guarantees:")
    print("- No forced repository-wide scan")
    print("- No forced full test suite")
    print("- No automatic subagent")
    print("- No automatic model escalation")
    print("- 0 CQO network requests · 0 blocking gates · 0 automatic model calls")
    if audit.get("note"):
        print(f"Note: {audit['note']}")
    print(f"Recorded locally in {history_path()}")


def print_history(items: list[dict[str, Any]]) -> None:
    if not items:
        print("No CQO history yet.")
        return
    for item in reversed(items):
        status = item.get("status", "?")
        print(
            f"{item.get('finished_at', item.get('started_at', '?'))}  "
            f"{item.get('id', '?')}  "
            f"{item.get('size', '?')}/{item.get('mode', '?')}  "
            f"{status}  "
            f"{item.get('task', '')}"
        )



def doctor_report() -> dict[str, Any]:
    """Inspect the local CQO setup without network access."""
    skill_root = Path(__file__).resolve().parents[1]
    skill_file = skill_root / "SKILL.md"

    home_ok = False
    home_error: str | None = None
    try:
        ensure_home()
        probe = cqo_home() / ".doctor-write-test"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
        home_ok = True
    except OSError as exc:
        home_error = str(exc)

    python_ok = sys.version_info >= (3, 10)
    cli_path = shutil.which("cqo")
    git_path = shutil.which("git")

    required_ok = python_ok and skill_file.is_file() and home_ok
    return {
        "version": VERSION,
        "ok": required_ok,
        "python": {
            "version": ".".join(map(str, sys.version_info[:3])),
            "ok": python_ok,
            "required": ">=3.10",
        },
        "skill": {
            "root": str(skill_root),
            "skill_md": str(skill_file),
            "ok": skill_file.is_file(),
        },
        "journal": {
            "home": str(cqo_home()),
            "writable": home_ok,
            "error": home_error,
        },
        "git": {
            "path": git_path,
            "available": bool(git_path),
            "required": False,
        },
        "cli": {
            "path": cli_path,
            "on_path": bool(cli_path),
            "required": False,
        },
        "active_session": bool(read_current()),
        "network_checks": 0,
    }


def print_doctor(report: dict[str, Any]) -> None:
    mark = lambda ok: "OK" if ok else "WARN"
    print(f"CQO doctor · v{report['version']}")
    print(
        f"[{mark(report['python']['ok'])}] Python "
        f"{report['python']['version']} (required {report['python']['required']})"
    )
    print(
        f"[{mark(report['skill']['ok'])}] Skill "
        f"{report['skill']['skill_md']}"
    )
    print(
        f"[{mark(report['journal']['writable'])}] Local journal "
        f"{report['journal']['home']}"
    )
    print(
        f"[{mark(report['git']['available'])}] Git "
        f"{report['git']['path'] or 'not found'} (optional for CLI)"
    )
    print(
        f"[{mark(report['cli']['on_path'])}] cqo shortcut "
        f"{report['cli']['path'] or 'not on PATH'} (optional)"
    )
    print(
        "Zero-friction check: 0 network requests · "
        "0 model calls · 0 blocking gates"
    )
    print("Required setup: ready" if report["ok"] else "Required setup: needs attention")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cqo",
        description="Zero-friction local usage governor for Codex.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser(
        "start",
        help="Classify a task and create a soft local budget.",
    )
    start.add_argument("task", nargs="*", help="Task text. Quotes are optional.")
    start.add_argument(
        "--mode",
        choices=("economy", "balanced", "emergency"),
        default=os.environ.get("CQO_MODE", "balanced"),
    )
    start.add_argument("--cwd", default=None, help="Repository path to inspect locally.")
    start.add_argument("--json", action="store_true")

    status = sub.add_parser(
        "status",
        help="Show the active local CQO session.",
    )
    status.add_argument("--json", action="store_true")

    audit = sub.add_parser(
        "audit",
        help="Finalize the active session and write a local audit.",
    )
    audit.add_argument("--note", default=None, help="Optional local note.")
    audit.add_argument("--cwd", default=None, help="Repository path to inspect locally.")
    audit.add_argument("--json", action="store_true")

    history = sub.add_parser(
        "history",
        help="Show recent local CQO sessions.",
    )
    history.add_argument("--limit", type=int, default=10)
    history.add_argument("--json", action="store_true")

    doctor = sub.add_parser(
        "doctor",
        help="Check local CQO installation and optional CLI setup.",
    )
    doctor.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "start":
        session = start_session(" ".join(args.task), args.mode, args.cwd)
        print_json(session) if args.json else print_start(session)
        return 0

    if args.command == "status":
        session = read_current()
        if args.json:
            print_json(session or {})
        else:
            print_status(session)
        return 0

    if args.command == "audit":
        audit = audit_session(args.note, args.cwd)
        if args.json:
            print_json(audit or {})
        else:
            print_audit(audit)
        return 0

    if args.command == "history":
        items = load_history(args.limit)
        if args.json:
            print_json(items)
        else:
            print_history(items)
        return 0

    if args.command == "doctor":
        report = doctor_report()
        if args.json:
            print_json(report)
        else:
            print_doctor(report)
        return 0 if report["ok"] else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
