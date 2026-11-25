#!/usr/bin/env python3
"""Validate the skill's internal references and links.

Portable: standard library only. Safe: reads local files only, never needs a
bot token, never touches the network, never sends a Telegram message.

Checks:
  * Every relative path referenced from SKILL.md (references/*.md, evals/*.md,
    scripts/*, agents/*) actually exists.
  * Every markdown link target that is a local relative path resolves.
  * No reference/eval file is empty.
  * Reference files that exist but are never linked from SKILL.md are reported
    as warnings (possible orphans).
  * Every references/**/*.md starts with front-matter holding exactly `summary`
    (one sentence, at most 200 chars), `verified` (a real YYYY-MM-DD date) and
    `bot_api` (e.g. "10.5"), followed by the H1 title.
  * A reference larger than 10 KB has a `## Contents` section, and every link in
    it points to a heading of the same file (GitHub anchor rules).
  * No bot token / obvious secret appears in any bundled file.

Exit code 0 on success, 1 on any error. Warnings do not fail the run.

Usage:  python scripts/validate_references.py
"""
from __future__ import annotations

import datetime
import os
import re
import sys
import unicodedata

TOKEN_RE = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b")
# Local relative references we care about (in backticks, prose, or md links).
PATH_RE = re.compile(r"(?:references|evals|scripts|agents|recipes|examples|tests)/[A-Za-z0-9._/-]+")
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".claude"}  # .claude: local agent worktrees
MD_LINK_RE = re.compile(r"\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")

FRONT_KEYS = ("summary", "verified", "bot_api")
SUMMARY_MAX = 200
CONTENTS_MIN_BYTES = 10_000  # a reference larger than this needs a "## Contents" list
FRONT_LINE_RE = re.compile(r'^([A-Za-z_]+):[ \t]*"(.*)"[ \t]*$')
BOT_API_RE = re.compile(r"^\d+\.\d+$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
FENCE_RE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
MD_LINK_TEXT_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
CONTENTS_LINK_RE = re.compile(r"\]\(#([^)\s]+)\)")


def skill_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip_code(text: str) -> str:
    """Drop fenced blocks and inline code so `[text](url)` examples inside
    backticks aren't mistaken for real markdown links."""
    return INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))


def is_local(target: str) -> bool:
    t = target.strip()
    if not t or t.startswith("#"):
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", t):  # scheme://
        return False
    if t.startswith("mailto:") or t.startswith("tg:"):
        return False
    return True


def routing_files(root: str) -> list[str]:
    """SKILL.md routes to a command; the command's playbook and index route to references."""
    files = [os.path.join(root, "SKILL.md"), os.path.join(root, "commands", "index.json")]
    commands = os.path.join(root, "commands")
    if os.path.isdir(commands):
        files += [os.path.join(commands, n) for n in sorted(os.listdir(commands)) if n.endswith(".md")]
    return [f for f in files if os.path.isfile(f)]


def split_front_matter(text: str) -> tuple[list[str] | None, str]:
    """Return (front-matter lines, body); lines is None when the file has no front-matter."""
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:])
    return None, text


def check_front_matter(fm: list[str] | None) -> list[str]:
    if fm is None:
        return ["missing front-matter (--- summary, verified, bot_api ---) at the top"]
    problems: list[str] = []
    meta: dict[str, str] = {}
    for line in fm:
        if not line.strip():
            continue
        m = FRONT_LINE_RE.match(line)
        if not m:
            problems.append(f'front-matter line is not `key: "value"`: {line[:60]}')
            continue
        key, value = m.group(1), m.group(2)
        if key not in FRONT_KEYS:
            problems.append(f"front-matter has an unknown key: {key}")
        elif key in meta:
            problems.append(f"front-matter repeats key: {key}")
        meta[key] = value
    for key in FRONT_KEYS:
        if key not in meta:
            problems.append(f"front-matter lacks `{key}`")
    summary = meta.get("summary")
    if summary is not None and not summary.strip():
        problems.append("front-matter `summary` is empty")
    elif summary is not None and len(summary) > SUMMARY_MAX:
        problems.append(f"front-matter `summary` is {len(summary)} chars (max {SUMMARY_MAX})")
    verified = meta.get("verified")
    if verified is not None:
        try:
            ok = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", verified))
            if ok:
                datetime.date.fromisoformat(verified)
        except ValueError:
            ok = False
        if not ok:
            problems.append(f"front-matter `verified` is not a valid YYYY-MM-DD date: {verified!r}")
    bot_api = meta.get("bot_api")
    if bot_api is not None and not BOT_API_RE.match(bot_api):
        problems.append(f'front-matter `bot_api` is not a version like "10.5": {bot_api!r}')
    return problems


def github_anchor(heading: str) -> str:
    """The id GitHub gives a heading (before the -1, -2 suffix for duplicates)."""
    text = MD_LINK_TEXT_RE.sub(r"\1", heading).lower()
    kept = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in "- " or cat[0] in "LMN" or cat == "Pc":
            kept.append(ch)
    return "".join(kept).replace(" ", "-")


def parse_headings(body: str) -> list[tuple[int, int, str, str]]:
    """(line index, level, text, anchor) of every ATX heading outside code fences."""
    found: list[tuple[int, int, str, str]] = []
    seen: dict[str, int] = {}
    fence = ""
    for idx, line in enumerate(body.split("\n")):
        f = FENCE_RE_LINE.match(line)
        if f:
            run = f.group(1)
            if not fence:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not line.strip().strip(run[0]):
                fence = ""
            continue
        if fence:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        text = (m.group(2) or "").strip()
        base = github_anchor(text)
        n = seen.get(base, 0)
        seen[base] = n + 1
        found.append((idx, len(m.group(1)), text, base if n == 0 else f"{base}-{n}"))
    return found


def check_contents(body: str, size: int) -> list[str]:
    headings = parse_headings(body)
    contents = next((h for h in headings if h[1] == 2 and h[2] == "Contents"), None)
    if contents is None:
        if size > CONTENTS_MIN_BYTES:
            return [f"file is {size} bytes (> {CONTENTS_MIN_BYTES}) and has no `## Contents` section"]
        return []
    lines = body.split("\n")
    later = [h[0] for h in headings if h[0] > contents[0]]
    section = lines[contents[0] + 1:(later[0] if later else len(lines))]
    targets = CONTENTS_LINK_RE.findall("\n".join(section))
    if not targets:
        return ["`## Contents` has no `[heading](#anchor)` links"]
    anchors = {h[3] for h in headings}
    return [f"Contents link points to a missing heading: #{t}" for t in targets if t not in anchors]


def check_reference(content: str, generated_index: bool = False) -> list[str]:
    """Front-matter and Contents problems of one references/**/*.md file. The generated
    references/INDEX.md is itself a contents list, so it needs no `## Contents`."""
    fm, body = split_front_matter(content)
    problems = check_front_matter(fm)
    first = next((ln for ln in body.split("\n") if ln.strip()), "")
    if fm is not None and not first.startswith("# "):
        problems.append("the H1 title must follow the front-matter")
    if generated_index:
        return problems
    return problems + check_contents(body, len(content.encode("utf-8")))


def collect_referenced_paths(root: str) -> set[str]:
    refs: set[str] = set()
    for path in routing_files(root):
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        for m in PATH_RE.findall(text):
            refs.add(m.strip("`.,);:\""))
        for target in MD_LINK_RE.findall(strip_code(text)):
            target = target.split("#", 1)[0].strip()
            if is_local(target):  # a Markdown link is relative to the file that holds it, not to the skill root
                full = os.path.normpath(os.path.join(os.path.dirname(path), target))
                refs.add(os.path.relpath(full, root).replace(os.sep, "/"))
    return refs


def main() -> int:
    root = skill_dir()
    errors: list[str] = []
    warnings: list[str] = []

    if not os.path.isfile(os.path.join(root, "SKILL.md")):
        print("FAIL: SKILL.md not found.")
        return 1

    referenced = collect_referenced_paths(root)

    # 1) every referenced path exists
    for rel in sorted(referenced):
        if not os.path.exists(os.path.join(root, rel)):
            errors.append(f"SKILL.md or a command playbook references missing path: {rel}")

    # 2) bundled markdown files: non-empty, links resolve, no secrets
    linked_refs: set[str] = set()
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            fpath = os.path.join(dirpath, fname)
            rel = os.path.relpath(fpath, root).replace(os.sep, "/")
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except OSError as exc:
                errors.append(f"cannot read {rel}: {exc}")
                continue

            if TOKEN_RE.search(content):
                errors.append(f"possible bot token / secret in {rel}")

            if fname.lower().endswith(".md"):
                if not content.strip():
                    errors.append(f"empty markdown file: {rel}")
                elif rel.startswith("references/"):
                    errors.extend(f"{rel}: {p}" for p in check_reference(content, rel == "references/INDEX.md"))
                base = os.path.dirname(fpath)
                for target in MD_LINK_RE.findall(strip_code(content)):
                    tgt = target.split("#", 1)[0].strip()
                    if not is_local(tgt):
                        continue
                    linked_refs.add(
                        os.path.relpath(os.path.normpath(os.path.join(base, tgt)), root)
                        .replace(os.sep, "/")
                    )
                    if not os.path.exists(os.path.normpath(os.path.join(base, tgt))):
                        errors.append(f"broken link in {rel}: {tgt}")

    # 3) orphan reference files (exist but never mentioned in SKILL.md)
    refs_dir = os.path.join(root, "references")
    if os.path.isdir(refs_dir):
        for fname in sorted(os.listdir(refs_dir)):
            if not fname.endswith(".md"):
                continue
            rel = f"references/{fname}"
            if rel not in referenced and rel not in linked_refs:
                warnings.append(f"reference not routed from SKILL.md or a command: {rel}")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s). INVALID.")
        return 1
    print(
        f"\nOK: references consistent "
        f"({len(referenced)} referenced path(s)). {len(warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
