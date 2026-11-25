"""The saved review next to the map: bot-ui/context/ (outside the map revision).

Shared by the Studio server and tgui.py so both write the same files the same safe way:
  context/requests/<id>.json   bot-ui-request/v1: {id, sid, text, at, baseRevision, status, result}
Status: queued -> taken -> done | rejected (a request removed in the Studio while still queued
becomes rejected). Every write resolves its path inside the project without following links or
junctions, goes through an exclusive temporary file and an atomic replace, and a status change
holds a per-request lock, so two agents cannot both take one request. Standard library only.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager

from .project import ID_RE, PathError, resolve_inside

REQUEST_SCHEMA = "bot-ui-request/v1"
REQUEST_ID = re.compile(r"^rq-[0-9a-f]{6,40}$")
MAX_TEXT = 2000
LOCK_STALE_SECONDS = 60
TRANSITIONS = {"take": ("queued", "taken"), "done": ("taken", "done"), "reject": (None, "rejected"),
               "cancel": ("queued", "rejected")}


class ContextError(ValueError):
    def __init__(self, message: str, exit_code: int = 2):
        super().__init__(message)
        self.exit_code = exit_code


def write_text_inside(root: str, rel: str, text: str) -> str:
    """Write `text` to root/rel: no links followed, exclusive temp file, atomic replace."""
    try:
        full = resolve_inside(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        full = resolve_inside(root, rel)  # again: nothing may have turned into a link meanwhile
    except PathError as err:
        raise ContextError(str(err), 4) from err
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(full), prefix=".tmp-", suffix=os.path.splitext(full)[1])
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, full)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return full


def write_json_inside(root: str, rel: str, data) -> str:
    return write_text_inside(root, rel, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


@contextmanager
def locked(root: str, rel: str):
    """A cross-process lock file at root/rel; a lock older than LOCK_STALE_SECONDS is taken over."""
    try:
        path = resolve_inside(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except PathError as err:
        raise ContextError(str(err), 4) from err
    for attempt in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                stale = time.time() - os.path.getmtime(path) > LOCK_STALE_SECONDS
            except OSError:
                stale = True
            if attempt or not stale:
                raise ContextError("another agent is changing this request; retry", 4) from None
            os.unlink(path)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def add_request(root: str, ctx_rel: str, sid: str | None, text: str, base_revision: str | None) -> dict:
    """Queue a request; `ctx_rel` is the context folder relative to `root` ("bot-ui/context" or "context")."""
    text = (text or "").strip()
    if not text:
        raise ContextError("a request needs text")
    if len(text) > MAX_TEXT:
        raise ContextError(f"a request is at most {MAX_TEXT} characters")
    if sid is not None and (not isinstance(sid, str) or not ID_RE.match(sid)):
        raise ContextError(f"not a screen id: {sid!r}")
    at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rid = "rq-" + hashlib.sha1(f"{sid}|{text}|{at}|{os.urandom(4).hex()}".encode("utf-8")).hexdigest()[:10]
    doc = {"schema": REQUEST_SCHEMA, "id": rid, "sid": sid, "text": text, "at": at,
           "baseRevision": base_revision, "status": "queued", "result": None}
    write_json_inside(root, f"{ctx_rel}/requests/{rid}.json", doc)
    return doc


def list_requests(context_dir: str) -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(context_dir, "requests", "*.json"))):
        if os.path.islink(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and doc.get("schema") == REQUEST_SCHEMA:
            out.append(doc)
    return sorted(out, key=lambda d: d.get("at") or "")


def set_request_status(root: str, ctx_rel: str, rid: str, action: str, result: str | None = None) -> dict:
    """take / done / reject / cancel one request under its lock; refuses a transition from the wrong state."""
    if not isinstance(rid, str) or not REQUEST_ID.match(rid):
        raise ContextError(f"not a request id: {rid!r} (see `requests list`)")
    if action not in TRANSITIONS:
        raise ContextError(f"unknown action {action!r}")
    rel = f"{ctx_rel}/requests/{rid}.json"
    with locked(root, f"{ctx_rel}/requests/{rid}.lock"):
        try:
            with open(resolve_inside(root, rel), encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError, PathError):
            raise ContextError(f"no request {rid}", 1) from None
        need, new = TRANSITIONS[action]
        if need is not None and doc.get("status") != need:
            raise ContextError(f"{rid} is {doc.get('status')}, not {need}", 4)
        doc["status"] = new
        if result is not None:
            doc["result"] = str(result)[:MAX_TEXT]
        write_json_inside(root, rel, doc)
    return doc
