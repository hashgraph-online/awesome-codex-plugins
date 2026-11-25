"""The one write path for the CLI, the Studio and patch import.

Invariants
* Every write names `expectedRevision`. Under a cross-process lock the snapshot is re-read;
  a different revision returns REVISION_CONFLICT with the fresh revision and per-field
  conflicts, and nothing is written.
* The future snapshot is validated first; an error blocks the write.
* A file is replaced atomically (temp file in the same folder + os.replace). Several files
  are written as a journaled transaction: originals are copied to .bot-ui/txn/, a journal
  lists them, then each file is replaced; an interrupted write is rolled back the next time
  the project is opened.
* An equivalent patch on the current revision changes no bytes and returns an empty diff.
"""
from __future__ import annotations

import copy
import difflib
import json
import os
import re
import shutil
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from . import PATCH_FORMAT
from .project import (STATE_DIR, Diagnostic, PathError, Snapshot, canonical_json, check_id, parse_files, read_files,
                      resolve_inside)
from .validate import targets, validate

LOCK_STALE_SECONDS = 30
LOCK_WAIT_SECONDS = 5

# Paths a patch may touch inside one screen document (JSON Pointer, RFC 6901 tokens).
_SEG = r"[a-z0-9][a-z0-9_-]*"
_LOC = r"[a-z]{2,3}(?:-[a-z0-9]{2,8})?"
ALLOWED_PATHS = [re.compile("^" + p + "$") for p in (
    r"/title", r"/kind", r"/audience", r"/notes",
    r"/message/format", rf"/message/text(/{_LOC})?", rf"/message/states/{_SEG}(/text(/{_LOC})?)?",
    r"/message/media", r"/message/media/(type|file|spoiler|emoji)",
    r"/keyboard", r"/keyboard/(type|rows|placeholder|resize|oneTime)", rf"/keyboard/placeholder/{_LOC}",
    rf"/actions/{_SEG}",
    rf"/actions/{_SEG}/(label|type|to|rule|presentation|set|handlerId|outcomes|pending|url|text|fallback|style|icon|hidden)",
    rf"/actions/{_SEG}/(label|text|pending)/{_LOC}",
    rf"/actions/{_SEG}/rule/(when|match|otherwise)", rf"/actions/{_SEG}/rule/when/(field|eq)",
    rf"/actions/{_SEG}/outcomes/{_SEG}", rf"/actions/{_SEG}/set/[a-z0-9_.-]+",
    r"/input", r"/input/(field|to)", r"/widget", r"/widget/(ref|caption)",
)]


WIDGET_FILE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*\.(html|css|js|json|svg)$")


def content_hash(data: bytes | None) -> str | None:
    if data is None:
        return None
    import hashlib
    return "sha256:" + hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


class StoreError(Exception):
    def __init__(self, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.code, self.message, self.extra = code, message, extra

    def to_json(self) -> dict:
        return {"code": self.code, "message": self.message, **self.extra}


@dataclass
class WriteResult:
    ok: bool
    revision: str
    previous_revision: str
    changed_files: list[str] = field(default_factory=list)
    diff: str = ""
    diagnostics: list[Diagnostic] = field(default_factory=list)
    dry_run: bool = False

    def to_json(self) -> dict:
        return {"ok": self.ok, "dryRun": self.dry_run, "revision": self.revision,
                "previousRevision": self.previous_revision, "changedFiles": self.changed_files,
                "diff": self.diff, "diagnostics": [d.to_json() for d in self.diagnostics]}


# ------------------------------------------------------------------ lock and journal

def _is_link(path: str) -> bool:
    return os.path.islink(path) or (hasattr(os.path, "isjunction") and os.path.isjunction(path))


def _state_dir(root: str) -> str:
    """<root>/.bot-ui, refused when a cloned project ships it as a link (every write goes through it)."""
    path = os.path.join(root, STATE_DIR)
    if _is_link(path):
        raise StoreError("STATE_DIR_LINK", f"{STATE_DIR} is a symbolic link or junction; remove it and retry")
    os.makedirs(path, exist_ok=True)
    gi = os.path.join(path, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("*\n")
    return path


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


@contextmanager
def write_lock(root: str, wait: float = LOCK_WAIT_SECONDS):
    path = os.path.join(_state_dir(root), "write.lock")
    deadline = time.monotonic() + wait
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, json.dumps({"pid": os.getpid(), "at": time.time()}).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                with open(path, encoding="utf-8") as fh:
                    info = json.load(fh)
                stale = time.time() - float(info.get("at", 0)) > LOCK_STALE_SECONDS or not _pid_alive(int(info.get("pid", 0)))
            except (OSError, ValueError):
                stale = time.time() - os.path.getmtime(path) > LOCK_STALE_SECONDS if os.path.exists(path) else True
            if stale:
                try:
                    os.remove(path)
                except OSError:
                    pass
                continue
            if time.monotonic() > deadline:
                raise StoreError("LOCKED", "another bot-ui process is writing this project; retry")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def recover_if_needed(root: str) -> int:
    """Roll back an interrupted transaction. Returns the number of restored files."""
    journal = os.path.join(root, STATE_DIR, "journal.json")
    if not os.path.exists(journal):
        return 0
    try:
        with open(journal, encoding="utf-8") as fh:
            entries = json.load(fh)["files"]
    except (ValueError, KeyError, TypeError):
        raise StoreError("JOURNAL_INVALID", f"{STATE_DIR}/journal.json is not a bot-ui journal; nothing was restored") from None
    # The journal is a file in the project: a cloned repository can carry a crafted one. Every
    # path is checked before anything moves: targets inside the project, backups only the
    # transaction's own <root>/.bot-ui/txn/<n>.bak, never a link.
    txn = os.path.realpath(os.path.join(root, STATE_DIR, "txn"))
    plan = []
    for e in entries if isinstance(entries, list) else [None]:
        if not isinstance(e, dict) or not isinstance(e.get("path"), str):
            raise StoreError("JOURNAL_INVALID", f"{STATE_DIR}/journal.json is not a bot-ui journal; nothing was restored")
        target = resolve_inside(root, e["path"])
        backup = e.get("backup")
        if backup is not None:
            name = os.path.basename(str(backup))
            safe = os.path.join(txn, name)
            if (not re.fullmatch(r"\d{1,6}\.bak", name) or os.path.realpath(str(backup)) != safe
                    or os.path.islink(safe) or not os.path.isfile(safe)):
                raise StoreError("JOURNAL_INVALID", f"{STATE_DIR}/journal.json names a backup outside "
                                                    f"{STATE_DIR}/txn/ ({backup!r}); nothing was restored")
            backup = safe
        plan.append((target, backup))
    for target, backup in plan:
        if backup is None:
            if os.path.exists(target):
                os.remove(target)
        else:
            os.replace(backup, target)
    os.remove(journal)
    shutil.rmtree(os.path.join(root, STATE_DIR, "txn"), ignore_errors=True)
    return len(entries)


def _atomic_write(path: str, data: bytes) -> None:
    """Write to a new, uniquely named file (exclusive create: never through a link or a hard link a
    cloned project planted next to the target), then atomically replace the target entry."""
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".bot-ui-tmp-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _commit(root: str, writes: dict[str, bytes | None], fail_after: int | None = None) -> None:
    """Write (bytes) or delete (None) files as one transaction. `fail_after` is a test hook."""
    sd = _state_dir(root)
    txn = os.path.join(sd, "txn")
    if _is_link(txn):
        raise StoreError("STATE_DIR_LINK", f"{STATE_DIR}/txn is a symbolic link or junction; remove it and retry")
    shutil.rmtree(txn, ignore_errors=True)   # start empty: a planted <n>.bak could be a hard link to another file
    os.makedirs(txn)
    entries = []
    for i, rel in enumerate(sorted(writes)):
        target = resolve_inside(root, rel)
        backup = None
        if os.path.exists(target):
            backup = os.path.join(txn, f"{i}.bak")
            shutil.copy2(target, backup)
        entries.append({"path": rel, "backup": backup})
    journal = os.path.join(sd, "journal.json")
    _atomic_write(journal, json.dumps({"files": entries}).encode())
    for n, rel in enumerate(sorted(writes)):
        if fail_after is not None and n >= fail_after:
            raise OSError("simulated failure during write")
        target = resolve_inside(root, rel)
        if writes[rel] is None:
            if os.path.exists(target):
                os.remove(target)
        else:
            _atomic_write(target, writes[rel])  # type: ignore[arg-type]
    os.remove(journal)
    shutil.rmtree(txn, ignore_errors=True)


# ------------------------------------------------------------------ JSON pointer

def _tokens(pointer: str) -> list[str]:
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer.split("/")[1:]]


def get_pointer(doc: Any, pointer: str) -> Any:
    cur = doc
    for t in _tokens(pointer):
        if isinstance(cur, dict) and t in cur:
            cur = cur[t]
        elif isinstance(cur, list) and t.isdigit() and int(t) < len(cur):
            cur = cur[int(t)]
        else:
            return _MISSING
    return cur


class _Missing:
    def __repr__(self) -> str:
        return "<missing>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Missing)

    def __hash__(self) -> int:
        return 0


_MISSING = _Missing()


def _set_pointer(doc: dict, pointer: str, value: Any, remove: bool = False) -> None:
    toks = _tokens(pointer)
    cur: Any = doc
    for t in toks[:-1]:
        if not isinstance(cur, dict):
            raise StoreError("PATCH_PATH_INVALID", f"{pointer}: parent is not an object")
        cur = cur.setdefault(t, {})
    if not isinstance(cur, dict):
        raise StoreError("PATCH_PATH_INVALID", f"{pointer}: parent is not an object")
    if remove:
        cur.pop(toks[-1], None)
    else:
        cur[toks[-1]] = value


# ------------------------------------------------------------------ patches

def check_patch_shape(patch: Any) -> None:
    if not isinstance(patch, dict) or patch.get("format") != PATCH_FORMAT:
        raise StoreError("PATCH_FORMAT", f"a patch is an object with format '{PATCH_FORMAT}'")
    if not isinstance(patch.get("baseRevision"), str):
        raise StoreError("PATCH_FORMAT", "the patch needs baseRevision")
    changes = patch.get("changes")
    if not isinstance(changes, list) or not changes:
        raise StoreError("PATCH_FORMAT", "the patch needs a non-empty changes list")
    for c in changes:
        if isinstance(c, dict) and "widgetId" in c:
            if check_id(c["widgetId"]) or not isinstance(c.get("file"), str) or not WIDGET_FILE_RE.match(c["file"]) \
                    or not isinstance(c.get("content"), str):
                raise StoreError("PATCH_FORMAT", "a widget change is {widgetId, file (name.html|css|js|json|svg), content}")
            if c["file"].endswith(".json"):
                try:
                    json.loads(c["content"])
                except json.JSONDecodeError as err:
                    raise StoreError("PATCH_FORMAT", f"widgets/{c['widgetId']}/{c['file']}: not valid JSON: {err}")
            continue
        if not isinstance(c, dict) or check_id(c.get("screenId")):
            raise StoreError("PATCH_FORMAT", f"change has an invalid screenId: {c!r}")
        if sum(k in c for k in ("ops", "create", "delete")) != 1:
            raise StoreError("PATCH_FORMAT", f"{c['screenId']}: a change has exactly one of ops, create or delete")
        for op in c.get("ops") or []:
            if not isinstance(op, dict) or op.get("op") not in ("set", "remove"):
                raise StoreError("PATCH_OP", f"{c['screenId']}: op must be set or remove")
            path = op.get("path")
            if not isinstance(path, str) or not any(p.match(path) for p in ALLOWED_PATHS):
                raise StoreError("PATCH_PATH_FORBIDDEN", f"{c['screenId']}: path {path!r} is not editable by a patch",
                                 hint="changing /id is a separate migration; see `bot-ui rename` (not in v1)")
            if op["op"] == "set" and "value" not in op:
                raise StoreError("PATCH_OP", f"{c['screenId']} {path}: set needs a value")


def apply_changes(snap: Snapshot, changes: list[dict]) -> tuple[dict[str, bytes | None], list[dict]]:
    """Future file bytes for each touched screen, and field conflicts against `from` values."""
    writes: dict[str, bytes | None] = {}
    conflicts: list[dict] = []
    created = {c["widgetId"] for c in changes if "widgetId" in c and c["file"] == "widget.json"}
    for c in changes:
        if "widgetId" in c:
            rel = f"widgets/{c['widgetId']}/{c['file']}"
            if c["widgetId"] not in snap.widgets and c["widgetId"] not in created:
                raise StoreError("WIDGET_NOT_FOUND", f"widget {c['widgetId']} does not exist")
            current = snap.files.get(rel)
            if "fromHash" in c and c["fromHash"] != content_hash(current):
                conflicts.append({"widgetId": c["widgetId"], "path": c["file"], "expected": c["fromHash"],
                                  "current": content_hash(current)})
            writes[rel] = c["content"].replace("\r\n", "\n").encode("utf-8")
            continue
        sid = c["screenId"]
        rel = snap.screen_path(sid)
        if "create" in c:
            if sid in snap.screens:
                raise StoreError("SCREEN_EXISTS", f"screen {sid} already exists")
            doc = copy.deepcopy(c["create"])
            if doc.get("id", sid) != sid:
                raise StoreError("PATCH_FORMAT", f"create: document id {doc.get('id')!r} differs from {sid}")
            doc["id"] = sid
            writes[f"screens/{sid}.json"] = canonical_json(doc, "screen")
            continue
        if sid not in snap.screens:
            raise StoreError("SCREEN_NOT_FOUND", f"screen {sid} does not exist", screenId=sid)
        if "delete" in c:
            incoming = [f"{other}/{aid}" for other, s in snap.screens.items() if other != sid
                        for aid, a in (s.get("actions") or {}).items()
                        if isinstance(a, dict) and sid in [t for _, t in targets(a)]]
            incoming += [f"entry:{ep.get('id')}" for ep in (snap.project or {}).get("entryPoints") or []
                         if ep.get("screen") == sid]
            if incoming:
                raise StoreError("SCREEN_HAS_INCOMING", f"{sid} is referenced by {', '.join(incoming)}",
                                 incoming=incoming)
            writes[rel] = None
            continue
        doc = copy.deepcopy(snap.screens[sid])
        for op in c["ops"]:
            if "from" in op:
                current = get_pointer(snap.screens[sid], op["path"])
                expected = _MISSING if op["from"] is None and current is _MISSING else op["from"]
                if current != expected:
                    conflicts.append({"screenId": sid, "path": op["path"], "expected": op["from"],
                                      "current": None if current is _MISSING else current})
            _set_pointer(doc, op["path"], op.get("value"), remove=op["op"] == "remove")
        writes[rel] = canonical_json(doc, "screen")
    return writes, conflicts


def unified(rel: str, before: bytes | None, after: bytes | None) -> str:
    a = (before or b"").decode("utf-8").splitlines(keepends=True)
    b = (after or b"").decode("utf-8").splitlines(keepends=True)
    return "".join(difflib.unified_diff(a, b, f"a/{rel}" if before is not None else "/dev/null",
                                        f"b/{rel}" if after is not None else "/dev/null"))


def write_patch(root: str, patch: dict, *, dry_run: bool = False, rebase: bool = False,
                _fail_after: int | None = None) -> WriteResult:
    """Validate and apply a bot-ui-patch/v1 document. Raises StoreError on refusal."""
    check_patch_shape(patch)
    from .project import open_snapshot

    def plan(snap: Snapshot):
        if snap.read_only:
            raise StoreError("READ_ONLY", "this project version opens read-only; migrate it first")
        if patch.get("projectId") not in (None, (snap.project or {}).get("projectId")):
            raise StoreError("PROJECT_MISMATCH", f"patch is for {patch.get('projectId')!r}, "
                                                 f"this project is {(snap.project or {}).get('projectId')!r}")
        writes, conflicts = apply_changes(snap, patch["changes"])
        writes = {rel: data for rel, data in writes.items() if snap.files.get(rel) != data}
        return writes, conflicts

    def future(snap: Snapshot, writes: dict[str, bytes | None]) -> Snapshot:
        files = dict(snap.files)
        for rel, data in writes.items():
            if data is None:
                files.pop(rel, None)
            else:
                files[rel] = data
        return parse_files(root, files)

    with write_lock(root) if not dry_run else _nullcontext():
        snap = open_snapshot(root)  # read under the lock: the revision check and the write see one state
        writes, conflicts = plan(snap)
        if snap.revision != patch["baseRevision"]:
            if not (rebase and not conflicts):
                raise StoreError("REVISION_CONFLICT", "the project changed since the patch was made",
                                 expectedRevision=patch["baseRevision"], currentRevision=snap.revision,
                                 fieldConflicts=conflicts,
                                 howToDiff="git diff -- <project> ; bot-ui show <screenId> --json",
                                 retry="re-read, rebuild the patch on currentRevision, or pass --rebase "
                                       "when fieldConflicts is empty")
        nxt = future(snap, writes)
        diags = validate(nxt)
        errors = [d for d in diags if d.severity == "error"]
        diff = "".join(unified(rel, snap.files.get(rel), writes[rel]) for rel in sorted(writes))
        res = WriteResult(ok=not errors, revision=nxt.revision, previous_revision=snap.revision,
                          changed_files=sorted(writes), diff=diff, diagnostics=diags, dry_run=dry_run)
        if errors:
            res.revision = snap.revision
            raise StoreError("VALIDATION_FAILED", f"{len(errors)} error(s) in the resulting project; nothing written",
                             diagnostics=[d.to_json() for d in errors], diff=diff)
        if dry_run or not writes:
            return res
        for rel in writes:
            resolve_inside(root, rel)  # path checks before any byte is replaced
        try:
            _commit(root, writes, fail_after=_fail_after)
        except OSError as err:
            recover_if_needed(root)
            raise StoreError("WRITE_FAILED", f"write failed and was rolled back: {err}")
        res.revision = open_snapshot(root).revision
        return res


@contextmanager
def _nullcontext():
    yield


def screen_patch(snap: Snapshot, sid: str, new_doc: dict) -> dict:
    """A patch that turns the current screen into `new_doc` (top-level key granularity, with from)."""
    old = snap.screens.get(sid)
    if old is None:
        return {"format": PATCH_FORMAT, "projectId": (snap.project or {}).get("projectId"),
                "baseRevision": snap.revision, "changes": [{"screenId": sid, "create": new_doc}]}
    ops = []
    _diff_ops(old, new_doc, "", ops)
    return {"format": PATCH_FORMAT, "projectId": (snap.project or {}).get("projectId"),
            "baseRevision": snap.revision, "changes": [{"screenId": sid, "ops": ops}]}


def _diff_ops(old: Any, new: Any, path: str, ops: list[dict]) -> None:
    """Smallest allowed ops: recurse while a deeper allowed path exists, else replace the value."""
    if old == new:
        return
    if path and not (isinstance(old, dict) and isinstance(new, dict) and _has_child_paths(path)):
        ops.append({"op": "set", "path": path, "value": new, "from": old})
        return
    for k in list(old) + [k for k in new if k not in old]:
        p = f"{path}/{k.replace('~', '~0').replace('/', '~1')}"
        if k not in new:
            ops.append({"op": "remove", "path": p, "from": old[k]})
        elif k not in old:
            ops.append({"op": "set", "path": p, "value": new[k], "from": None})
        else:
            _diff_ops(old[k], new[k], p, ops)


def _has_child_paths(p: str) -> bool:
    """True when some allowed pattern accepts p plus one more segment."""
    probes = ("ru", "en", "when", "field", "eq", "text", "match", "otherwise", "rows", "type", "label", "x", "a1")
    return any(rx.match(f"{p}/{t}") for rx in ALLOWED_PATHS for t in probes)


def load_patch(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as err:
        raise StoreError("PATCH_UNREADABLE", f"cannot read patch {path}: {err}")


__all__ = ["StoreError", "WriteResult", "write_patch", "screen_patch", "check_patch_shape", "recover_if_needed",
           "write_lock", "PathError"]
