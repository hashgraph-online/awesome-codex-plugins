"""Project files: safe paths, canonical JSON, the source set and its revision."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*(\.[a-z0-9][a-z0-9_-]*)*$")
ID_MAX = 64
WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
STATE_DIR = ".bot-ui"  # lock, write journal, build cache: never part of the revision

# Key order used when the tool writes a file. Unknown keys are kept and go last, in their order.
KEY_ORDER = {
    "project": ["schemaVersion", "projectId", "title", "defaultLocale", "locales", "entryPoints", "contexts",
                "fields", "handlers", "messages", "capabilities", "adapter"],
    "screen": ["id", "title", "kind", "audience", "notes", "message", "keyboard", "actions", "input", "widget",
               "fallback"],
    "message": ["id", "format", "media", "text", "states"],
    "media": ["type", "file", "spoiler", "emoji"],
    "action": ["label", "type", "to", "rule", "presentation", "set", "handlerId", "outcomes", "pending", "url",
               "text", "fallback", "style", "icon", "callbackData", "hidden"],
    "rule": ["when", "match", "otherwise"],
    "when": ["field", "eq"],
    "keyboard": ["type", "rows", "placeholder", "resize", "oneTime"],
    "input": ["field", "to", "placeholder"],
    "widget": ["ref", "caption"],
}
SOURCE_PATTERNS = [
    re.compile(r"^project\.json$"),
    re.compile(r"^screens/[^/]+\.json$"),
    re.compile(r"^scenarios/[^/]+\.json$"),
    re.compile(r"^widgets/[^/]+(/[^/]+)*\.(json|html|css|js|svg)$"),
]


class PathError(ValueError):
    pass


def check_id(value: Any) -> str | None:
    """None if `value` is a valid stable ID, else the reason."""
    if not isinstance(value, str) or not value:
        return "ID must be a non-empty string"
    if len(value) > ID_MAX:
        return f"ID is longer than {ID_MAX} characters"
    if not ID_RE.match(value):
        return "ID uses lowercase ASCII letters, digits, '_' and '-', with '.' between segments"
    if any(seg in WINDOWS_RESERVED for seg in value.split(".")):
        return "ID segment is a reserved Windows file name"
    return None


def resolve_inside(root: str, rel: str) -> str:
    """Absolute path of `rel` under `root`; raises PathError for anything that could escape it."""
    if not isinstance(rel, str) or not rel or "\x00" in rel:
        raise PathError("empty or invalid path")
    norm = rel.replace("\\", "/")
    if norm.startswith("/") or norm.startswith("//") or re.match(r"^[A-Za-z]:", norm) or ":" in norm:
        raise PathError(f"{rel!r}: absolute, UNC or drive paths are not allowed")
    parts = norm.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise PathError(f"{rel!r}: empty, '.' or '..' components are not allowed")
    base = os.path.realpath(root)
    cur = base
    for p in parts:
        cur = os.path.join(cur, p)
        if os.path.islink(cur) or (hasattr(os.path, "isjunction") and os.path.isjunction(cur)):
            raise PathError(f"{rel!r}: symbolic links and junctions are not followed")
    full = os.path.realpath(cur)
    if os.path.normcase(os.path.commonpath([base, full])) != os.path.normcase(base):
        raise PathError(f"{rel!r}: resolves outside the project")
    return full


def is_source(rel: str) -> bool:
    return any(p.match(rel) for p in SOURCE_PATTERNS)


def _ordered(obj: Any, kind: str | None) -> Any:
    if isinstance(obj, list):
        return [_ordered(v, None) for v in obj]
    if not isinstance(obj, dict):
        return obj
    order = KEY_ORDER.get(kind or "", [])
    # Maps keep their key order where it is meaningful to people (actions, locales, fields).
    keys = [k for k in order if k in obj] + [k for k in obj if k not in order] if kind else list(obj)
    out = {}
    for k in keys:
        child = _CHILD.get((kind, k))
        if child == "action*" and isinstance(obj[k], dict):
            out[k] = {a: _ordered(v, "action") for a, v in obj[k].items()}
        else:
            out[k] = _ordered(obj[k], child)
    return out


_CHILD = {("screen", "message"): "message", ("screen", "keyboard"): "keyboard", ("screen", "actions"): "action*",
          ("screen", "input"): "input", ("screen", "widget"): "widget", ("action", "rule"): "rule",
          ("rule", "when"): "when", ("message", "media"): "media"}


def canonical_json(doc: Any, kind: str | None = None) -> bytes:
    """Machine-written form: UTF-8, 2-space indent, fixed key order, LF, final newline.
    Order of keyboard rows, locales and list items is semantic and never changed."""
    text = json.dumps(_ordered(doc, kind), ensure_ascii=False, indent=2)
    return (text + "\n").encode("utf-8")


def normalize_bytes(data: bytes) -> bytes:
    """Revision input: CRLF -> LF, so a Git checkout with autocrlf has the same revision."""
    return data.replace(b"\r\n", b"\n")


def replace_dir(src: str, dst: str, attempts: int = 8) -> None:
    """os.replace for a freshly written folder. On Windows an antivirus or indexer can hold the
    new folder for a moment and the rename fails with "Access is denied"; wait and try again."""
    for i in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if os.name != "nt" or i == attempts - 1:
                raise
            time.sleep(0.05 * 2 ** i)


def revision_of(files: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for rel in sorted(files):
        data = normalize_bytes(files[rel])
        h.update(rel.encode("utf-8") + b"\x00" + str(len(data)).encode() + b"\x00" + data + b"\x00")
    return "sha256:" + h.hexdigest()


@dataclass
class Diagnostic:
    code: str
    severity: str  # error | warning | info
    file: str
    pointer: str
    message: str
    screenId: str | None = None

    def to_json(self) -> dict:
        d = {"code": self.code, "severity": self.severity, "file": self.file, "pointer": self.pointer,
             "message": self.message}
        if self.screenId:
            d["screenId"] = self.screenId
        return d


@dataclass
class Snapshot:
    root: str
    files: dict[str, bytes]
    revision: str
    project: dict | None = None
    screens: dict[str, dict] = field(default_factory=dict)
    screen_files: dict[str, str] = field(default_factory=dict)  # id -> rel path
    scenarios: dict[str, dict] = field(default_factory=dict)
    widgets: dict[str, dict] = field(default_factory=dict)
    load_diagnostics: list[Diagnostic] = field(default_factory=list)
    read_only: bool = False

    def screen_path(self, sid: str) -> str:
        return self.screen_files.get(sid, f"screens/{sid}.json")


def read_files(root: str) -> dict[str, bytes]:
    """Every canonical source under root (relative POSIX path -> bytes). Skips STATE_DIR."""
    out: dict[str, bytes] = {}
    base = os.path.realpath(root)
    for dirpath, dirnames, filenames in os.walk(base):
        rel_dir = os.path.relpath(dirpath, base).replace(os.sep, "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d != "node_modules"
                             and not os.path.islink(os.path.join(dirpath, d)))
        for name in sorted(filenames):
            rel = f"{rel_dir}/{name}" if rel_dir else name
            if not is_source(rel):
                continue
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                continue
            with open(full, "rb") as fh:
                out[rel] = fh.read()
    return out


def parse_files(root: str, files: dict[str, bytes]) -> Snapshot:
    from . import SCHEMA_VERSION
    snap = Snapshot(root=root, files=files, revision=revision_of(files))
    diags = snap.load_diagnostics

    def load(rel: str):
        try:
            return json.loads(files[rel].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            diags.append(Diagnostic("JSON_INVALID", "error", rel, "", f"not valid UTF-8 JSON: {err}"))
            return None

    if "project.json" not in files:
        diags.append(Diagnostic("PROJECT_MISSING", "error", "project.json", "", "project.json is missing"))
    else:
        snap.project = load("project.json")
        if isinstance(snap.project, dict):
            ver = snap.project.get("schemaVersion")
            if ver != SCHEMA_VERSION:
                snap.read_only = True
                diags.append(Diagnostic("SCHEMA_VERSION_UNSUPPORTED", "error", "project.json", "/schemaVersion",
                                        f"schemaVersion {ver!r} is not {SCHEMA_VERSION}; the project opens read-only "
                                        "until a migration is chosen"))
    lower_seen: dict[str, str] = {}
    for rel in sorted(files):
        low = rel.lower()
        if low in lower_seen:
            diags.append(Diagnostic("PATH_CASE_COLLISION", "error", rel, "",
                                    f"differs from {lower_seen[low]} only by letter case (one file on Windows)"))
        lower_seen[low] = rel
        if rel.startswith("screens/"):
            doc = load(rel)
            if not isinstance(doc, dict):
                continue
            sid = doc.get("id")
            if sid in snap.screens:
                diags.append(Diagnostic("SCREEN_DUPLICATE", "error", rel, "/id",
                                        f"screen ID {sid!r} is also defined in {snap.screen_files[sid]}", sid))
                continue
            if isinstance(sid, str):
                snap.screens[sid] = doc
                snap.screen_files[sid] = rel
        elif rel.startswith("scenarios/"):
            doc = load(rel)
            if isinstance(doc, dict):
                snap.scenarios[str(doc.get("scenarioId", rel[10:-5]))] = doc
        elif rel.startswith("widgets/") and rel.endswith("/widget.json"):
            doc = load(rel)
            if isinstance(doc, dict):
                wid = rel.split("/")[1]
                doc.setdefault("id", wid)
                snap.widgets[wid] = doc
    return snap


def open_snapshot(root: str, *, recover: bool = True) -> Snapshot:
    """The project as it is on disk. recover=False never writes: a pending journal of an interrupted
    write is reported (WRITE_PENDING) instead of rolled back, for read-only callers such as MCP tools."""
    from .store import recover_if_needed
    if not recover:
        snap = parse_files(root, read_files(root))
        if os.path.exists(os.path.join(root, STATE_DIR, "journal.json")):
            snap.load_diagnostics.append(Diagnostic("WRITE_PENDING", "warning", f"{STATE_DIR}/journal.json", "",
                                                    "an interrupted write is pending; any bot-ui write command rolls it back"))
        return snap
    recovered = recover_if_needed(root)
    snap = parse_files(root, read_files(root))
    if recovered:
        snap.load_diagnostics.append(Diagnostic("WRITE_RECOVERED", "warning", f"{STATE_DIR}/journal.json", "",
                                                f"an interrupted write was rolled back ({recovered} file(s))"))
    return snap


def find_root(start: str) -> str | None:
    """Nearest folder with project.json, looking at start, start/bot-ui and the parents."""
    cur = os.path.abspath(start)
    while True:
        for cand in (cur, os.path.join(cur, "bot-ui")):
            if os.path.isfile(os.path.join(cand, "project.json")):
                return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent
