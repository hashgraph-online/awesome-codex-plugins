"""What a code-writing batch added that quiets a check: a report-only scan.

An unattended writer that meets a lint or test gate can satisfy it by adding a
suppression (``# noqa``, ``# type: ignore``, ``eslint-disable``), skipping a
test, or loosening the gate's configuration, and its own summary seldom says
so. This module lists those additions so a person sees them: each hit is
``path:line``, the marker, and whether a reason sits beside it. It is report
only. Nothing here fails a batch, changes an exit code or blocks a run; the
callers list the hits under :data:`CHECK_THESE_HEADING` in the phase's
``summary.md`` (docs/development/write-scheduler.md#suppressions-a-batch-added).

What counts:

- **Python comment markers** (:data:`SEG_MARKERS`): read with ``tokenize``, so
  text inside a string never matches, and only when a ``#`` segment of the
  comment *starts* with the marker, so prose that mentions one does not. The
  reason is the rest of the comment, or a comment line directly above.
- **JavaScript, TypeScript and Go comment markers** (:data:`JS_MARKERS`):
  ``eslint-disable``, ``@ts-ignore``, ``@ts-expect-error``, ``@ts-nocheck``,
  ``istanbul``/``c8 ignore`` and ``//nolint``, only right after a comment
  opener that sits outside a string literal (:func:`_c_like_comments`).
- **Skip and xfail markers**: in Python code through ``ast``
  (``pytest.mark.skip``, ``pytest.skip()``, ``unittest.skip``, ...), with the
  call's own reason argument as the reason; in JavaScript and TypeScript code
  (``it.skip(``, ``xit(``, ...) outside strings and comments.
- **Lint, type-checker and test configuration** (:data:`RUFF_FILES`,
  :data:`PY_CFG`, :data:`C_LIKE_CFG`): TOML compared key by key, each changed
  key reported and a loosening named (a raised threshold, a new ignore entry,
  a rule dropped from ``select``); any other format line by line.

Every marker is keyed by its kind, its text and the code on its line (a skip
marker by its name and the function around it, a JavaScript skip by its
line) and netted against the before side (:func:`scan_changes`): per file on
that key, so a line the batch only moved is not reported; for a comment
marker, per file on the kind and text alone, so a marker the file already
held is not reported because the batch edited its line (each one the file
lost cancels the added one whose code is most alike, when more than half
their words match: :data:`PAIRING_MIN_ALIKE`), while a second copy still is;
and across the batch's files on the whole key, so a line moved from one file
to another is not reported. A skip marker is not netted on its name alone,
so a skip moved from one test to another is reported, and so is a renamed
skipped test or an edited JavaScript skip line. The reason is never part of
a key: neither before side records it. A marker-free dodge (a parameter
renamed ``_name`` to satisfy an unused-argument rule) has no marker to read
and is not detected: a heuristic for it was tried and was unreliable.

Pure: callers hand over each file's before and after text, or for the before
side the counters :func:`before_side` recorded from it; nothing here reads a
file or runs git. A file the scan fails on (an odd configuration value, a
source ``ast`` cannot walk) is left out and named, never the batch's other
files. Change the Python detection only with its validation in mind
(docs/development/write-scheduler.md#suppressions-a-batch-added).
"""

from __future__ import annotations

import ast
import collections
import difflib
import io
import json
import re
import tokenize
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .redact import redact_text
from .text_clip import clip

__all__ = [
    "CHECK_THESE_HEADING",
    "before_side",
    "from_rows",
    "hit_line",
    "notice_clause",
    "scan_changes",
    "scannable",
    "section_lines",
]

#: The heading both legs list a phase's hits under in ``summary.md``.
CHECK_THESE_HEADING = "## Check these: suppressions added"

#: The longest quoted source line and reason a hit carries.
TEXT_MAX_CHARS = 200
REASON_MAX_CHARS = 160

#: A before side: absent (``None``: the file did not exist), its text, or the
#: counters :func:`before_side` recorded from its text.
Before = Union[None, str, Mapping[str, Any]]

#: Directories and files never scanned: caches, environments, git itself and
#: the plugin's own workspace.
EXCLUDED = re.compile(
    r"(^|/)(\.multi-llm|__pycache__|\.pytest_cache|\.venv|venv|\.ruff_cache|"
    r"\.mypy_cache|\.git|node_modules)(/|$)|\.pyc$"
)

#: A ``#`` comment segment that starts with one of these is a marker. Its
#: text is the match, whitespace collapsed (``noqa: PLR0913``).
SEG_MARKERS = [
    ("noqa", re.compile(r"^noqa\b(:\s*[A-Z]+[0-9]+(\s*,\s*[A-Z]+[0-9]+)*)?", re.I)),
    ("ruff-noqa-file", re.compile(r"^(ruff|flake8)\s*:\s*noqa\b.*", re.I)),
    ("type-ignore", re.compile(r"^type:\s*ignore\b(\[[^\]]*\])?")),
    ("pyright-ignore", re.compile(r"^pyright:\s*ignore\b(\[[^\]]*\])?")),
    ("pragma-no-cover", re.compile(r"^pragma:\s*no\s*(cover|branch)\b")),
    ("pylint-disable", re.compile(r"^pylint:\s*disable\b.*")),
    ("fmt-off", re.compile(r"^fmt:\s*(off|skip)\b")),
    ("nosec", re.compile(r"^nosec\b")),
]

#: A comment of a C-like file (``//`` or ``/* */``) that starts with one of
#: these is a marker. ``eslint-disable`` takes its rule list up to an
#: ``--`` description or the comment's end; ``nolint`` its ``:rule`` list.
JS_MARKERS = [
    ("eslint-disable", re.compile(r"^eslint-disable(-next-line|-line)?\b[^*]*?(?=\s--\s|\s--$|\*/|$)")),
    ("ts-ignore", re.compile(r"^@ts-ignore\b")),
    ("ts-expect-error", re.compile(r"^@ts-expect-error\b")),
    ("ts-nocheck", re.compile(r"^@ts-nocheck\b")),
    ("coverage-ignore", re.compile(r"^(istanbul|c8)\s+ignore\b(\s+(next|else|if|file|start|stop))?")),
    ("nolint", re.compile(r"^nolint\b(:[\w,-]+)?")),
]

#: Python skip markers: an attribute reached as ``...mark.skip``, and calls.
SKIP_ATTR = re.compile(r"(^|\.)mark\.(skip|skipif|xfail)$")
SKIP_CALL = re.compile(
    r"^(pytest\.(skip|xfail|importorskip)|unittest\.(skip|skipIf|skipUnless|expectedFailure)"
    r"|self\.skipTest|skip|xfail)$"
)
#: The skip key of a Python file ``ast`` cannot read, netted like any other:
#: a batch that leaves a file unparseable gets one ``unparseable`` hit, since
#: its skip markers could not be read.
_UNPARSEABLE = "UNPARSEABLE"
UNPARSEABLE_MARKER = "the file does not parse, so its skip markers could not be read"
#: JavaScript and TypeScript skip markers, in code outside strings and comments.
JS_SKIP = re.compile(
    r"(?<![\w.$])(?:(?:it|test|describe|suite|context)\.(?:skip|todo)|x(?:it|test|describe))\s*\("
)

RUFF_FILES = re.compile(r"(^|/)(ruff\.toml|\.ruff\.toml)$")
PY_CFG = re.compile(
    r"(^|/)(pyproject\.toml|setup\.cfg|tox\.ini|mypy\.ini|\.flake8|pytest\.ini|"
    r"\.coveragerc|\.pylintrc)$"
)
#: The JavaScript, TypeScript and Go lint and type-checker configurations,
#: compared line by line.
C_LIKE_CFG = re.compile(
    r"(^|/)(\.eslintrc(\.(js|cjs|json|ya?ml))?|eslint\.config\.(js|mjs|cjs|ts|mts|cts)|"
    r"\.eslintignore|tsconfig(\.[\w-]+)?\.json|\.golangci\.(ya?ml|toml|json))$"
)
LOOSEN_LIST_GROW = re.compile(
    r"(^|\.)(ignore|extend-ignore|per-file-ignores(\..*)?|exclude|extend-exclude|unfixable|"
    r"extend-per-file-ignores(\..*)?|norecursedirs|filterwarnings|addopts|disable_error_code|"
    r"ignore_missing_imports|omit|exclude_lines|exclude_also)$"
)
LOOSEN_NUM_UP = re.compile(
    r"(^|\.)(max-complexity|max-args|max-positional-args|max-branches|max-returns|"
    r"max-statements|max-locals|line-length|max-line-length|max-doc-length|"
    r"max-nested-blocks|fail_under_down)$"
)
SELECT_KEYS = re.compile(r"(^|\.)(select|extend-select)$")
#: The ``[tool.*]`` tables of ``pyproject.toml`` that configure a check.
PYPROJECT_TOOLS = ("ruff", "pytest", "mypy", "coverage", "pylint", "pyright", "flake8")

_PY_SUFFIXES = (".py", ".pyi")
_JS_SUFFIXES = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
_GO_SUFFIXES = (".go",)


def _is_python(path: str) -> bool:
    return path.endswith(_PY_SUFFIXES)


def _is_c_like(path: str) -> bool:
    return path.endswith(_JS_SUFFIXES + _GO_SUFFIXES)


def _is_config(path: str) -> bool:
    return bool(RUFF_FILES.search(path) or PY_CFG.search(path) or C_LIKE_CFG.search(path))


def scannable(path: str) -> bool:
    """Whether :func:`scan_changes` reads *path* (repository-relative, ``/``):
    a Python, JavaScript/TypeScript or Go source, or a check's configuration."""
    path = str(path).replace("\\", "/")
    if EXCLUDED.search(path):
        return False
    return _is_python(path) or _is_c_like(path) or _is_config(path)


# ---------------------------------------------------------------------------
# Python comment markers (tokenize)
# ---------------------------------------------------------------------------

def _segments(comment: str) -> List[Tuple[str, str]]:
    """The markers a ``#`` comment's segments start with: ``(kind, text)``."""
    out = []
    for seg in comment.split("#")[1:]:
        s = seg.strip()
        for kind, rx in SEG_MARKERS:
            m = rx.match(s)
            if m:
                out.append((kind, re.sub(r"\s+", " ", m.group(0))))
                break
    return out


def _reason(comment: str) -> str:
    """Prose in the same comment that is not itself a marker: the rest of a
    marker segment, or another segment."""
    words = []
    for seg in comment.split("#")[1:]:
        s = seg.strip()
        rest = s
        for _kind, rx in SEG_MARKERS:
            m = rx.match(s)
            if m:
                rest = s[m.end():]
                break
        rest = rest.strip(" -—–:;,.()")
        if re.search(r"[A-Za-z]{3,}", rest):
            words.append(rest)
    return " | ".join(words)


def _python_comment_markers(src: Optional[str]) -> List[Tuple[str, str, str, int, str, Optional[str]]]:
    """``[(kind, marker text, code before it, line, full line, reason)]`` from
    real comments only; reason ``None`` when the comment and the line above
    give none."""
    res: List[Tuple[str, str, str, int, str, Optional[str]]] = []
    if src is None:
        return res
    lines = src.splitlines()
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        toks = None
    if toks is None:
        # Untokenizable: every `#` read as a comment's start.
        for i, line in enumerate(lines, 1):
            if "#" in line:
                code, _, com = line.partition("#")
                for kind, text in _segments("#" + com):
                    res.append((kind, text, code.strip(), i, line.strip(),
                                _reason("#" + com) or None))
        return res
    for tok in toks:
        if tok.type != tokenize.COMMENT:
            continue
        lineno = tok.start[0]
        full = lines[lineno - 1] if lineno - 1 < len(lines) else tok.string
        code = full[:tok.start[1]].strip()
        segs = _segments(tok.string)
        if not segs:
            continue
        above = lines[lineno - 2].strip() if lineno >= 2 else ""
        above = above.lstrip("#").strip() if above.startswith("#") and not _segments(above) else ""
        for kind, text in segs:
            reason = _reason(tok.string) or (("above: " + above) if above else "")
            res.append((kind, text, code, lineno, full.strip(), reason or None))
    return res


# ---------------------------------------------------------------------------
# C-like comment markers and JavaScript skips (a small lexer)
# ---------------------------------------------------------------------------

def _c_like_comments(src: str) -> List[Tuple[int, int, str, str]]:
    """``[(line, column, comment text, code before it)]`` for each ``//`` and
    ``/* */`` comment of a C-like source, its text without the opener (a
    block comment's text per line), found outside string literals.

    Strings are ``'…'``, ``"…"`` and backquoted ones, each ending at the line's
    end when unterminated; a block comment may span lines.
    """
    out: List[Tuple[int, int, str, str]] = []
    in_block = False
    for number, line in enumerate(src.splitlines(), 1):
        index, size, quote, code_end = 0, len(line), "", None
        if in_block:
            end = line.find("*/")
            text = line if end < 0 else line[:end]
            out.append((number, 0, text.strip().lstrip("*").strip(), ""))
            if end < 0:
                continue
            in_block, index = False, end + 2
        while index < size:
            char = line[index]
            if quote:
                if char == "\\":
                    index += 2
                    continue
                if char == quote:
                    quote = ""
                index += 1
                continue
            if char in "'\"`":
                quote = char
            elif line.startswith("//", index):
                code_end = index if code_end is None else code_end
                out.append((number, index, line[index + 2:], line[:code_end].strip()))
                break
            elif line.startswith("/*", index):
                code_end = index if code_end is None else code_end
                end = line.find("*/", index + 2)
                text = line[index + 2:] if end < 0 else line[index + 2:end]
                out.append((number, index, text.strip().lstrip("*").strip(),
                            line[:code_end].strip()))
                if end < 0:
                    in_block = True
                    break
                index = end + 2
                continue
            index += 1
    return out


def _c_like_code(src: str) -> List[Tuple[int, str]]:
    """``[(line, code)]``: each line with its comments and string literals
    blanked out, for the skip markers."""
    blanked: Dict[int, List[str]] = {}
    lines = src.splitlines()
    in_block = False
    for number, line in enumerate(lines, 1):
        chars = list(line)
        index, size, quote = 0, len(line), ""
        if in_block:
            end = line.find("*/")
            stop = size if end < 0 else end + 2
            chars[:stop] = " " * stop
            if end < 0:
                blanked[number] = chars
                continue
            in_block, index = False, stop
        while index < size:
            char = line[index]
            if quote:
                chars[index] = " "
                if char == "\\" and index + 1 < size:
                    chars[index + 1] = " "
                    index += 2
                    continue
                if char == quote:
                    quote = ""
                index += 1
                continue
            if char in "'\"`":
                quote = char
                index += 1
                continue
            if line.startswith("//", index):
                chars[index:] = " " * (size - index)
                break
            if line.startswith("/*", index):
                end = line.find("*/", index + 2)
                stop = size if end < 0 else end + 2
                chars[index:stop] = " " * (stop - index)
                if end < 0:
                    in_block = True
                    break
                index = stop
                continue
            index += 1
        blanked[number] = chars
    return [(number, "".join(chars)) for number, chars in blanked.items()]


def _js_reason(kind: str, rest: str) -> str:
    """The description after a C-like marker: an ESLint ``--`` description,
    a TypeScript directive's own words, or a later ``//`` segment."""
    if kind == "eslint-disable":
        _, dashes, after = rest.partition("--")
        rest = after if dashes else ""
    elif kind == "nolint":
        _, slashes, after = rest.partition("//")
        rest = after if slashes else ""
    rest = rest.strip().rstrip("*/").strip(" -—–:;,.()")
    return rest if re.search(r"[A-Za-z]{3,}", rest) else ""


def _c_like_comment_markers(src: Optional[str]) -> List[Tuple[str, str, str, int, str, Optional[str]]]:
    """:func:`_python_comment_markers`' records for a C-like source."""
    res: List[Tuple[str, str, str, int, str, Optional[str]]] = []
    if src is None:
        return res
    lines = src.splitlines()
    comments = _c_like_comments(src)
    commented = {number for number, _col, _text, code in comments if not code}
    for number, _col, text, code in comments:
        body = text.strip()
        for kind, rx in JS_MARKERS:
            m = rx.match(body)
            if not m:
                continue
            marker = re.sub(r"\s+", " ", m.group(0)).strip()
            reason = _js_reason(kind, body[m.end():])
            if not reason and number - 1 in commented:
                above = [t for n, _c, t, c in comments if n == number - 1 and not c]
                above_text = above[0].strip() if above else ""
                if above_text and not any(r.match(above_text) for _k, r in JS_MARKERS):
                    reason = "above: " + above_text
            res.append((kind, marker, code, number, lines[number - 1].strip(), reason or None))
            break
    return res


def _comment_markers(path: str, src: Optional[str]) -> List[Tuple[str, str, str, int, str, Optional[str]]]:
    if _is_python(path):
        return _python_comment_markers(src)
    if _is_c_like(path):
        return _c_like_comment_markers(src)
    return []


# ---------------------------------------------------------------------------
# Skip markers
# ---------------------------------------------------------------------------

def _dotted(node: ast.AST) -> Optional[str]:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _call_reason(call: Optional[ast.AST]) -> Optional[str]:
    """A skip call's ``reason=`` keyword, else its first string argument."""
    if not isinstance(call, ast.Call):
        return None
    for keyword in call.keywords:
        if keyword.arg in ("reason", "msg") and isinstance(keyword.value, ast.Constant) \
                and isinstance(keyword.value.value, str):
            return keyword.value.value
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def _python_skip_markers(src: Optional[str]) -> List[Tuple[str, str, int, str, Optional[str]]]:
    """``[(name, enclosing def, line, full line, reason)]`` skip and xfail
    markers in code; one ``UNPARSEABLE`` record for a file ``ast`` cannot read."""
    res: List[Tuple[str, str, int, str, Optional[str]]] = []
    if src is None:
        return res
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return [(_UNPARSEABLE, "", 0, "", None)]
    lines = src.splitlines()
    parents: Dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    def enclosing(node: ast.AST) -> str:
        while node in parents:
            node = parents[node]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                return node.name
        return "<module>"

    seen = set()
    for node in ast.walk(tree):
        name = None
        call: Optional[ast.AST] = None
        if isinstance(node, ast.Attribute):
            dotted = _dotted(node)
            if dotted and SKIP_ATTR.search(dotted):
                name = dotted
                parent = parents.get(node)
                call = parent if isinstance(parent, ast.Call) and parent.func is node else None
        elif isinstance(node, ast.Call):
            dotted = _dotted(node.func)
            if dotted and SKIP_CALL.match(dotted):
                name = dotted + "()"
                call = node
        if name and (node.lineno, name.rstrip("()")) not in seen:
            seen.add((node.lineno, name.rstrip("()")))
            full = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
            res.append((name, enclosing(node), node.lineno, full, _call_reason(call)))
    return res


def _js_skip_markers(src: Optional[str]) -> List[Tuple[str, str, int, str, Optional[str]]]:
    """:func:`_python_skip_markers`' records for JavaScript and TypeScript,
    keyed by the code on the line in place of the enclosing function."""
    res: List[Tuple[str, str, int, str, Optional[str]]] = []
    if src is None:
        return res
    lines = src.splitlines()
    for number, code in _c_like_code(src):
        for match in JS_SKIP.finditer(code):
            name = re.sub(r"\s+", "", match.group(0)).rstrip("(") + "()"
            full = lines[number - 1].strip()
            res.append((name, full, number, full, None))
    return res


def _skip_markers(path: str, src: Optional[str]) -> List[Tuple[str, str, int, str, Optional[str]]]:
    if _is_python(path):
        return _python_skip_markers(src)
    if path.endswith(_JS_SUFFIXES):
        return _js_skip_markers(src)
    return []


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _toml_module() -> Any:
    try:
        # tomllib is 3.11+; on 3.10 TOML is compared line by line instead.
        import tomllib as _toml
    except ImportError:  # pragma: no cover - Python 3.10
        return None
    return _toml


def _flat(data: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            out.update(_flat(value, f"{prefix}{key}." if isinstance(value, dict) else f"{prefix}{key}"))
            if isinstance(value, dict) and not value:
                out[prefix + key] = {}
    else:
        out[prefix.rstrip(".")] = data
    return out


def _json(value: Any) -> str:
    """A configuration value as a finding spells it: JSON, with what JSON
    has no form for (a TOML date or time) as its text."""
    return json.dumps(value, default=str)


def _toml_load(toml: Any, text: Optional[str]) -> Dict[str, Any]:
    if text is None:
        return {}
    try:
        return toml.loads(text)
    except Exception as exc:  # noqa: BLE001 - an unparseable config is a finding
        return {"__unparseable__": str(exc)}


def _comment_free(text: Optional[str]) -> List[str]:
    return [
        line.strip() for line in (text or "").splitlines()
        if line.strip() and not line.strip().startswith(("#", ";", "//"))
    ]


def _line_of(after: Optional[str], key: str = "", line: str = "") -> int:
    """Where a config finding sits in *after*: the first line equal to *line*,
    else the first assigning *key*'s last part; 0 when neither is found."""
    if not after:
        return 0
    rows = after.splitlines()
    if line:
        for number, row in enumerate(rows, 1):
            if row.strip() == line:
                return number
    if key:
        leaf = re.escape(key.rsplit(".", 1)[-1])
        assign = re.compile(rf"""^\s*["']?{leaf}["']?\s*=""")
        for number, row in enumerate(rows, 1):
            if assign.match(row):
                return number
    return 0


def _config_reason(after: Optional[str], number: int) -> Optional[str]:
    """A ``#`` (or ``//``) comment on line *number* of *after*, else a
    comment line directly above it."""
    if not after or number <= 0:
        return None
    rows = after.splitlines()
    row = rows[number - 1] if number - 1 < len(rows) else ""
    for opener in ("#", "//"):
        if opener in row:
            rest = row.split(opener, 1)[1].strip(" -—–:;,.()")
            if re.search(r"[A-Za-z]{3,}", rest):
                return rest
    above = rows[number - 2].strip() if number >= 2 else ""
    for opener in ("#", ";", "//"):
        if above.startswith(opener):
            text = above[len(opener):].strip()
            if re.search(r"[A-Za-z]{3,}", text):
                return "above: " + text
    return None


def _config_findings(path: str, before: Optional[str], after: Optional[str]) -> List[Tuple[str, str, int, str]]:
    """``[(kind, path, line, what changed)]`` for one configuration file."""
    res: List[Tuple[str, str, int, str]] = []
    toml = _toml_module() if path.endswith(".toml") else None
    if toml is not None:
        b, a = _toml_load(toml, before), _toml_load(toml, after)
        if path.endswith("pyproject.toml"):
            b = {k: v for k, v in b.get("tool", {}).items() if k in PYPROJECT_TOOLS} \
                if isinstance(b.get("tool"), dict) else {}
            a = {k: v for k, v in a.get("tool", {}).items() if k in PYPROJECT_TOOLS} \
                if isinstance(a.get("tool"), dict) else {}
        fb, fa = _flat(b), _flat(a)
        if before is None and fa and (RUFF_FILES.search(path) or "ruff" in a):
            res.append(("new-lint-config", path, 1, f"new config file with keys {sorted(fa)}"))
        for key in sorted(set(fb) | set(fa)):
            vb, va = fb.get(key, "<absent>"), fa.get(key, "<absent>")
            if vb == va:
                continue
            kind = "cfg-changed"
            if LOOSEN_NUM_UP.search(key) and isinstance(vb, (int, float)) \
                    and isinstance(va, (int, float)) and va > vb:
                kind = "cfg-loosened-threshold"
            elif LOOSEN_NUM_UP.search(key) and vb == "<absent>":
                kind = "cfg-loosened-threshold"
            elif LOOSEN_LIST_GROW.search(key):
                kind = "cfg-ignore-entry"
            elif SELECT_KEYS.search(key) and isinstance(vb, list):
                # Membership, not a set: an entry may be a list or a table.
                kept = va if isinstance(va, list) else []
                if any(entry not in kept for entry in vb):
                    kind = "cfg-select-removed"
            line = 0 if va == "<absent>" else _line_of(after, key=key)
            res.append((kind, path, line, f"{key}: {_json(vb)} -> {_json(va)}"))
    else:
        # Any other format: a line diff of the lines that are not comments.
        cb, ca = collections.Counter(_comment_free(before)), collections.Counter(_comment_free(after))
        for line in (ca - cb).elements():
            res.append(("cfg-changed", path, _line_of(after, line=line), "+ " + line))
        for line in (cb - ca).elements():
            res.append(("cfg-changed", path, 0, "- " + line))
    return res


# ---------------------------------------------------------------------------
# The scan
# ---------------------------------------------------------------------------

def before_side(path: str, text: Optional[str]) -> Optional[Dict[str, Any]]:
    """What :func:`scan_changes` nets *path*'s after side against, recorded
    from its *text* now: the counts of its marker keys and skip keys, and a
    configuration file's text. JSON-serializable, so a leg can keep it
    between binding a batch and recording it. ``None`` for an absent file."""
    if text is None:
        return None
    path = str(path).replace("\\", "/")
    comments = collections.Counter(
        (kind, marker, code) for kind, marker, code, *_rest in _comment_markers(path, text)
    )
    skips = collections.Counter(
        (name, encl) for name, encl, *_rest in _skip_markers(path, text)
    )
    side: Dict[str, Any] = {
        "comment": [[*key, count] for key, count in sorted(comments.items())],
        "skip": [[*key, count] for key, count in sorted(skips.items())],
    }
    if _is_config(path):
        side["config"] = text
    return side


def _before_counts(path: str, before: Before) -> Tuple[collections.Counter, collections.Counter, Optional[str]]:
    """``(marker keys, skip keys, config text)`` of a before side."""
    if before is None:
        return collections.Counter(), collections.Counter(), None
    if isinstance(before, str):
        side = before_side(path, before) or {}
    else:
        side = dict(before)
    comments = collections.Counter({
        (str(row[0]), str(row[1]), str(row[2])): int(row[3])
        for row in side.get("comment") or [] if isinstance(row, (list, tuple)) and len(row) == 4
    })
    skips = collections.Counter({
        (str(row[0]), str(row[1])): int(row[2])
        for row in side.get("skip") or [] if isinstance(row, (list, tuple)) and len(row) == 3
    })
    config = side.get("config")
    return comments, skips, config if isinstance(config, str) else None


#: What a quoted source line loses: the controls ``text_clip.plain_line``
#: removes (a terminal acts on them), tabs read as spaces; its own spacing stays.
_CONTROLS = re.compile("[\x00-\x08\x0a-\x1f\x7f-\x9f\u200e\u200f\u202a-\u202e\u2066-\u2069]")


def _quoted(text: str) -> str:
    return clip(_CONTROLS.sub("", redact_text(text).replace("\t", " ")).strip(),
                TEXT_MAX_CHARS, flatten=False)


def _hit(path: str, line: int, kind: str, marker: str, text: str,
         reason: Optional[str]) -> Dict[str, Any]:
    return {
        "path": path,
        "line": int(line or 0),
        "kind": kind,
        "marker": clip(redact_text(marker), TEXT_MAX_CHARS),
        "text": _quoted(text),
        "reason": clip(redact_text(reason), REASON_MAX_CHARS) if reason else None,
    }


def _shown_marker(path: str, kind: str, marker: str) -> str:
    """A comment marker as its source spells it: ``# noqa: E501``."""
    if _is_python(path):
        return f"# {marker}"
    return marker


#: Where a marker was found: ``(path, line, full line, reason)``.
_Where = Tuple[str, int, str, Optional[str]]
#: A file's netted side of one marker family: the added occurrences (each with
#: its key), and the keys its before side held that are gone and were not
#: matched to an edited line.
_Netted = Tuple[List[Tuple[Tuple[str, ...], _Where]], collections.Counter]

#: Past this many pairs to weigh for one marker in one file, the edited-line
#: netting falls back to the count: each vanished marker cancels one added
#: one, the added ones taken in line order, with no likeness weighed and no
#: :data:`PAIRING_MIN_ALIKE` floor. The vanished side has no line (a recorded
#: before side keeps counts only), so no order pairs an edited line with its
#: old self there, and a floor over arbitrary pairs would list real edits.
PAIRING_MAX = 2500

#: How alike (:func:`_alike`) the code beside a vanished comment marker and
#: beside an added one must be, strictly, for the second to count as the first
#: on an edited line: more than half their words in common. Typical edits of
#: a marked line measure 0.67 (``except Exception:`` gaining ``as exc``) to
#: 0.94 (a sixth argument added to a ``def``; ``import os`` to
#: ``import os, sys`` is 0.8), while different lines sit at 0.5 or below
#: (``import os`` and ``import json``, ``from a import b`` and
#: ``from c import d``; ``self.x = x`` and ``self.y = y`` 0.33). A tie at 0.5
#: is listed: the scan is report-only, so a doubtful pair costs a person one
#: line to read, while a wrong cancellation hides a suppression. The cost: a
#: two-word line whose second word changed (``x = 1`` to ``x = 2``, 0.5) is
#: listed as added.
PAIRING_MIN_ALIKE = 0.5


_WORD = re.compile(r"\w+")


def _alike(left: str, right: str) -> float:
    """How alike two places are, word by word: ``2 * matched / total`` over
    their ``\\w+`` words, punctuation left out, so ``a = f()`` and
    ``b = g()`` share nothing (``import os`` is nearer ``import os, sys``
    than ``import json``, which it is not letter by letter). Two places with
    no word at all (a marker alone on its line, a bare ``})``) are alike."""
    return difflib.SequenceMatcher(
        None, _WORD.findall(left), _WORD.findall(right), autojunk=False).ratio()


def _net_file(
    before: Mapping[Tuple[str, ...], int], after: Mapping[Tuple[str, ...], List[_Where]],
    *, edited_lines: bool,
) -> _Netted:
    """One file's added markers of one family (comment or skip), netted on
    the whole key and, for comment markers, on an edited line too.

    A key is the marker's family (``kind, marker`` or a skip's name) followed
    by its place (the code on its line, or the function around a skip, or a
    JavaScript skip's line). First on the whole key: a key found more often
    after than before contributes its last surplus occurrences, a key found
    less often leaves that many vanished. Then, with *edited_lines* (comment
    markers only), on the family alone: each vanished marker cancels the
    added one of its family whose code is most alike, when that likeness
    passes :data:`PAIRING_MIN_ALIKE` (past :data:`PAIRING_MAX`, one added
    one each, by count), since a marker that was in the file
    before and still is was not added just because the batch edited its
    line; a second copy of it still counts. Skips are netted on the whole key
    alone: a skip's place is the function around it, which editing its line
    does not change, so the second netting would only hide a skip moved from
    one test to another.
    """
    added: List[Tuple[Tuple[str, ...], _Where]] = []
    for key, found in after.items():
        surplus = len(found) - before.get(key, 0)
        if surplus > 0:
            added += [(key, where) for where in found[-surplus:]]
    vanished: List[Tuple[str, ...]] = []
    for key, count in sorted(before.items()):
        vanished += [key] * (count - len(after.get(key, ())))
    dropped: set = set()
    matched: set = set()
    families = sorted({key[:-1] for key in vanished}) if edited_lines else []
    for family in families:
        mine = [i for i, (key, _w) in enumerate(added) if key[:-1] == family]
        gone = [j for j, key in enumerate(vanished) if key[:-1] == family]
        if not mine:
            continue
        if len(mine) * len(gone) <= PAIRING_MAX:
            pairs = sorted(
                (-_alike(added[i][0][-1], vanished[j][-1]), i, j) for i in mine for j in gone)
            pairs = [(i, j) for unlike, i, j in pairs if -unlike > PAIRING_MIN_ALIKE]
        else:
            pairs = list(zip(mine, gone))
        for i, j in pairs:
            if i not in dropped and j not in matched:
                dropped.add(i)
                matched.add(j)
    left = collections.Counter(key for j, key in enumerate(vanished) if j not in matched)
    return [entry for i, entry in enumerate(added) if i not in dropped], left


def _scan_file(path: str, before: Before, after: Optional[str]) -> Tuple[
        List[Dict[str, Any]], _Netted, _Netted]:
    """``(configuration hits, comment markers, skip markers)`` of one file,
    the markers netted within it (:func:`_net_file`)."""
    comments_before, skips_before, config_before = _before_counts(path, before)
    hits: List[Dict[str, Any]] = []
    if _is_config(path):
        for kind, where, line, what in _config_findings(path, config_before, after):
            hits.append(_hit(where, line, kind, what, what, _config_reason(after, line)))
    comments: Dict[Tuple[str, ...], List[_Where]] = collections.defaultdict(list)
    for kind, marker, code, line, full, reason in _comment_markers(path, after):
        comments[(kind, marker, code)].append((path, line, full, reason))
    skips: Dict[Tuple[str, ...], List[_Where]] = collections.defaultdict(list)
    for name, encl, line, full, reason in _skip_markers(path, after):
        skips[(name, encl)].append((path, line, full, reason))
    return (hits, _net_file(comments_before, comments, edited_lines=True),
            _net_file(skips_before, skips, edited_lines=False))


def _net_across(netted: Sequence[_Netted]) -> List[Tuple[Tuple[str, ...], _Where]]:
    """The added markers of every file, less one for each marker of the same
    key a file lost without an edited line to match it: a line the batch
    moved from one of its files to another."""
    left: collections.Counter = collections.Counter()
    for _added, gone in netted:
        left.update(gone)
    out = []
    for added, _gone in netted:
        for key, where in added:
            if left[key] > 0:
                left[key] -= 1
                continue
            out.append((key, where))
    return out


def scan_changes(
    changes: Iterable[Tuple[str, Before, Optional[str]]],
    not_scanned: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, Any]]:
    """The markers the changes added, sorted by path and line.

    *changes* holds ``(path, before, after)`` for every file one batch
    changed: *path* repository-relative, *before* its text before the batch
    (or :func:`before_side`'s record of it, or ``None`` for a file the batch
    created), *after* its text now (``None`` for a file it deleted). Files
    :func:`scannable` declines are skipped. A file the scan fails on is
    left out, so the others still report, and named in *not_scanned* as
    ``{path, why}`` when the caller passes a list.

    Each hit is ``{path, line, kind, marker, text, reason}``: *kind* is
    ``comment-marker:<name>``, ``skip-marker:<name>`` or a configuration
    finding (``cfg-ignore-entry``, ``cfg-loosened-threshold``,
    ``cfg-select-removed``, ``cfg-changed``, ``new-lint-config``); *line* is
    1-based in the after text (0 when the finding has no line, a removed
    key); *text* is that line, redacted and clipped; *reason* is the words
    beside the marker (``above: …`` when they are on the comment line
    above), or ``None`` when it carries none.

    A marker counts as added only past the nettings: per file on its kind,
    text and the code on its line (a skip on its name and the function
    around it); for a comment marker only, per file on its kind and text
    alone, so editing the line of a marker the file already held does not
    add it (the two lines must share more than half their words,
    :data:`PAIRING_MIN_ALIKE`); and across the batch's files on the whole
    key, so a line moved between them is not reported. A skip moved to
    another test of the same file, a renamed skipped test and an edited
    JavaScript skip line are reported.
    """
    hits: List[Dict[str, Any]] = []
    comments: List[_Netted] = []
    skips: List[_Netted] = []
    for raw_path, before, after in changes:
        path = str(raw_path).replace("\\", "/")
        if not scannable(path):
            continue
        try:
            found, file_comments, file_skips = _scan_file(path, before, after)
        except Exception as exc:  # noqa: BLE001 - one odd file must not cost the others their hits
            if not_scanned is not None:
                not_scanned.append({"path": path, "why": "the scan failed on it (" + clip(
                    redact_text(f"{type(exc).__name__}: {exc}"), REASON_MAX_CHARS) + ")"})
            continue
        hits += found
        comments.append(file_comments)
        skips.append(file_skips)
    for key, (path, line, full, reason) in _net_across(comments):
        hits.append(_hit(path, line, "comment-marker:" + key[0],
                         _shown_marker(path, key[0], key[1]), full, reason))
    for key, (path, line, full, reason) in _net_across(skips):
        if key[0] == _UNPARSEABLE:
            hits.append(_hit(path, 0, "unparseable", UNPARSEABLE_MARKER, "", None))
            continue
        hits.append(_hit(path, line, "skip-marker:" + key[0], key[0], full, reason))
    return sorted(hits, key=lambda hit: (hit["path"], hit["line"], hit["kind"], hit["text"]))


# ---------------------------------------------------------------------------
# What a person reads
# ---------------------------------------------------------------------------

ByTask = List[Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]]


def from_rows(rows: Iterable[Mapping[str, Any]]) -> ByTask:
    """``(task id, hits, not scanned)`` for each batch report row that has
    any, in the rows' order; an earlier run's row is named so."""
    out: ByTask = []
    for row in rows:
        hits = [dict(hit) for hit in row.get("suppressions") or [] if isinstance(hit, Mapping)]
        unscanned = [
            dict(entry) for entry in row.get("suppressions_not_scanned") or []
            if isinstance(entry, Mapping)
        ]
        if hits or unscanned:
            label = str(row.get("task_id") or "?") + (
                " (earlier run)" if row.get("from_earlier_run") else "")
            out.append((label, hits, unscanned))
    return out


def _code(text: str) -> str:
    """*text* as inline Markdown code, fenced past any backquote it holds."""
    text = str(text)
    fence = "``" if "`" in text else "`"
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _where(hit: Mapping[str, Any]) -> str:
    line = int(hit.get("line") or 0)
    return f"{hit.get('path')}:{line}" if line > 0 else str(hit.get("path"))


def hit_line(hit: Mapping[str, Any], task_id: Optional[str] = None) -> str:
    """One hit as ``path:line marker — reason (task): line``, plain text,
    for a marker line on stdout."""
    reason = hit.get("reason")
    said = f"reason: {reason}" if reason else "no reason given"
    by = f" ({task_id})" if task_id else ""
    return f"{_where(hit)} {hit.get('marker')} — {said}{by}: {hit.get('text')}"


def _bullet(hit: Mapping[str, Any], task_id: str) -> str:
    reason = hit.get("reason")
    said = f"reason: {reason.replace('|', '/')}" if reason else "**no reason given**"
    kind = str(hit.get("kind") or "")
    shown = _code(hit.get("text") or "") if not kind.startswith(("cfg-", "new-lint")) else ""
    return (
        f"- {_code(_where(hit))} {_code(hit.get('marker') or '')} — {said} — "
        f"{task_id}" + (f" — {shown}" if shown else "")
    )


def section_lines(
    by_task: Sequence[Tuple[str, Sequence[Mapping[str, Any]], Sequence[Mapping[str, Any]]]],
) -> List[str]:
    """``summary.md``'s section for a phase, or ``[]`` with nothing to list.

    *by_task* holds ``(task id, hits, not scanned)`` per batch in its order;
    a not-scanned entry is ``{path, why}``: a file the batch changed whose
    bytes before it are not on record.
    """
    bullets: List[str] = []
    unscanned: List[str] = []
    for task_id, hits, skipped in by_task:
        bullets += [_bullet(hit, task_id) for hit in hits]
        unscanned += [
            f"- {_code(str(entry.get('path')))} — {task_id}: not scanned, "
            f"{entry.get('why') or 'its bytes before the batch are not on record'}"
            for entry in skipped
        ]
    if not bullets and not unscanned:
        return []
    lines = ["", CHECK_THESE_HEADING, ""]
    if bullets:
        lines += [
            "The batches added these suppression or skip markers, or changed "
            "this lint, type-checker or test configuration. None of them "
            "failed the run. Read each one: keep it only where the code is "
            "right as written and the reason holds. A line number is where "
            "the line was when its batch finished.",
            "",
        ] + bullets
    if unscanned:
        lines += ([""] if bullets else []) + [
            "These files changed but were not scanned for suppressions:",
            "",
        ] + unscanned
    return lines


def notice_clause(by_task: ByTask, *, where: str = "summary.md") -> Optional[str]:
    """The result notice's words for a phase's hits, or ``None`` without any."""
    hits = [hit for _task, found, _skipped in by_task for hit in found]
    if not hits:
        return None
    bare = sum(1 for hit in hits if not hit.get("reason"))
    shown = ", ".join(
        f"{_where(hit)} {hit.get('marker')}" for hit in hits[:3]
    ) + (f", +{len(hits) - 3} more" if len(hits) > 3 else "")
    return (
        f"check these: the batches added {len(hits)} suppression(s) or check "
        f"change(s)" + (f", {bare} with no reason given" if bare else "")
        + f" ({shown}), listed under \"{CHECK_THESE_HEADING.lstrip('# ')}\" "
        f"in {where}"
    )
