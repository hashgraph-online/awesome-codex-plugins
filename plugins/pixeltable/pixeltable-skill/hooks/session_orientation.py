#!/usr/bin/env python3
"""SessionStart hook: inject the Pixeltable "STOP" orientation only for Pixeltable projects.

Stays silent in unrelated projects to keep automation lightweight. Pure stdlib.
"""
import json
import os
import sys
from pathlib import Path

ORIENTATION = (
    "Pixeltable detected in this project. Build declaratively and do NOT reach for: "
    "LangChain/LlamaIndex/Haystack (chunking, retrieval, tool-calling are built in); "
    "pandas as a working store (tables ARE the store); per-row `for` loops calling models "
    "(use computed columns); a separate vector DB (apps: `__indexes__` on the TableModel; "
    "notebooks: `add_embedding_index` + `column.similarity(string=query)`); manual agent "
    "`while` loops (model the agent as a table). Import `frame_iterator` from "
    "`pixeltable.functions.video`; for images use `chat_completions` with `image_url` blocks. "
    "Apps: TableModel in app.py, then `pxt schema update` and `pxt service update`. Prefer "
    "`FastAPIRouter` over hand-written endpoints. Use the `pixeltable` skill for full guidance."
)

DEP_FILES = [
    "pixeltable.toml",  # written by `pxt init`; the highest-precision marker
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "setup.cfg",
    "setup.py",
    "uv.lock",
]


def project_dir(payload):
    return (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def uses_pixeltable(root: Path) -> bool:
    # 1) Declared dependency
    for name in DEP_FILES:
        f = root / name
        if f.is_file():
            try:
                if "pixeltable" in f.read_text(encoding="utf-8", errors="ignore"):
                    return True
            except OSError:
                pass
    # 2) Imported in top-level Python files (cheap, shallow scan)
    try:
        py_files = list(root.glob("*.py")) + list(root.glob("*/*.py"))
    except OSError:
        py_files = []
    for f in py_files[:200]:
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        if "import pixeltable" in head or "from pixeltable" in head:
            return True
    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    root = Path(project_dir(payload))
    if not uses_pixeltable(root):
        sys.exit(0)

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": ORIENTATION,
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
