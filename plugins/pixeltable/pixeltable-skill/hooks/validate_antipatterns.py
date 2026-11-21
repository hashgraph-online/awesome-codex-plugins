#!/usr/bin/env python3
"""PostToolUse hook: flag deprecated/incorrect Pixeltable APIs and anti-patterns.

Reads the Claude Code hook payload from stdin, inspects Python content written or
edited, and returns non-blocking guidance via hookSpecificOutput.additionalContext.
Pure stdlib; no third-party dependencies.

Each check is (regex, severity, message, gate). Severity: "error" = wrong/deprecated
API, "recommended" = redundant framework Pixeltable already replaces. A gate is a
second regex that must also match the payload before the check may fire; it exists
for patterns that are correct in one file kind and wrong in another.

A false positive costs more than a missed hit: it pushes an agent to rewrite working
code. When in doubt, do not add the check.
"""
import io
import json
import os
import re
import sys
import tokenize
from pathlib import Path

# A file that declares a TableModel is an application file, where the catalog is
# built by `pxt schema update` and never by module-level SDK calls.
APP_FILE = re.compile(r"model_base\s*\(|\bTableModel\b")
PIXELTABLE_FILE = re.compile(r"\b(?:import\s+pixeltable|from\s+pixeltable\b|pxt\.)")

CHECKS = [
    (
        re.compile(r"from\s+pixeltable\.iterators\s+import|\bpixeltable\.iterators\b"),
        "error",
        (
            "`pixeltable.iterators` is a deprecated shim in full (FrameIterator, VideoSplitter, "
            "DocumentSplitter, StringSplitter, AudioSplitter, TileIterator). Import the function "
            "from `pixeltable.functions.*` instead -- e.g. "
            "`from pixeltable.functions.video import frame_iterator`."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(
            r"openai\.vision|functions\.openai\s+import\s*(?:\([^)]*\bvision\b|[^\n]*\bvision\b)"
        ),
        "error",
        (
            "`openai.vision` is deprecated. Use `chat_completions` with `image_url` content "
            "blocks, or `responses`."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(
            r"\.similarity\(\s*(?!(?:string|image|audio|video|document|vector|idx)\s*=)[^)\s]"
        ),
        "error",
        (
            "Positional `.similarity(...)` call. Always use a keyword: "
            "`similarity(string=...)`, or `image=` / `audio=` / `video=` / `document=` / `vector=` "
            "for the other modalities (`idx=` selects among several indexes on one column)."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(r"\.\w+_error(?:type|msg)\b"),
        "error",
        (
            "There is no `<col>_errortype` column. The error properties are attributes on the "
            "column: `t.summary.errortype` / `t.summary.errormsg`, valid on stored computed or "
            "media columns. Media cells also carry `.fileurl` / `.localpath`."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(r"\b(?:make_video|stitch_tiles)\s*\([^)]*\border_by\s*="),
        "error",
        (
            "`make_video` and `stitch_tiles` require the ordering expression as their FIRST "
            "POSITIONAL argument; `order_by=` raises. Call "
            "`make_video(t.pos, t.frame, fps=25)`."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(r"\bpxt\.Required\b|from\s+pixeltable\s+import\s+[^\n]*\bRequired\b"),
        "error",
        (
            "`pxt.Required` is deprecated and redundant: bare types are already non-nullable. "
            "Use `T` for required and `T | None` for optional."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(r"\badd_query_route\s*\([^)]*\bone_row\s*="),
        "error",
        (
            "`add_query_route(one_row=...)` was removed in Pixeltable 0.7.22. The route takes its "
            "response shape from the query: a query that aggregates without `group_by()` or ends in "
            "`limit(1)` is single-row (0 rows is a 404; 409 is gone). Put `limit(1)` on the query."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(r"@pxt\.query\s*\([^)]*\breturn_scalar\s*="),
        "error",
        (
            "`@pxt.query(return_scalar=...)` was removed in Pixeltable 0.7.22. A query that selects "
            "a single unnamed expression returns values instead of dicts; name the column to keep dicts."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(r"@pxt\.query[\s\S]*?sim=sim"),
        "recommended",
        (
            "`sim=sim` in `@pxt.query` can break `.collect()` and FastAPIRouter query routes. Alias similarity as "
            "`score=sim` (any name other than `sim`)."
        ),
        PIXELTABLE_FILE,
    ),
    (
        re.compile(r"\badd_embedding_index\s*\("),
        "recommended",
        (
            "This file declares a TableModel, so indexes belong on the model: "
            "`__indexes__ = [pxt.EmbeddingIndex(col, embedding=fn, name='...')]`. "
            "Note the model DSL spells it `name=` where the SDK spells it `idx_name=`."
        ),
        APP_FILE,
    ),
    (
        re.compile(
            r"^(?:\w+\s*=\s*)?pxt\.(?:create_table|get_table|create_view|create_dir)\s*\(",
            re.MULTILINE,
        ),
        "recommended",
        (
            "This file declares a TableModel, so importing it must not mutate the catalog. "
            "Declare the table as a model and apply it with `pxt schema update`; call "
            "`pxt.get_table()` inside a handler, not at module level."
        ),
        APP_FILE,
    ),
    (
        re.compile(
            r"^\s*(?:from|import)\s+(langchain|langgraph|llama_index|llama-index|haystack|"
            r"chromadb|faiss|pinecone|qdrant|weaviate|pgvector)\b",
            re.MULTILINE,
        ),
        "recommended",
        (
            "Detected a framework/vector-DB that Pixeltable replaces (chunking, embedding indexes, "
            "retrieval, and tool-calling are built in). See the `pixeltable` skill "
            "`references/anti-patterns.md`."
        ),
        PIXELTABLE_FILE,
    ),
]

PY_SUFFIXES = (".py", ".ipynb")
MAX_FILE_BYTES = 1_000_000


def code_only(text):
    """Remove comments and string contents before regex matching."""
    tokens = []
    try:
        stream = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in stream:
            if token.type in {tokenize.COMMENT, tokenize.STRING}:
                token = tokenize.TokenInfo(token.type, "", token.start, token.end, token.line)
            tokens.append(token)
    except (tokenize.TokenError, IndentationError):
        pass
    return tokenize.untokenize(tokens) if tokens else text


def read_python_file(path):
    try:
        if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            return None
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix == ".ipynb":
            notebook = json.loads(text)
            return "\n".join(
                "".join(cell.get("source", []))
                for cell in notebook.get("cells", [])
                if cell.get("cell_type") == "code"
            )
        return text
    except (OSError, ValueError, TypeError):
        return None


def extract_python_content(payload):
    """Return (file_path, text) from a supported hook payload, else (None, None)."""
    tool = payload.get("tool_name") or payload.get("toolName") or ""
    if tool not in {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}:
        return None, None
    ti = payload.get("tool_input") or payload.get("toolInput") or {}
    candidates = []
    direct_path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    if isinstance(direct_path, str) and direct_path.endswith(PY_SUFFIXES):
        candidates.append(direct_path)
    command = ti.get("command")
    if isinstance(command, str):
        candidates.extend(
            match.group(1).strip()
            for match in re.finditer(r"^\*\*\* (?:Add|Update) File: (.+)$", command, re.MULTILINE)
            if match.group(1).strip().endswith(PY_SUFFIXES)
        )

    root = Path(payload.get("cwd") or os.getcwd())
    saved = []
    names = []
    for candidate in dict.fromkeys(candidates):
        path = Path(candidate)
        if not path.is_absolute():
            path = root / path
        content = read_python_file(path)
        if content is not None:
            saved.append(content)
            names.append(candidate)
    if saved:
        return ", ".join(names), "\n".join(saved)

    parts = []
    for key in ("content", "new_string", "new_source"):
        if isinstance(ti.get(key), str):
            parts.append(ti[key])
    edits = ti.get("edits")
    if isinstance(edits, list):
        for e in edits:
            if isinstance(e, dict) and isinstance(e.get("new_string"), str):
                parts.append(e["new_string"])
    if not parts:
        return None, None
    return direct_path or "edited Python", "\n".join(parts)


def findings_for(text):
    """Return the ordered list of finding strings for a block of source text."""
    text = code_only(text)
    found = []
    for pattern, severity, message, gate in CHECKS:
        if gate is not None and not gate.search(text):
            continue
        if pattern.search(text):
            marker = "FIX" if severity == "error" else "CONSIDER"
            found.append(f"[{marker}] {message}")
    return found


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    file_path, text = extract_python_content(payload)
    if not text:
        sys.exit(0)

    findings = findings_for(text)
    if not findings:
        sys.exit(0)

    context = (
        f"Pixeltable review of {file_path}:\n- " + "\n- ".join(findings)
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context,
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
