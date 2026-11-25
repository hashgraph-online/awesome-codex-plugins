"""Interactive artifact for a host without a local port: one self-contained HTML file.

The page is the Studio client built in artifact mode (studio/web, `npm run build:artifact`,
everything inlined, no network). This module injects a bot-ui-snapshot/v1 document into it.
The snapshot holds what the map, the inspector and the simulator need, and nothing that
identifies the machine: no absolute paths, no tokens, no widget sources, no Git data.
"""
from __future__ import annotations

import json
import os

from . import SCHEMA_VERSION, SNAPSHOT_FORMAT, TOOL_VERSION, emoji
from .project import Snapshot
from .validate import validate

from .skill import trusted_web_dir

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "__BOT_UI_SNAPSHOT__"
PROJECT_KEYS = ("schemaVersion", "projectId", "title", "defaultLocale", "locales", "entryPoints", "contexts",
                "fields", "handlers", "messages", "capabilities")


def snapshot_document(snap: Snapshot, screens: list[str] | None = None, emoji_previews: str = "used",
                      emoji_budget: int = 1_500_000, emoji_library_file: str | None = None) -> dict:
    p = snap.project or {}
    chosen = {sid: doc for sid, doc in snap.screens.items() if not screens or sid in screens}
    return {
        "format": SNAPSHOT_FORMAT, "tool": TOOL_VERSION, "schemaVersion": SCHEMA_VERSION,
        "projectId": p.get("projectId"), "baseRevision": snap.revision,
        "project": {k: p[k] for k in PROJECT_KEYS if k in p},
        "screens": chosen,
        "scenarios": snap.scenarios,
        "widgets": {wid: {"title": w.get("title"), "fallbackScreen": w.get("fallbackScreen")} for wid, w in snap.widgets.items()},
        "diagnostics": [d.to_json() for d in validate(snap) if not d.screenId or d.screenId in chosen],
        "features": {"map": True, "simulate": True, "editText": True, "editRule": True, "exportPatch": True,
                     "save": False, "widgets": False, "createScreen": False},
        "apply": "py -3 studio/bot-ui.py apply-patch --project <bot-ui folder> --patch-file <exported .json>",
        **({"emoji": block} if (block := emoji.snapshot_block(snap, emoji_budget, emoji_previews, emoji_library_file)) else {}),
    }


def build_artifact(snap: Snapshot, output: str, screens: list[str] | None = None, *, replace: bool = True,
                   emoji_library_file: str | None = None) -> str:
    """Write the single-file page. replace=False creates the file exclusively (FileExistsError if it is there)."""
    template = trusted_web_dir(snap.root, "dist-artifact", "index.html")
    if template is None:
        raise RuntimeError("the artifact client found by default lies inside the repository being opened; "
                           "set BOT_UI_STUDIO_DIR to the studio folder of a telegram-bot-ui checkout you trust")
    if not os.path.isfile(template):
        raise RuntimeError("the artifact client is not built: run `npm ci` and `npm run build:artifact` in studio/web")
    with open(template, encoding="utf-8") as fh:
        page = fh.read()
    if MARK not in page:
        raise RuntimeError(f"{template} has no {MARK} placeholder")
    doc = json.dumps(snapshot_document(snap, screens, emoji_library_file=emoji_library_file), ensure_ascii=False)
    doc = doc.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    page = page.replace(MARK, doc, 1)
    os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)
    with open(output, "w" if replace else "x", encoding="utf-8", newline="\n") as fh:  # "x": exclusive create
        fh.write(page)
    return output
