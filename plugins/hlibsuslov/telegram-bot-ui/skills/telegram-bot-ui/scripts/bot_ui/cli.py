"""bot-ui command line. JSON on stdout with --json; diagnostics for humans go to stderr.

Exit codes: 0 ok · 1 validation errors / failed scenario · 2 usage · 3 revision conflict ·
4 refused (path, lock, read-only, stale build) or I/O error.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import uuid

from . import PATCH_FORMAT, SCHEMA_VERSION, TOOL_VERSION
from .engine import parity_view, run_scenario
from .project import Snapshot, find_root, open_snapshot, replace_dir
from .render import bot_request, render_screen
from .store import StoreError, load_patch, write_patch
from .validate import summary, targets, validate

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "templates")
EXIT = {"REVISION_CONFLICT": 3, "VALIDATION_FAILED": 1}
KEEP_ON_INIT = ("context",)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def _emit(args, payload: dict, human: str | None = None) -> None:
    if args.json:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    elif human is not None:
        sys.stdout.write(human.rstrip("\n") + "\n")


def _fail(args, code: str, message: str, exit_code: int | None = None, **extra) -> int:
    err = {"code": code, "message": message, **extra}
    if args.json:
        sys.stdout.write(json.dumps({"ok": False, "error": err}, ensure_ascii=False, indent=2) + "\n")
    print(f"error [{code}]: {message}", file=sys.stderr)
    for d in extra.get("diagnostics") or []:
        print(f"  {d['severity']} {d['code']} {d['file']}{d['pointer']}: {d['message']}", file=sys.stderr)
    for c in extra.get("fieldConflicts") or []:
        print(f"  conflict {c['screenId']} {c['path']}: expected {c['expected']!r}, now {c['current']!r}", file=sys.stderr)
    return exit_code if exit_code is not None else EXIT.get(code, 4)


def _root(args) -> str:
    root = args.project or find_root(os.getcwd())
    if not root or not os.path.isfile(os.path.join(root, "project.json")):
        raise SystemExit(_fail(args, "PROJECT_NOT_FOUND", f"no project.json at {args.project or os.getcwd()}", 2))
    return os.path.abspath(root)


def _diag_lines(diags) -> str:
    return "\n".join(f"{d.severity:7} {d.code:28} {d.file}{d.pointer}  {d.message}" for d in diags)


# ------------------------------------------------------------------ commands

def cmd_init(args) -> int:
    target = os.path.abspath(args.project)
    src = os.path.join(TEMPLATES, args.template)
    if not os.path.isdir(src):
        return _fail(args, "TEMPLATE_UNKNOWN", f"no template {args.template!r} (have: {', '.join(sorted(os.listdir(TEMPLATES)))})", 2)
    # The skill's saved review (context/) may exist before the map; init keeps it.
    existing = os.listdir(target) if os.path.isdir(target) else []
    if os.path.exists(target) and [n for n in existing if n not in KEEP_ON_INIT]:
        return _fail(args, "TARGET_NOT_EMPTY", f"{target} exists and is not empty; init never overwrites", 4)
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)
    stage = os.path.join(parent, f".{os.path.basename(target)}.bot-ui-init-{uuid.uuid4().hex[:8]}")
    shutil.copytree(src, stage)
    snap = open_snapshot(stage)
    errors = [d for d in validate(snap) if d.severity == "error"]
    if errors:
        shutil.rmtree(stage, ignore_errors=True)
        return _fail(args, "TEMPLATE_INVALID", "the template does not validate", 1, diagnostics=[d.to_json() for d in errors])
    shutil.rmtree(os.path.join(stage, ".bot-ui"), ignore_errors=True)
    moved: list[str] = []
    try:
        if os.path.exists(target):
            for name in existing:
                os.replace(os.path.join(target, name), os.path.join(stage, name))
                moved.append(name)
            os.rmdir(target)
        replace_dir(stage, target)
    except OSError as err:  # the saved review must survive a failed publish
        os.makedirs(target, exist_ok=True)
        for name in moved:
            kept = os.path.join(stage, name)
            if os.path.lexists(kept) and not os.path.lexists(os.path.join(target, name)):
                os.replace(kept, os.path.join(target, name))
        shutil.rmtree(stage, ignore_errors=True)
        return _fail(args, "INIT_FAILED", f"could not publish {target}: {err}; its saved files are back in place", 4)
    _emit(args, {"ok": True, "project": target, "projectId": snap.project["projectId"], "revision": snap.revision,
                 "files": sorted(snap.files)},
          f"created {target} ({len(snap.files)} files), revision {snap.revision}")
    return 0


def _screen_row(snap: Snapshot, sid: str) -> dict:
    s = snap.screens[sid]
    entries = [ep.get("id") for ep in (snap.project or {}).get("entryPoints") or [] if ep.get("screen") == sid]
    return {"id": sid, "title": s.get("title"), "kind": s.get("kind"), "file": snap.screen_path(sid),
            "actions": list((s.get("actions") or {}).keys()), "entryPoints": entries}


def cmd_list(args) -> int:
    snap = open_snapshot(_root(args))
    rows = [_screen_row(snap, sid) for sid in sorted(snap.screens)]
    if args.filter:
        q = args.filter.lower()
        rows = [r for r in rows if q in r["id"] or q in str(r["title"]).lower() or q == r["kind"]]
    _emit(args, {"ok": True, "revision": snap.revision, "projectId": (snap.project or {}).get("projectId"),
                 "screens": rows, "widgets": sorted(snap.widgets), "scenarios": sorted(snap.scenarios)},
          "\n".join(f"{r['id']:32} {r['kind'] or '':13} {r['title'] or ''}" for r in rows))
    return 0


def links(snap: Snapshot, sid: str) -> tuple[list[dict], list[dict]]:
    incoming, outgoing = [], []
    for other, s in snap.screens.items():
        for aid, a in (s.get("actions") or {}).items():
            if not isinstance(a, dict):
                continue
            for via, t in targets(a):
                if other == sid:
                    outgoing.append({"actionId": aid, "via": via, "to": t})
                if t == sid:
                    incoming.append({"screenId": other, "actionId": aid, "via": via})
        inp = s.get("input")
        if isinstance(inp, dict):
            if other == sid and inp.get("to"):
                outgoing.append({"actionId": None, "via": "input", "to": inp["to"]})
            if inp.get("to") == sid:
                incoming.append({"screenId": other, "actionId": None, "via": "input"})
    for ep in (snap.project or {}).get("entryPoints") or []:
        if ep.get("screen") == sid:
            incoming.append({"entryPoint": ep.get("id"), "type": ep.get("type")})
    return incoming, outgoing


def cmd_show(args) -> int:
    snap = open_snapshot(_root(args))
    sid = args.screen_id
    if sid not in snap.screens:
        close = [s for s in snap.screens if sid in s]
        return _fail(args, "SCREEN_NOT_FOUND", f"no screen with ID exactly {sid!r}", 1, similar=close)
    incoming, outgoing = links(snap, sid)
    p = snap.project or {}
    rendered = {loc: render_screen(p, snap.screens[sid], locale=loc, values=_examples(p)) for loc in p.get("locales") or []}
    diags = [d.to_json() for d in validate(snap) if d.screenId == sid]
    payload = {"ok": True, "revision": snap.revision, "file": snap.screen_path(sid), "screen": snap.screens[sid],
               "incoming": incoming, "outgoing": outgoing, "render": rendered, "diagnostics": diags}
    human = [f"{sid}  ({snap.screen_path(sid)}, revision {snap.revision[:19]})"]
    for loc, r in rendered.items():
        human.append(f"[{loc}] {r['text']}")
        for row in r["keyboard"]["rows"]:
            human.append("   " + " | ".join(f"[{b['text']}]" for b in row))
    human.append("in:  " + ", ".join(str(i.get("screenId") or "entry:" + str(i.get("entryPoint"))) for i in incoming))
    human.append("out: " + ", ".join(f"{o['actionId']}->{o['to']}" for o in outgoing))
    _emit(args, payload, "\n".join(human))
    return 0


def _examples(p: dict) -> dict:
    return {k: f.get("example") for k, f in (p.get("fields") or {}).items() if isinstance(f, dict) and "example" in f}


def cmd_validate(args) -> int:
    snap = open_snapshot(_root(args))
    diags = validate(snap)
    counts = summary(diags)
    _emit(args, {"ok": counts["error"] == 0, "revision": snap.revision, "readOnly": snap.read_only, "summary": counts,
                 "diagnostics": [d.to_json() for d in diags]},
          (_diag_lines(diags) + "\n" if diags else "") +
          f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['info']} info · revision {snap.revision}")
    return 0 if counts["error"] == 0 else 1


def _write(args, patch: dict) -> int:
    try:
        res = write_patch(_root(args), patch, dry_run=args.dry_run, rebase=getattr(args, "rebase", False))
    except StoreError as err:
        return _fail(args, err.code, err.message, **err.extra)
    out = res.to_json()
    human = (res.diff or "(no change: the project already has this content)") + \
        f"\n{'dry run, nothing written' if res.dry_run else 'written'} · revision {res.revision}"
    _emit(args, out, human)
    return 0


def cmd_patch(args) -> int:
    doc = load_patch(args.patch_file) if args.patch_file != "-" else json.load(sys.stdin)
    if isinstance(doc, dict) and doc.get("format") == PATCH_FORMAT:
        ids = {c.get("screenId") for c in doc.get("changes") or []}
        if ids != {args.screen_id}:
            return _fail(args, "PATCH_SCOPE", f"the patch touches {sorted(ids)}, not only {args.screen_id}; use apply-patch", 2)
        patch = doc
        if args.expected_revision:
            patch["baseRevision"] = args.expected_revision
    else:
        ops = doc.get("ops") if isinstance(doc, dict) else doc
        if not args.expected_revision:
            return _fail(args, "EXPECTED_REVISION_REQUIRED", "pass --expected-revision (from `bot-ui show --json`)", 2)
        patch = {"format": PATCH_FORMAT, "baseRevision": args.expected_revision,
                 "changes": [{"screenId": args.screen_id, "ops": ops}]}
    return _write(args, patch)


def cmd_set(args) -> int:
    value = json.loads(args.value) if args.json_value else args.value
    patch = {"format": PATCH_FORMAT, "baseRevision": args.expected_revision,
             "changes": [{"screenId": args.screen_id,
                          "ops": [{"op": "set", "path": "/" + args.path.lstrip("/"), "value": value}]}]}
    return _write(args, patch)


def cmd_apply_patch(args) -> int:
    return _write(args, load_patch(args.patch_file))


def cmd_simulate(args) -> int:
    snap = open_snapshot(_root(args))
    names = sorted(snap.scenarios) if args.all else [args.scenario]
    overrides = {"context": dict(kv.split("=", 1) for kv in args.context or [])}
    if args.locale:
        overrides["locale"] = args.locale
    results = []
    for name in names:
        if name not in snap.scenarios:
            return _fail(args, "SCENARIO_NOT_FOUND", f"no scenario {name!r} (have: {', '.join(sorted(snap.scenarios))})", 2)
        r = run_scenario(snap, snap.scenarios[name], overrides=overrides)
        results.append(parity_view(r) if args.parity else r)
    ok = all(r["ok"] for r in results)
    lines = []
    for r in results:
        lines.append(f"== {r['scenarioId']}: {'ok' if r['ok'] else 'FAILED'} (simulated, local; not Telegram)")
        for e in r.get("trace") or r.get("steps"):
            if e["update"].get("type") == "local" and not e["diagnostics"]:
                continue
            tr = e["transition"]
            effs = ", ".join(_eff(x) for x in e["effects"])
            what = f"{e['action']['screenId']}/{e['action']['actionId']} " if e["action"] else ""
            via = f" -> {tr['to']} ({tr['via']})" if tr else ""
            lines.append(f"{e['step']:3} {_upd(e['update'])} {what}{via}  [{effs}]")
            for d in e["diagnostics"]:
                lines.append(f"      ! {d['code'] if isinstance(d, dict) else d}: {d.get('message', '') if isinstance(d, dict) else ''}")
    payload = results[0] if len(results) == 1 and not args.all else {"ok": ok, "results": results}
    _emit(args, payload, "\n".join(lines))
    return 0 if ok else 1


def _upd(u: dict) -> str:
    if u["type"] == "message":
        return f"text {u['text']!r}"
    if u["type"] == "callback_query":
        return f"press {u['actionId']}" + (f"@{u['message']}" if "message" in u else "")
    if u["type"] == "event":
        return f"event {u['eventKey']}"
    return "local " + json.dumps({k: v for k, v in u.items() if k != "type"}, ensure_ascii=False)


def _eff(x: dict) -> str:
    t = x["type"]
    if t in ("send", "edit"):
        return f"{t} #{x['instance']} {x['view']['screenId']}" + (f"<{x['view']['state']}>" if x["view"].get("state") else "")
    if t == "answer":
        return "answer" + (f" {x['text']!r}" if x.get("text") else "")
    if t == "fallback":
        return f"fallback {x['reason']}"
    if t == "link":
        return f"link {x['url']}"
    return f"{t} {x.get('reason', '')}"


def cmd_render(args) -> int:
    snap = open_snapshot(_root(args))
    if args.screen_id not in snap.screens:
        return _fail(args, "SCREEN_NOT_FOUND", f"no screen {args.screen_id!r}", 1)
    p = snap.project or {}
    values = _examples(p)
    values.update(dict(kv.split("=", 1) for kv in args.value or []))
    logical = render_screen(p, snap.screens[args.screen_id], locale=args.locale, state=args.state, values=values)
    req = bot_request(logical, args.chat_id, edit_message_id=args.edit)
    vp = __import__("bot_ui.skill", fromlist=["load"]).load("validate_payload")
    rep = vp.Validator(vp.load_catalog(vp.DATA_DIR)).check_request(req["method"], req["params"])
    _emit(args, {"ok": rep.ok, "revision": snap.revision, "request": req, "payloadErrors": rep.errors,
                 "status": "static"}, json.dumps(req, ensure_ascii=False, indent=2))
    return 0 if rep.ok else 1


def cmd_build(args) -> int:
    from . import widgets
    snap = open_snapshot(_root(args))
    out = os.path.abspath(args.output) if args.output else os.path.join(snap.root, ".bot-ui", "build")
    os.makedirs(out, exist_ok=True)
    p = snap.project or {}
    reports, ok = [], True
    for wid in sorted(snap.widgets):
        if args.widget and wid != args.widget:
            continue
        for lang in snap.widgets[wid].get("languages") or [p.get("defaultLocale", "en")]:
            b = widgets.build(snap, wid, lang=lang, values=_examples(p))
            ok &= b["ok"]
            rep = {k: v for k, v in b.items() if k != "html"}
            if b["ok"]:
                with open(os.path.join(out, f"{wid}.{lang}.html"), "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(b["html"])
                with open(os.path.join(out, f"{wid}.{lang}.payload.json"), "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(widgets.payload(snap, wid, b), fh, ensure_ascii=False, indent=2)
            reports.append(rep)
    _emit(args, {"ok": ok, "revision": snap.revision, "output": out, "widgets": reports},
          "\n".join(f"{r['widget']} [{r['lang']}] {'ok' if r['ok'] else 'FAILED'}: "
                    f"{r['rawBytes']} B raw / {r['compressedBytes']} B zlib-9 (limits {r['limits']['rawBytes']} / "
                    f"{r['limits']['compressedBytes']})" + "".join(f"\n   ! {e}" for e in r["errors"]) for r in reports)
          + f"\noutput: {out}")
    return 0 if ok else 1


def cmd_studio(args) -> int:
    from .server import serve
    return serve(_root(args), host="127.0.0.1", port=args.port, open_screen=args.screen, open_browser=args.open,
                 emoji_library_file=args.emoji_library_file)


def cmd_export_snapshot(args) -> int:
    from .artifact import build_artifact, snapshot_document
    from .emoji import EmojiError
    snap = open_snapshot(_root(args))
    try:
        if args.format == "json":
            doc = snapshot_document(snap, screens=args.screen, emoji_previews=args.emoji_previews,
                                    emoji_budget=args.emoji_budget, emoji_library_file=args.emoji_library_file)
            with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False, indent=2)
        else:
            build_artifact(snap, args.output, screens=args.screen, emoji_library_file=args.emoji_library_file)
    except RuntimeError as err:
        return _fail(args, "ARTIFACT_BUILD", str(err), 4)
    except EmojiError as err:
        return _fail(args, err.code, err.message, 4)
    _emit(args, {"ok": True, "output": os.path.abspath(args.output), "baseRevision": snap.revision},
          f"wrote {os.path.abspath(args.output)} (baseRevision {snap.revision})")
    return 0


def cmd_inventory(args) -> int:
    from .inventory import scan
    if not os.path.isdir(args.source):
        return _fail(args, "SOURCE_NOT_FOUND", f"{args.source} is not a folder", 2)
    inv = scan(args.source)
    lines = [f"{len(inv['entryPoints'])} command(s), {len(inv['callbacks'])} callback handler(s), "
             f"{len(inv['buttons'])} button(s), {len(inv['dynamic'])} dynamic place(s) (static analysis, read-only)"]
    for sc in inv["proposedScreens"]:
        lines.append(f"  {sc['id']:32} {sc['confidence']:6} {sc['sourceHandler']}")
    for d in inv["dynamic"]:
        lines.append(f"  ? {d['file']}:{d['line']} {d['what']}")
    _emit(args, {"ok": True, **inv}, chr(10).join(lines))
    return 0


def cmd_import(args) -> int:
    from .importer import import_bot, report_markdown
    from .store import StoreError
    if not os.path.isdir(args.source):
        return _fail(args, "SOURCE_NOT_FOUND", f"{args.source} is not a folder", 2)
    into = args.into or os.path.join(args.source, "bot-ui")
    try:
        probe = import_bot(args.source, into, project_id=args.project_id, dry_run=True)
        if not (probe.get("stats") or {}).get("handlers"):
            return _fail(args, "NO_HANDLERS_FOUND",
                         "no aiogram router handlers (@router.message / @router.callback_query with filters) were "
                         "found, so nothing was created. This bot routes updates in its own code: connect it "
                         "with the skill's existing-bot route (references/bot-ui-projects.md) - the agent maps "
                         "its views and texts to screens one route at a time, keeping its callback_data.", 1,
                         files=(probe.get("stats") or {}).get("files"))
        res = probe if args.dry_run else import_bot(args.source, into, project_id=args.project_id, dry_run=False)
    except StoreError as err:
        return _fail(args, err.code, err.message, **err.extra)
    text = report_markdown(res)
    if args.emoji_packs and not args.dry_run and res["stats"].get("customEmoji"):
        from . import emoji
        try:
            used = emoji.import_used(into, open_snapshot(into))
            res["emojiPacks"] = used
            text += "\n\nemoji packs: " + emoji.import_used_markdown(used)
        except emoji.EmojiError as err:
            res["emojiPacks"] = {"ok": False, "error": err.to_json()}
            text += f"\n\nemoji packs not imported: {err.code} {err.message}"
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
    _emit(args, res, text + ("" if args.dry_run else f"\nproject: {res['project']}"))
    return 1 if res.get("errors") else 0


def cmd_emoji(args) -> int:
    from . import emoji
    root = _root(args)
    try:
        if args.action == "import":
            sticker_set = None
            if args.from_json:
                with open(args.from_json, encoding="utf-8") as fh:
                    sticker_set = json.load(fh)
            elif not args.link:
                return _fail(args, "USAGE", "emoji import <pack link or name> | --from-json saved-getStickerSet.json", 2)
            res = emoji.import_pack(root, link=args.link, sticker_set=sticker_set)
            _emit(args, res, f"{res['title']} ({res['pack']}): {res['count']} emoji, {res['previews']} previews "
                             f"-> {emoji.LIBRARY}")
            return 0
        if args.action == "import-used":
            res = emoji.import_used(root, open_snapshot(root), map_icons=not args.no_icon_map)
            _emit(args, res, emoji.import_used_markdown(res))
            return 1 if res["failed"] else 0
        if args.action == "remove":
            if not args.link:
                return _fail(args, "USAGE", "emoji remove <pack name>", 2)
            res = emoji.remove_pack(root, args.link)
            _emit(args, res, f"removed {res['removed']}" + (f"; icons kept: {', '.join(res['iconsKept'])}" if res["iconsKept"] else ""))
            return 0
        if args.action == "icon":
            if not args.slot:
                return _fail(args, "USAGE", "emoji icon --slot <meaning> [--id <custom emoji id> | --clear]", 2)
            res = emoji.set_icon(root, args.slot, None if args.clear else args.id, note=args.note, fallback=args.fallback)
            _emit(args, res, f"{args.slot}: {'cleared' if args.clear else args.id}")
            return 0
        snap = open_snapshot(root)
        lib = emoji.load_library(root)
        if args.action == "list":
            _emit(args, {"ok": True, "library": lib, "previews": emoji.previews(root)},
                  "\n".join(f"{n}: {p.get('title')} · {len(p.get('emoji') or [])} emoji · {p.get('link')}"
                            for n, p in lib["packs"].items()) or "no packs: bot-ui emoji import https://t.me/addemoji/<name>")
            return 0
        if args.action == "review":
            out = args.out or "icon-review.html"
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(emoji.review_sheet(snap, lib))
            idx = emoji.emoji_index(lib)
            issues = emoji.meaning_issues(snap, lib)
            moving = [b for b in emoji.button_icons(snap) if emoji.is_moving(idx.get(b["id"]))]
            _emit(args, {"ok": not issues and not moving, "file": out, "meaningMismatch": issues,
                         "animatedOnButtons": moving},
                  f"{out}: open it and look at every row; {len(issues)} meaning mismatch(es), "
                  f"{len(moving)} animated button icon(s)")
            return 1 if issues or moving else 0
        b = emoji.brief(snap, lib)
        _emit(args, {"ok": True, **b}, emoji.brief_markdown(b))
        return 0
    except emoji.EmojiError as err:
        return _fail(args, err.code, err.message, 2 if err.code in ("PACK_LINK", "SLOT_INVALID", "EMOJI_INVALID") else 4)
    except (OSError, ValueError) as err:
        return _fail(args, "IO_ERROR", str(err))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bot-ui", description=f"bot-ui {TOOL_VERSION} (project schemaVersion {SCHEMA_VERSION})")
    ap.add_argument("--version", action="version", version=f"bot-ui {TOOL_VERSION} schema {SCHEMA_VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--project", help="project root (folder with project.json); default: search from cwd")
        p.add_argument("--json", action="store_true", help="stable JSON on stdout")
        p.set_defaults(fn=fn)
        return p

    p = add("init", cmd_init, "create a project from a template (never overwrites)")
    p.add_argument("--template", default="checkout")
    p = add("list", cmd_list, "list screens")
    p.add_argument("--filter")
    p = add("show", cmd_show, "one screen by exact ID, its links and rendering")
    p.add_argument("screen_id")
    add("validate", cmd_validate, "validate the whole project")
    p = add("patch", cmd_patch, "apply ops to one screen with a revision check")
    p.add_argument("screen_id")
    p.add_argument("--patch-file", required=True)
    p.add_argument("--expected-revision")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--rebase", action="store_true", help="apply on a newer revision when no field conflicts")
    p = add("set", cmd_set, "set one allowed path of a screen")
    p.add_argument("screen_id")
    p.add_argument("path", help="JSON pointer, e.g. /message/text/ru")
    p.add_argument("value")
    p.add_argument("--json-value", action="store_true", help="parse value as JSON")
    p.add_argument("--expected-revision", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--rebase", action="store_true")
    p = add("apply-patch", cmd_apply_patch, "apply a bot-ui-patch/v1 file (from the Studio or the artifact)")
    p.add_argument("--patch-file", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--rebase", action="store_true")
    p = add("simulate", cmd_simulate, "replay scenario fixtures (local, no Telegram)")
    p.add_argument("--scenario")
    p.add_argument("--all", action="store_true")
    p.add_argument("--locale")
    p.add_argument("--context", action="append", metavar="FIELD=VALUE")
    p.add_argument("--parity", action="store_true", help="only the fields both engines must agree on")
    p = add("render", cmd_render, "Bot API request of one screen, structurally checked")
    p.add_argument("screen_id")
    p.add_argument("--locale")
    p.add_argument("--state")
    p.add_argument("--chat-id", default=111111111, type=int)
    p.add_argument("--edit", type=int, help="render as editMessageText of this message_id")
    p.add_argument("--value", action="append", metavar="FIELD=VALUE")
    p = add("build", cmd_build, "build widgets (default output: <project>/.bot-ui/build)")
    p.add_argument("--output")
    p.add_argument("--widget")
    p = add("studio", cmd_studio, "local Studio on http://127.0.0.1")
    p.add_argument("--port", type=int, default=0, help="0 = a free port")
    p.add_argument("--screen", help="open this screen ID")
    p.add_argument("--open", action="store_true", help="open the browser")
    p.add_argument("--emoji-library-file", help="the emoji library's offline export (emoji-library.ndjson.gz): the Emoji "
                                                "page filters and picks packs from it instead of the network")
    p = add("export-snapshot", cmd_export_snapshot, "interactive artifact (HTML) or snapshot JSON for a host without a port")
    p.add_argument("--output", required=True)
    p.add_argument("--format", choices=("html", "json"), default="html")
    p.add_argument("--screen", action="append", help="only these screens (default: all)")
    p.add_argument("--emoji-previews", choices=("used", "all"), default="used",
                   help="json: inline pictures of the used emoji only (default) or of every imported pack")
    p.add_argument("--emoji-budget", type=int, default=1_500_000, help="json: bytes of inlined emoji pictures")
    p.add_argument("--emoji-library-file", help="embed the emoji library's catalog from this offline export "
                                                "(default: the one the Studio last loaded, if any)")
    p = add("emoji", cmd_emoji, "premium emoji library: import a pack by link, map icons to meanings, the agent's brief")
    p.add_argument("action", choices=("import", "import-used", "list", "icon", "remove", "brief", "review"),
                   help="import-used: import every pack the bot's screens and code already use; review: an HTML sheet "
                        "of every button icon next to its label (meaning, static, family) to look at before shipping")
    p.add_argument("--out", help="review: where to write the HTML sheet (default icon-review.html)")
    p.add_argument("link", nargs="?", help="import: https://t.me/addemoji/<name> or the name; remove: the pack name")
    p.add_argument("--from-json", help="import a saved getStickerSet response (offline, no previews)")
    p.add_argument("--slot", help="icon: the meaning, e.g. home, back, cart")
    p.add_argument("--id", help="icon: the custom emoji id")
    p.add_argument("--clear", action="store_true", help="icon: remove the slot")
    p.add_argument("--note", help="icon: where to use it")
    p.add_argument("--fallback", help="icon: the ordinary emoji, for an id not in an imported pack")
    p.add_argument("--no-icon-map", action="store_true", help="import-used: do not adopt the button icons into the icon map")
    p = sub.add_parser("import", help="build a bot-ui project from an existing aiogram bot (the bot's code is not changed)")
    p.add_argument("--source", required=True, help="the bot's source folder")
    p.add_argument("--into", help="project folder to create (default: <source>/bot-ui); an existing project is re-imported")
    p.add_argument("--project-id")
    p.add_argument("--report", help="also write the review list as Markdown here")
    p.add_argument("--emoji-packs", action="store_true",
                   help="also import the premium emoji packs the bot uses (online: the resolver or a bot token)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_import, project=None)
    p = sub.add_parser("inventory", help="read-only inventory of an existing aiogram bot (proposed screens)")
    p.add_argument("--source", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_inventory, project=None)
    args = ap.parse_args(argv)
    if not hasattr(args, "dry_run"):
        args.dry_run = False
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
