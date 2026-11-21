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
  * No bot token / obvious secret appears in any bundled file.

Exit code 0 on success, 1 on any error. Warnings do not fail the run.

Usage:  python scripts/validate_references.py
"""
from __future__ import annotations

import os
import re
import sys

TOKEN_RE = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b")
# Local relative references we care about (in backticks, prose, or md links).
PATH_RE = re.compile(r"(?:references|evals|scripts|agents|recipes|examples|tests)/[A-Za-z0-9._/-]+")
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".claude"}  # .claude: local agent worktrees
MD_LINK_RE = re.compile(r"\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


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


def collect_referenced_paths(root: str) -> set[str]:
    skill_md = os.path.join(root, "SKILL.md")
    refs: set[str] = set()
    with open(skill_md, "r", encoding="utf-8") as fh:
        text = fh.read()
    for m in PATH_RE.findall(text):
        refs.add(m.strip("`.,);:"))
    for target in MD_LINK_RE.findall(strip_code(text)):
        target = target.split("#", 1)[0].strip()
        if is_local(target):
            refs.add(target)
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
            errors.append(f"SKILL.md references missing path: {rel}")

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
                warnings.append(f"reference not linked from SKILL.md: {rel}")

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
