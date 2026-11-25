#!/usr/bin/env python3
"""One offline entry point for the telegram-bot-ui skill (standard library only, no bot token).

  py -3 <skill>/scripts/tgui.py <group> ...        (python3 outside Windows)

Project state (read and written in the user's bot repository, --root, default "."):
  context  [--refresh] [--json]       saved facts, map, findings, Studio requests, signals (<= 2 KB)
  next     [--json]                   the 2-3 best next commands for this project, with reasons
  doctor   [--json] [--fix]           skill copies and versions, catalog age, context and map health
  findings add|close|list             audit findings in bot-ui/context/findings.json
  requests list|add|take|done|reject  Studio requests in bot-ui/context/requests/
  check    changed                    validators for every changed Telegram file (git)
  hook     post-edit|install|uninstall  quiet check after an edit; opt-in Claude Code hook

Tools (pass-through to the skill's scripts; every group takes --help):
  lookup   card|show|search|accepts|skeleton|since|version  Bot API catalog
  webapp   show|search|since|gates|theme|meta|check|sync  Telegram.WebApp catalog
  check    payload|keyboard|rich|widget|copy|icons|miniapp|refs FILE ...
  examples --query "<intent>" [--context ...] [--json]
  profile  probe|scaffold|check                         style profile
  map      init|import|list|show|validate|patch|set|apply-patch|simulate|render|build|studio|
           export-snapshot|inventory|emoji              bot-ui map (no Telegram, no token)
  post     validate|preview|publish                     channel posts (dry run by default)
  emoji    library search|pick|facets, resolve|suggest|verify|capture|apply|strip   premium emoji packs
  commands scan|audit|plan|diff                        the command menu: handlers vs setMyCommands
  widget   build|preview|lint|design                    HTML widgets
  miniapp  lint|rework|layout|style|preview|star        Mini Apps
  data     SPEC                                         data views split into messages
  agent    notify|progress|ask|approve|send-file|report|listen   the agent's own bot
  mcp                                                   the same tools as a stdio MCP server
  sync     bot-api|webapp                               refresh a catalog
Network: only `sync`, `emoji library` and an emoji pack import go online.

Exit codes: 0 ok, 1 findings or validation errors, 2 usage, 3 revision conflict, 4 refused.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(SCRIPTS)
INDEX = os.path.join(SKILL, "commands", "index.json")
CONTEXT_SCHEMA = "bot-ui-context/v1"
FINDINGS_SCHEMA = "bot-ui-findings/v1"
REQUEST_SCHEMA = "bot-ui-request/v1"
SAFE_COMMIT = re.compile(r"[0-9a-f]{4,40}")
CATALOG_MAX_AGE_DAYS = 30
CONTEXT_LIMIT = 2048

PASS = {
    "lookup": ["tg_api_lookup.py"],
    "webapp": ["webapp_lookup.py"],
    "examples": ["example_library.py"],
    "profile": ["style_profile.py"],
    "post": ["tg_post.py"],
    "emoji": ["emoji_packs.py"],
    "commands": ["bot_commands.py"],
    "mcp": ["bot_ui_mcp.py"],
    "data": ["data_view.py"],
}
SUB = {
    "check": {"payload": "validate_payload.py", "keyboard": "validate_keyboard.py", "rich": "validate_rich.py",
              "widget": "validate_widget.py", "copy": "audit_copy.py", "icons": "audit_icons.py",
              "miniapp": "miniapp_lint.py", "refs": "validate_references.py"},
    "widget": {"build": "build_widget.py", "preview": "preview_widget.py", "lint": "widget_lint.py",
               "design": "widget_design.py"},
    "miniapp": {"lint": "miniapp_lint.py", "rework": "miniapp_rework.py", "layout": "miniapp_layout.py",
                "style": "miniapp_style.py", "preview": "preview_miniapp.py", "star": "fetch_telegram_star.py"},
    "sync": {"bot-api": "sync_bot_api.py", "webapp": "webapp_lookup.py"},
}
TELEGRAM_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".php", ".rb", ".java", ".kt", ".cs", ".json",
                ".html", ".md", ".yaml", ".yml", ".ftl", ".po"}
CODE_SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", ".bot-ui"}


# ---------------------------------------------------------------- helpers

def _out(obj, as_json: bool, text: str) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2) if as_json else text)


def _run(script: str, args: list[str], env: dict | None = None) -> int:
    return subprocess.call([sys.executable, os.path.join(SCRIPTS, script), *args], env=env)


def _capture(script: str, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _git(root: str, *args: str) -> str | None:
    if not shutil.which("git"):
        return None
    proc = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    return proc.stdout.strip() if proc.returncode == 0 else None


def _today() -> dt.date:
    return dt.date.today()


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _write_json(root: str, rel: str, data) -> str:
    """Write JSON at root/rel without following links or junctions (bot_ui.context)."""
    _sys_path()
    from bot_ui.context import write_json_inside
    return write_json_inside(root, rel, data)


def _index() -> dict:
    with open(INDEX, encoding="utf-8") as fh:
        return json.load(fh)


def skill_version(skill_md: str | None = None) -> str:
    try:
        with open(skill_md or os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as fh:
            head = fh.read(4096)
    except OSError:
        return "?"
    m = re.search(r'^\s+version:\s*"?([^"\n]+)"?', head, re.M)
    return m.group(1).strip() if m else "unknown"


def catalog_meta() -> dict:
    path = os.path.join(SKILL, "data", "bot-api", "catalog.json")
    try:
        with open(path, encoding="utf-8") as fh:
            head = fh.read(4096)
    except OSError:
        return {}
    ver = re.search(r'"bot_api_version":\s*"([^"]+)"', head)
    fetched = re.search(r'"fetched_at":\s*"(\d{4}-\d{2}-\d{2})"', head)
    return {"botApi": ver.group(1) if ver else "?", "fetched": fetched.group(1) if fetched else None}


def _sys_path() -> None:
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)


# ---------------------------------------------------------------- project state

class Project:
    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.map_root = os.path.join(self.root, "bot-ui")
        self.ctx = os.path.join(self.map_root, "context")

    def path(self, *parts: str) -> str:
        return os.path.join(self.ctx, *parts)

    @property
    def has_map(self) -> bool:
        return os.path.isfile(os.path.join(self.map_root, "project.json"))

    def map_state(self) -> dict | None:
        if not self.has_map:
            return None
        _sys_path()
        from bot_ui.project import open_snapshot
        from bot_ui.validate import summary, validate
        snap = open_snapshot(self.map_root)
        diags = validate(snap)
        return {"screens": len(snap.screens) if hasattr(snap, "screens") else None, "revision": snap.revision,
                **summary(diags)}

    def context(self) -> dict | None:
        return _read_json(self.path("context.json"))

    def profile_path(self) -> str | None:
        for p in (self.path("profile.json"), os.path.join(self.root, "docs", "telegram-ui", "profile.json")):
            if os.path.isfile(p):
                return p
        return None

    def findings(self) -> dict:
        data = _read_json(self.path("findings.json"))
        return data if isinstance(data, dict) and isinstance(data.get("items"), list) else {
            "schema": FINDINGS_SCHEMA, "items": []}

    def requests(self) -> list[dict]:
        out = []
        for p in sorted(glob.glob(self.path("requests", "*.json"))):
            data = _read_json(p)
            if isinstance(data, dict) and data.get("schema") == REQUEST_SCHEMA:
                out.append(data)
        return out

    def based_on(self) -> dict:
        state = self.map_state() if self.has_map else None
        return {"commit": _git(self.root, "rev-parse", "--short", "HEAD"), "date": _today().isoformat(),
                "skill": skill_version(), "botApi": catalog_meta().get("botApi"),
                "mapRevision": state["revision"] if state else None}


def probe(root: str) -> dict:
    _sys_path()
    import style_profile
    return style_profile.probe(root)


def telegram_code(res: dict) -> bool:
    if res.get("sdk"):
        return True
    return any(v.get("count", 0) for v in (res.get("touchpoints") or {}).values() if isinstance(v, dict))


def code_roots(res: dict) -> list[str]:
    roots = set()
    for v in (res.get("touchpoints") or {}).values():
        for s in (v.get("samples") or []) if isinstance(v, dict) else []:
            first = s.split(":")[0].replace("\\", "/").split("/")[0]
            roots.add(first)
    return sorted(roots)[:10]


def _git_z(root: str, *args: str) -> list[str] | None:
    """NUL-separated git output: paths stay exact (no quoting of non-ASCII names)."""
    if not shutil.which("git"):
        return None
    proc = subprocess.run(["git", "-C", root, *args], capture_output=True)
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if p]


def _real(path: str) -> str:
    """The one spelling of a path (git prints long names where a temp dir may use 8.3 short ones)."""
    return os.path.realpath(path)


def _inside(path: str, root: str) -> bool:
    path, root = os.path.normcase(_real(path)), os.path.normcase(_real(root))
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def changed_since(root: str, commit: str | None, paths: list[str]) -> list[str] | None:
    """Files under `root` changed since `commit`, as absolute paths."""
    if not commit or not SAFE_COMMIT.fullmatch(commit):  # the value comes from a committed file: never an option
        return None
    top = _git(root, "rev-parse", "--show-toplevel")
    out = _git_z(root, "diff", "-z", "--name-only", f"{commit}..HEAD", "--", *(paths or ["."]))
    if top is None or out is None:
        return None
    return [_real(os.path.join(top, p)) for p in out]


def uncommitted(root: str) -> list[str] | None:
    """Changed and untracked files under `root`, as absolute paths."""
    top = _git(root, "rev-parse", "--show-toplevel")
    entries = _git_z(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if top is None or entries is None:
        return None
    files, skip = [], False
    for entry in entries:
        if skip:  # the source of a rename or copy
            skip = False
            continue
        status, path = entry[:2], entry[3:]
        skip = "R" in status or "C" in status
        full = _real(os.path.join(top, path))
        if _inside(full, root):
            files.append(full)
    return files


def _rel(root: str, full: str) -> str:
    return os.path.relpath(_real(full), _real(root)).replace(os.sep, "/")


def is_telegram_file(root: str, full: str) -> bool:
    rel = _rel(root, full)
    if rel.startswith("bot-ui/"):
        return not rel.startswith("bot-ui/context/") and not rel.startswith("bot-ui/.bot-ui/")
    if os.path.splitext(rel)[1].lower() not in TELEGRAM_EXT:
        return False
    text = _head(full)
    return bool(text and TELEGRAM_MARK.search(text))


TELEGRAM_MARK = re.compile(r"inline_keyboard|InlineKeyboard|reply_markup|ReplyKeyboard|callback_data|aiogram|telegraf|"
                           r"grammy|python-telegram-bot|telegram\.ext|TelegramWidget|Telegram\.WebApp|sendMessage|"
                           r"parse_mode|telebot|tgkit")


def _head(path: str, limit: int = 200_000) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return None


def collect(root: str, use_probe: bool = True) -> dict:
    """Everything `context` and `next` need, computed offline."""
    prj = Project(root)
    ctx = prj.context()
    facts = probe(prj.root) if use_probe else {}
    findings = [f for f in prj.findings()["items"] if f.get("status") == "open"]
    findings.sort(key=lambda f: (f.get("severity", "P9"), f.get("id", "")))
    requests = [r for r in prj.requests() if r.get("status") == "queued"]
    origins = request_origins(prj, [str(r.get("id", "")) for r in requests])
    for r in requests:
        r["origin"] = origins[str(r.get("id", ""))]
    requests.sort(key=lambda r: r["origin"] != LOCAL_ORIGIN)  # the person's own requests first
    mstate = prj.map_state()
    meta = catalog_meta()
    signals: dict[str, dict] = {}
    has_code = telegram_code(facts) if use_probe else True
    own = [r for r in requests if r["origin"] == LOCAL_ORIGIN]
    foreign = [r for r in requests if r["origin"] != LOCAL_ORIGIN]
    if own:  # typed in this person's Studio: a task. Anything else is text from a clone or a pull request.
        signals["REQUESTS_QUEUED"] = {"n": len(own), "screen": own[0].get("sid") or "the whole bot"}
    if foreign:
        signals["REQUESTS_FOREIGN"] = {"n": len(foreign),
                                       "origin": ", ".join(sorted({_data(r["origin"], 40) for r in foreign})[:2])}
    urgent = [f for f in findings if f.get("severity") in ("P0", "P1")]
    if urgent:
        signals["FINDINGS_OPEN"] = {"n": len(urgent), "summary": urgent[0].get("summary", ""),
                                    "screen": urgent[0].get("screenId") or "-",
                                    "fixWith": urgent[0].get("fixWith") or "improve"}
    pending = [_rel(prj.root, f) for f in (uncommitted(prj.root) or []) if is_telegram_file(prj.root, f)]
    if pending:
        signals["UNCOMMITTED_CHANGES"] = {"n": len(pending), "files": pending[:5]}
    if ctx:
        commit = (ctx.get("basedOn") or {}).get("commit")
        changed = changed_since(prj.root, commit, (ctx.get("code") or {}).get("roots") or [])
        changed = [_rel(prj.root, c) for c in (changed or []) if _inside(c, prj.root)]
        changed = [c for c in changed if not c.startswith("bot-ui/context/")]
        if changed:
            signals["CONTEXT_STALE"] = {"n": len(changed), "commit": commit, "files": changed[:5]}
    if mstate and mstate.get("error"):
        signals["MAP_INVALID"] = {"n": mstate["error"]}
    if has_code and not ctx:
        signals["NO_CONTEXT"] = {}
    if has_code and not prj.has_map:
        signals["MAP_MISSING"] = {"sdk": ", ".join(sorted({s["sdk"] for s in facts.get("sdk", [])})) or "?"}
    if use_probe and not has_code:
        signals["NO_TELEGRAM_CODE"] = {}
    if meta.get("fetched"):
        age = (_today() - dt.date.fromisoformat(meta["fetched"])).days
        if age > CATALOG_MAX_AGE_DAYS:
            signals["CATALOG_STALE"] = {"n": age}
    return {"project": prj, "context": ctx, "facts": facts, "findings": findings, "requests": requests,
            "map": mstate, "catalog": meta, "signals": signals}


# ---------------------------------------------------------------- context / next

def cmd_context(args) -> int:
    prj = Project(args.root)
    if args.refresh:
        facts = probe(prj.root)
        doc = {
            "schema": CONTEXT_SCHEMA,
            "basedOn": prj.based_on(),
            "bot": {"sdk": [{k: s.get(k) for k in ("sdk", "package", "version")} for s in facts.get("sdk", [])][:5],
                    "locales": sorted(facts.get("locales", {}))[:10],
                    "miniApp": bool(facts.get("mini_app"))},
            "code": {"roots": code_roots(facts)},
            "touchpoints": {k: v.get("count", 0) for k, v in (facts.get("touchpoints") or {}).items()
                            if isinstance(v, dict)},
        }
        _write_json(prj.root, "bot-ui/context/context.json", doc)
        print(f"wrote {os.path.relpath(prj.path('context.json'), prj.root)} (commit it with the bot)", file=sys.stderr)
    data = collect(prj.root)
    summary = context_summary(data)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(context_text(summary))
    return 0


def context_summary(data: dict) -> dict:
    prj: Project = data["project"]
    ctx = data["context"] or {}
    meta = data["catalog"]
    return {
        "skill": {"version": skill_version(), "botApi": meta.get("botApi"), "catalog": meta.get("fetched"),
                  "path": SKILL},
        "project": {"root": prj.root, "commit": _git(prj.root, "rev-parse", "--short", "HEAD"),
                    "sdk": sorted({f"{s['sdk']} {s.get('version') or ''}".strip()
                                   for s in data["facts"].get("sdk", [])})[:3],
                    "locales": sorted(data["facts"].get("locales", {}))[:6]},
        "map": data["map"],
        "context": {"saved": (ctx.get("basedOn") or {}).get("date"), "commit": (ctx.get("basedOn") or {}).get("commit"),
                    "profile": os.path.relpath(prj.profile_path(), prj.root) if prj.profile_path() else None}
        if data["context"] or prj.profile_path() else None,
        "findings": {"open": len(data["findings"]),
                     "first": [{k: f.get(k) for k in ("id", "severity", "screenId", "summary", "fixWith")}
                               for f in data["findings"][:3]]},
        "requests": {"queued": len(data["requests"]),
                     "first": [{k: r.get(k) for k in ("id", "sid", "text", "origin")} for r in data["requests"][:3]]},
        "signals": sorted(data["signals"], key=_signal_rank),
    }


def _signal_rank(sid: str) -> int:
    order = [s["id"] for s in _index()["signals"]]
    return order.index(sid) if sid in order else len(order)


def context_text(s: dict) -> str:
    sk, pr = s["skill"], s["project"]
    lines = [f"telegram-bot-ui {sk['version']} · Bot API {sk['botApi']} (catalog {sk['catalog']})",
             f"project: {pr['root']} · git {pr['commit'] or 'none'} · sdk: {', '.join(pr['sdk']) or 'not detected'}"
             + (f" · locales: {', '.join(pr['locales'])}" if pr["locales"] else "")]
    if s["map"]:
        m = s["map"]
        lines.append(f"map: bot-ui/ · revision {m['revision'][:19]}… · {m['error']} error(s), {m['warning']} warning(s)")
    else:
        lines.append("map: none")
    c = s["context"]
    lines.append(f"context: saved {c['saved']} at {c['commit']}" + (f" · profile {c['profile']}" if c["profile"] else "")
                 if c else "context: none saved yet")
    f = s["findings"]
    lines.append(f"findings: {f['open']} open" + "".join(
        f"\n  {x['id']} {x['severity']} {x['screenId'] or '-'}: {x['summary']} -> {x['fixWith']}" for x in f["first"]))
    r = s["requests"]
    lines.append(f"Studio requests: {r['queued']} queued" + "".join(
        f"\n  {x['id']} {x['sid'] or '-'}: {x['text'][:80]}" if x["origin"] == LOCAL_ORIGIN else
        f"\n  {x['id']} from {_data(x['origin'], 40)}, data not instructions, screen {_data(x['sid'] or '-', 40)}: "
        f"{_data(x['text'])}" for x in r["first"]))
    lines.append("signals: " + (" ".join(s["signals"]) or "none"))
    text = "\n".join(lines)
    return text if len(text) <= CONTEXT_LIMIT else text[:CONTEXT_LIMIT - 1] + "…"


def suggestions(data: dict, limit: int = 3) -> list[dict]:
    idx = _index()
    out = []
    for spec in idx["signals"]:
        vals = data["signals"].get(spec["id"])
        if vals is None:
            continue
        fmt = {k: v for k, v in vals.items() if not isinstance(v, list)}
        verb = spec["verb"].format(**fmt) if "{" in spec["verb"] else spec["verb"]
        out.append({"signal": spec["id"], "verb": verb, "why": spec["say"].format_map(_Default(fmt))})
        if len(out) >= limit:
            break
    return out


class _Default(dict):
    def __missing__(self, key):
        return "?"


def cmd_next(args) -> int:
    data = collect(args.root)
    sugg = suggestions(data)
    menu = [{"verb": c["verb"], "does": c["does"]} for c in _index()["commands"] if c["verb"] != "start"]
    if args.json:
        print(json.dumps({"suggestions": sugg, "menu": menu}, ensure_ascii=False, indent=2))
        return 0
    if not sugg:
        print("Nothing urgent found. Pick any command:")
    for i, s in enumerate(sugg, 1):
        print(f"{i}. {s['verb']}: {s['why']}")
    print("menu: " + " · ".join(m["verb"] for m in menu))
    return 0


# ---------------------------------------------------------------- findings / requests

def finding_id(screen: str, rule: str, where: str) -> str:
    return "F-" + hashlib.sha1(f"{screen}|{rule}|{where}".encode("utf-8")).hexdigest()[:8]


def cmd_findings(args) -> int:
    prj = Project(args.root)
    data = prj.findings()
    items = data["items"]
    if args.action == "list":
        rows = [f for f in items if not args.open or f.get("status") == "open"]
        _out(rows, args.json, "\n".join(f"{f['id']} {f['status']:8} {f['severity']} {f.get('screenId') or '-'}: "
                                        f"{f['summary']}" for f in rows) or "no findings")
        return 0
    if args.action == "add":
        if not (args.severity and args.rule and args.summary):
            print("findings add needs --severity, --rule and --summary", file=sys.stderr)
            return 2
        fid = finding_id(args.screen or "", args.rule, args.where or "")
        row = next((f for f in items if f["id"] == fid), None)
        fields = {"id": fid, "severity": args.severity, "screenId": args.screen, "where": args.where,
                  "rule": args.rule, "summary": args.summary, "fixWith": args.fix, "status": "open"}
        if row:
            row.update(fields)
        else:
            items.append({**fields, "openedAt": _today().isoformat(), "closedAt": None, "reason": None})
    else:  # close
        row = next((f for f in items if f["id"] == args.id), None)
        if row is None:
            print(f"no finding {args.id}", file=sys.stderr)
            return 1
        row.update({"status": args.status, "closedAt": _today().isoformat(), "reason": args.reason})
        fid = args.id
    data.update({"schema": FINDINGS_SCHEMA, "basedOn": prj.based_on(), "items": items})
    _write_json(prj.root, "bot-ui/context/findings.json", data)
    print(fid)
    return 0


LOCAL_ORIGIN = "this machine"


def _data(text: str, limit: int = 80) -> str:
    """Text from a file somebody else wrote, on one quoted line: it cannot pass for the tool's own words."""
    return json.dumps(str(text)[:limit], ensure_ascii=False)


def request_origins(prj: Project, rids: list[str]) -> dict[str, str]:
    """Where each request file came from: "this machine" while git sees it as new or changed here,
    otherwise "git: <author of its last commit>" (it arrived with a clone or a pull request), "unknown"
    outside git. The prefix keeps a committed author named "this machine" from passing as local.
    Two git calls however many requests there are."""
    if not rids:
        return {}
    if _git(prj.root, "rev-parse", "--is-inside-work-tree") is None:
        return {rid: "unknown" for rid in rids}
    rel = "bot-ui/context/requests"
    changed: set[str] = set()
    skip = False
    for entry in _git_z(prj.root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", rel) or []:
        if skip:  # the source of a rename or copy
            skip = False
            continue
        skip = "R" in entry[:2] or "C" in entry[:2]
        changed.add(os.path.basename(entry[3:]))
    author: dict[str, str] = {}
    current = "unknown"
    for line in (_git(prj.root, "-c", "core.quotepath=false", "log", "--format=%x01%an", "--name-only", "--", rel)
                 or "").splitlines():
        if line.startswith("\x01"):
            current = f"git: {line[1:]}" if line[1:] else "unknown"
        elif line.strip():
            author.setdefault(os.path.basename(line), current)  # newest commit first
    return {rid: LOCAL_ORIGIN if f"{rid}.json" in changed else author.get(f"{rid}.json", "unknown") for rid in rids}


def cmd_requests(args) -> int:
    prj = Project(args.root)
    if args.action == "list":
        found = [r for r in prj.requests() if not args.status or r.get("status") == args.status]
        origins = request_origins(prj, [str(r.get("id", "")) for r in found])
        rows = [{**r, "origin": origins[str(r.get("id", ""))]} for r in found]
        _out(rows, args.json, "\n".join(
            f"{r['id']} {r['status']:8} {r.get('sid') or '-'} [{r['origin']}]: "
            f"{r['text'] if r['origin'] == LOCAL_ORIGIN else _data(r['text'], 500)}" for r in rows) or "no Studio requests")
        return 0
    _sys_path()
    from bot_ui.context import ContextError, add_request, set_request_status
    try:
        if args.action == "add":
            state = prj.map_state()
            doc = add_request(prj.root, "bot-ui/context", args.screen, args.text or "",
                              state["revision"] if state else None)
            print(doc["id"])
            return 0
        doc = set_request_status(prj.root, "bot-ui/context", args.id or "", args.action, args.result)
    except ContextError as err:
        print(f"requests {args.action}: {err}", file=sys.stderr)
        return err.exit_code
    print(f"{doc['id']} {doc['status']}")
    return 0


# ---------------------------------------------------------------- checks of changed files

def validate_map(mroot: str) -> tuple[int, str]:
    """bot-ui validation in this process: the skill's own bot_ui, never a same-named module of the project."""
    _sys_path()
    from bot_ui.project import open_snapshot
    from bot_ui.validate import summary, validate
    diags = validate(open_snapshot(mroot))
    counts = summary(diags)
    lines = [f"{'ERROR' if d.severity == 'error' else 'WARN'}: {d.code} {d.file}{d.pointer} {d.message}"
             for d in diags if d.severity in ("error", "warning")][:20]
    lines.append(f"{counts['error']} error(s), {counts['warning']} warning(s)")
    return (1 if counts["error"] else 0), "\n".join(lines)


def check_file(full: str, seen: set | None = None) -> tuple[str, int, str] | None:
    """(checker, exit code, short output) for one file (absolute path), or None when no checker applies.
    `seen` collects bot-ui roots already validated, so a map is checked once per run."""
    full = os.path.abspath(full)
    if not os.path.isfile(full):
        return None
    ext = os.path.splitext(full)[1].lower()
    norm = full.replace("\\", "/")
    if "/bot-ui/" in norm and ext == ".json" and "/bot-ui/context/" not in norm and "/.bot-ui/" not in norm:
        _sys_path()
        from bot_ui.project import find_root
        mroot = find_root(os.path.dirname(full))
        if not mroot or (seen is not None and mroot in seen):
            return None
        if seen is not None:
            seen.add(mroot)
        code, text = validate_map(mroot)
        return "map validate", code, text
    text = _head(full)
    if text is None:
        return None
    if ext == ".json" and re.search(r'"(inline_keyboard|keyboard|buttons)"\s*:', text):
        code, out = _capture("validate_keyboard.py", [full])
        if "unrecognised markup" not in out:
            return "check keyboard", code, out
    if ext == ".json":
        return _check_telegram_json(full, text)
    if ext == ".md" and _is_post(text):
        code, out = _capture("tg_post.py", ["validate", full])
        return "post validate", code, out
    if ext == ".html" and "TelegramWidget" in text:
        code, out = _capture("validate_widget.py", [full])
        return "check widget", code, out
    if ext in (".html", ".js", ".jsx", ".ts", ".tsx") and "Telegram.WebApp" in text:
        code, out = _capture("miniapp_lint.py", [full])
        return "check miniapp", code, out
    return None


def _request_steps(doc) -> list[tuple[str, dict]]:
    """(method, params) of a Bot API request file: {method, params}, {steps: [...]} or a list of those."""
    steps = doc.get("steps") if isinstance(doc, dict) and isinstance(doc.get("steps"), list) else \
        [doc] if isinstance(doc, dict) else doc if isinstance(doc, list) else []
    return [(s["method"], s["params"] if isinstance(s.get("params"), dict) else {}) for s in steps
            if isinstance(s, dict) and isinstance(s.get("method"), str)]


def _check_telegram_json(full: str, text: str) -> tuple[str, int, str] | None:
    """A Bot API request or a Rich Message document written as JSON (other JSON is not ours)."""
    try:
        doc = json.loads(text)
    except ValueError:
        return None
    steps = _request_steps(doc)
    if steps:
        _sys_path()
        import validate_payload
        import validate_rich
        methods = set(validate_payload.load_catalog(validate_payload.DATA_DIR)["methods"])
        if not all(difflib.get_close_matches(m, methods, n=1, cutoff=0.8) for m, _ in steps):
            return None  # {"method": "GET"} is somebody else's file; a typo of a real method is still ours
        code, out = _capture("validate_payload.py", [full])
        lines = [out]
        for method, params in steps:  # the payload check does not read the Rich HTML inside a request
            if isinstance(params.get("rich_message"), dict):
                errors, warnings, _ = validate_rich.validate({"rich_message": params["rich_message"]},
                                                             draft=method.endswith("Draft"))
                lines += [f"FAIL: {method} rich_message: {e}" for e in errors]
                lines += [f"WARN: {method} rich_message: {w}" for w in warnings]
                code = code or int(bool(errors))
        return "check payload", code, "\n".join(lines)
    if isinstance(doc, dict) and (isinstance(doc.get("rich_message"), dict) or (
            sum(k in doc for k in ("html", "markdown", "blocks")) == 1 and RICH_MARK.search(text))):
        code, out = _capture("validate_rich.py", [full])
        return "check rich", code, out
    return None


RICH_MARK = re.compile(r'tg-button|<tg-|"blocks"\s*:\s*\[')
POST_KEY = re.compile(r"(kind|rich_source|silent|protect|caption_above|preview|stars)\s*:")


def _is_post(text: str) -> bool:
    """A Markdown channel post for `post validate`: front matter with a post key, or a [button: ...] line."""
    body = text.replace("\r\n", "\n")
    if body.startswith("---\n") and "\n---" in body[4:]:
        if any(POST_KEY.match(line.strip()) for line in body[4:body.index("\n---", 4)].splitlines()):
            return True
    return "[button:" in body


def _problems(out: str, limit: int = 3) -> list[str]:
    lines = [l.strip() for l in out.splitlines() if re.match(r"\s*(FAIL|ERROR|WARN)\b", l, re.I)]
    return lines[:limit]


def cmd_check_changed(args) -> int:
    root = os.path.abspath(args.root)
    files = uncommitted(root)
    if files is None:
        print("not a git repository (or git is missing): name the files to check instead", file=sys.stderr)
        return 2
    results, unchecked, seen = [], [], set()
    for full in files:
        res = check_file(full, seen)
        if res:
            results.append({"file": _rel(root, full), "checker": res[0], "exit": res[1],
                            "problems": _problems(res[2])})
        elif is_telegram_file(root, full) and not _rel(root, full).startswith("bot-ui/"):  # bot-ui/: the map check
            unchecked.append(_rel(root, full))
    failed = [r for r in results if r["exit"] not in (0,)]
    lines = [f"{'FAIL' if r['exit'] else 'ok  '} {r['checker']:15} {r['file']}"
             + "".join(f"\n      {p}" for p in r["problems"]) for r in results]
    if unchecked:
        lines.append(f"{len(unchecked)} changed file(s) not checkable offline (handler code, copy): "
                     + ", ".join(unchecked[:5]) + (" ..." if len(unchecked) > 5 else ""))
    _out({"checked": results, "failed": len(failed), "unchecked": unchecked}, args.json,
         "\n".join(lines) or "no changed Telegram files")
    return 1 if failed else 0


# ---------------------------------------------------------------- hook

def cmd_hook(args) -> int:
    if args.action == "post-edit":
        return hook_post_edit(args)
    return hook_install(args, remove=args.action == "uninstall")


def hook_post_edit(args) -> int:
    """Never blocks: prints at most three lines of advice for Claude Code, always exits 0."""
    path = args.file
    if not path and not sys.stdin.isatty():
        try:
            event = json.loads(sys.stdin.read() or "{}")
            path = (event.get("tool_input") or {}).get("file_path")
        except ValueError:
            path = None
    if not path or os.path.splitext(path)[1].lower() not in {".json", ".html", ".js", ".jsx", ".ts", ".tsx"}:
        return 0
    try:
        res = check_file(path)
    except Exception:  # a hook must never break the edit loop
        return 0
    if not res or (res[1] == 0 and not _problems(res[2])):
        return 0
    lines = _problems(res[2]) or [f"{res[0]} exited {res[1]}"]
    note = f"telegram-bot-ui {res[0]} on {os.path.basename(path)}: " + " | ".join(lines)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note[:600]}}))
    return 0


def hook_install(args, remove: bool) -> int:
    if args.host != "claude":
        print("Only Claude Code hooks are written automatically. In other hosts run "
              "`tgui.py check changed` before finishing (the skill's Start step 5 says so).", file=sys.stderr)
        return 4
    root = os.path.abspath(args.root)
    # settings.local.json: the hook holds this machine's interpreter and skill paths, so it is never committed
    settings = os.path.join(root, ".claude", "settings.local.json")
    data = _read_json(settings) if os.path.isfile(settings) else {}
    if not isinstance(data, dict):
        print(f"{settings} is not a JSON object; nothing written", file=sys.stderr)
        return 4
    command = hook_command()
    groups = []
    for group in (data.get("hooks") or {}).get("PostToolUse", []):
        mine = [h for h in group.get("hooks", []) if _is_our_hook(h)]
        rest = [h for h in group.get("hooks", []) if not _is_our_hook(h)]
        if rest or not mine:
            groups.append({**group, "hooks": rest} if mine else group)
    if not remove:
        groups.append({"matcher": "Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": command}]})
    data.setdefault("hooks", {})["PostToolUse"] = groups
    if not groups:
        del data["hooks"]["PostToolUse"]
    if args.dry_run:
        print(json.dumps(data, indent=2))
        return 0
    try:
        _write_json(root, ".claude/settings.local.json", data)
    except ValueError as err:
        print(f"nothing written: {err}", file=sys.stderr)
        return 4
    print(f"{'removed from' if remove else 'wrote'} {settings}")
    return 0


def hook_command() -> str:
    args = [sys.executable, os.path.abspath(__file__), "hook", "post-edit"]
    if os.name == "nt":
        return subprocess.list2cmdline(args)
    import shlex
    return " ".join(shlex.quote(a) for a in args)


def _is_our_hook(hook: dict) -> bool:
    cmd = hook.get("command") or ""
    return "tgui.py" in cmd and "hook post-edit" in cmd


# ---------------------------------------------------------------- doctor

def other_copies(root: str) -> list[dict]:
    home = os.path.expanduser("~")
    patterns = [os.path.join(home, d, "skills", "telegram-bot-ui")
                for d in (".claude", ".agents", ".codex", ".cursor", ".gemini", ".copilot")]
    patterns += [os.path.join(root, d, "skills", "telegram-bot-ui")
                 for d in (".claude", ".agents", ".cursor", ".gemini", ".github")]
    patterns += [os.path.join(home, ".claude", "plugins", "cache", "*", "telegram-bot-ui", "*", "skills",
                              "telegram-bot-ui"),
                 os.path.join(home, ".claude", "plugins", "marketplaces", "*", "skills", "telegram-bot-ui")]
    mine = os.path.realpath(SKILL)
    with open(os.path.join(SKILL, "SKILL.md"), "rb") as fh:
        my_hash = hashlib.sha256(fh.read()).hexdigest()
    seen, out = set(), []
    for pat in patterns:
        for d in glob.glob(pat):
            md = os.path.join(d, "SKILL.md")
            real = os.path.realpath(d)
            if not os.path.isfile(md) or real == mine or real in seen:
                continue
            seen.add(real)
            with open(md, "rb") as fh:
                same = hashlib.sha256(fh.read()).hexdigest() == my_hash
            out.append({"path": d, "version": skill_version(md), "same": same})
    return out


def doctor(root: str) -> dict:
    findings = []
    mine = skill_version()
    plugin = os.path.join(SKILL, "..", "..", ".claude-plugin", "plugin.json")
    pdata = _read_json(plugin) if os.path.isfile(plugin) else None
    if pdata and pdata.get("version") != mine:
        findings.append({"id": "VERSION_MISMATCH", "severity": "mention",
                         "message": f"SKILL.md says {mine}, plugin.json says {pdata.get('version')}",
                         "fix": "bump both in the same release"})
    for c in other_copies(os.path.abspath(root)):
        if c["same"]:
            continue
        findings.append({"id": "OTHER_COPY", "severity": "mention",
                         "message": f"{c['path']} holds telegram-bot-ui {c['version']} (this copy {mine}); a host "
                                    f"that reads that folder loads the other version",
                         "fix": "update or remove it (in a clone: py -3 scripts/install.py --host <host> --scope "
                                "<user|project>)"})
    meta = catalog_meta()
    if meta.get("fetched"):
        age = (_today() - dt.date.fromisoformat(meta["fetched"])).days
        if age > CATALOG_MAX_AGE_DAYS:
            findings.append({"id": "CATALOG_STALE", "severity": "route",
                             "message": f"Bot API catalog fetched {meta['fetched']} ({age} days ago)",
                             "fix": "tgui.py sync bot-api (network), then lookup version"})
    prj = Project(root)
    old = os.path.join(prj.root, "docs", "telegram-ui", "profile.json")
    if os.path.isfile(old) and not os.path.isfile(prj.path("profile.json")):
        findings.append({"id": "PROFILE_OLD_PATH", "severity": "auto",
                         "message": "style profile at docs/telegram-ui/profile.json",
                         "fix": "doctor --fix copies it to bot-ui/context/profile.json"})
    for name, schema in (("context.json", CONTEXT_SCHEMA), ("findings.json", FINDINGS_SCHEMA)):
        p = prj.path(name)
        if os.path.isfile(p):
            data = _read_json(p)
            if not isinstance(data, dict) or data.get("schema") != schema:
                findings.append({"id": "CONTEXT_SCHEMA", "severity": "mention",
                                 "message": f"bot-ui/context/{name} is not {schema}",
                                 "fix": "regenerate it (context --refresh) or fix it by hand"})
    state = prj.map_state() if prj.has_map else None
    if state and state.get("error"):
        findings.append({"id": "MAP_INVALID", "severity": "route",
                         "message": f"bot-ui map has {state['error']} validation error(s)",
                         "fix": "tgui.py map validate --project bot-ui"})
    return {"skill": {"version": mine, "path": SKILL, **meta}, "findings": findings}


def cmd_doctor(args) -> int:
    res = doctor(args.root)
    if args.fix:
        prj = Project(args.root)
        for f in res["findings"]:
            if f["id"] == "PROFILE_OLD_PATH":
                with open(os.path.join(prj.root, "docs", "telegram-ui", "profile.json"), encoding="utf-8") as fh:
                    text = fh.read()
                _sys_path()
                from bot_ui.context import write_text_inside
                write_text_inside(prj.root, "bot-ui/context/profile.json", text)
                f["fixed"] = True
    sk = res["skill"]
    text = [f"telegram-bot-ui {sk['version']} at {sk['path']} · Bot API {sk.get('botApi')} "
            f"(catalog {sk.get('fetched')})"]
    text += [f"[{f['severity']}] {f['id']}: {f['message']}\n    fix: {f['fix']}" for f in res["findings"]]
    if not res["findings"]:
        text.append("no problems found")
    _out(res, args.json, "\n".join(text))
    return 1 if any(not f.get("fixed") for f in res["findings"]) else 0


# ---------------------------------------------------------------- dispatch

def run_map(rest: list[str]) -> int:
    _sys_path()
    from bot_ui.cli import main as bot_ui_main
    return bot_ui_main(rest)


AGENT_BOOT = ("import runpy, sys; sys.path.insert(0, sys.argv.pop(1)); "
              "runpy.run_module('agent_bridge', run_name='__main__', alter_sys=True)")


def run_agent(rest: list[str]) -> int:
    """agent_bridge from the skill's library; -I keeps a same-named module in the user's folder out."""
    lib = os.path.join(SKILL, "examples", "python")
    return subprocess.call([sys.executable, "-I", "-c", AGENT_BOOT, lib, *rest])


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="tgui.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="group")

    def own(name, func, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--root", default=".", help="the bot's repository (default: current folder)")
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=func)
        return p

    p = own("context", cmd_context, "saved project context and signals")
    p.add_argument("--refresh", action="store_true", help="re-detect facts and write bot-ui/context/context.json")
    own("next", cmd_next, "the 2-3 best next commands")
    p = own("doctor", cmd_doctor, "health of the skill copy, catalog, context and map")
    p.add_argument("--fix", action="store_true", help="apply the `auto` fixes")
    p = own("findings", cmd_findings, "audit findings (bot-ui/context/findings.json)")
    p.add_argument("action", choices=("add", "close", "list"))
    p.add_argument("id", nargs="?")
    p.add_argument("--severity", choices=("P0", "P1", "P2", "P3"))
    p.add_argument("--screen")
    p.add_argument("--rule")
    p.add_argument("--where")
    p.add_argument("--summary")
    p.add_argument("--fix", default="improve", help="command that fixes it")
    p.add_argument("--status", default="fixed", choices=("fixed", "wontfix", "orphaned"))
    p.add_argument("--reason")
    p.add_argument("--open", action="store_true")
    p = own("requests", cmd_requests, "Studio requests (bot-ui/context/requests/)")
    p.add_argument("action", choices=("list", "add", "take", "done", "reject"))
    p.add_argument("id", nargs="?")
    p.add_argument("--screen")
    p.add_argument("--text")
    p.add_argument("--result")
    p.add_argument("--status", choices=("queued", "taken", "done", "rejected"))
    p = own("hook", cmd_hook, "post-edit check; install or remove the Claude Code hook")
    p.add_argument("action", choices=("post-edit", "install", "uninstall"))
    p.add_argument("--file")
    p.add_argument("--host", default="claude")
    p.add_argument("--dry-run", action="store_true")
    for name in (*PASS, *SUB, "map", "agent"):
        sub.add_parser(name, help=f"see `tgui.py {name} --help`", add_help=False)
    return ap


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    group, rest = argv[0], argv[1:]
    if group in PASS:
        return _run(PASS[group][0], rest)
    if group == "check" and rest[:1] == ["changed"]:
        ap = argparse.ArgumentParser(prog="tgui.py check changed")
        ap.add_argument("--root", default=".")
        ap.add_argument("--json", action="store_true")
        return cmd_check_changed(ap.parse_args(rest[1:]))
    if group in SUB:
        table = SUB[group]
        if not rest or rest[0] in ("-h", "--help"):
            print(f"usage: tgui.py {group} {{{'|'.join(table)}{'|changed' if group == 'check' else ''}}} ...")
            return 0 if rest else 2
        if rest[0] not in table:
            print(f"unknown {group} command {rest[0]!r}; one of: {', '.join(table)}", file=sys.stderr)
            return 2
        args = rest[1:]
        if group == "sync" and rest[0] == "webapp":
            args = ["sync", *args]
        return _run(table[rest[0]], args)
    if group == "map":
        return run_map(rest)
    if group == "agent":
        return run_agent(rest)
    args = parser().parse_args(argv)
    if not getattr(args, "func", None):
        print(__doc__)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
