#!/usr/bin/env python3
"""Scaffold a new research skill that passes the Research Agent Skills validators.

Creates skills/<name>/SKILL.md (spec-compliant frontmatter + body skeleton),
optional scripts/ and references/ folders, and evals/<name>/evals.json at the
repository root (evals are kept out of the installed skill).

Usage:
    python new_skill.py my-skill-name --category literature-review \
        --description "What it does. Use when ..." [--scripts] [--references] [--root /path/to/repo]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

SKILL_TEMPLATE = """---
name: {name}
description: {description}
license: MIT
compatibility: {compatibility}
metadata:
  version: "1.0"
  category: {category}
  maintainer: Kalaris Labs
  author: {author}
---

# {title}

One paragraph: the problem this skill solves for a researcher and what "done well" looks like.

## When to use

- Concrete trigger situations (mirror the phrases users actually type).

## Workflow

1. Step one: what to inspect or ask first.
2. Step two: the core procedure. Prefer checklists and decision tables over prose.
3. Step three: how to verify the result before handing it back.

## Rules

- Hard constraints (never fabricate data or citations; verify venue requirements from official sources; ...).

## Related skills

- `other-skill`: when to hand off.
"""

SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
"""One-line summary of what this script does.

Usage:
    python {script}.py INPUT [--json]

Exit codes: 0 ok, 1 findings, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import sys

for _stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = {{"input": args.input}}
    print(json.dumps(result, indent=2) if args.json else result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def find_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "skills").is_dir() and (p / "third_party" / "categories.yaml").is_file():
            return p
    sys.exit("could not find the repository root (a folder with skills/ and third_party/categories.yaml); pass --root")


def known_categories(root: Path) -> list[str]:
    text = (root / "third_party" / "categories.yaml").read_text(encoding="utf-8")
    block = text.split("categories:", 1)[1].split("\n\n", 1)[0]
    return re.findall(r"^  ([a-z0-9-]+):", block, re.M)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--category", required=True)
    ap.add_argument("--description", required=True, help="what it does + 'Use when ...' triggers (max 1024 chars)")
    ap.add_argument("--compatibility", default="No runtime dependencies.")
    ap.add_argument("--author", default="Kalaris Labs")
    ap.add_argument("--scripts", action="store_true")
    ap.add_argument("--references", action="store_true")
    ap.add_argument("--root", type=Path)
    args = ap.parse_args()

    root = args.root.resolve() if args.root else find_root(Path.cwd().resolve())
    if not NAME_RE.match(args.name) or len(args.name) > 64:
        sys.exit("name must be lowercase kebab-case, at most 64 characters")
    cats = known_categories(root)
    if args.category not in cats:
        sys.exit(f"unknown category '{args.category}'. Known: {', '.join(cats)}")
    if len(args.description) > 1024 or "use when" not in args.description.lower():
        sys.exit("description must be <= 1024 chars and include 'Use when ...' trigger phrases")
    if re.search(r"[<>]", args.description):
        sys.exit("description must not contain angle brackets")

    skill = root / "skills" / args.name
    if skill.exists():
        sys.exit(f"{skill} already exists")
    skill.mkdir(parents=True)
    title = args.name.replace("-", " ").title()
    desc = json.dumps(args.description, ensure_ascii=False)  # YAML-safe quoting
    (skill / "SKILL.md").write_text(SKILL_TEMPLATE.format(name=args.name, description=desc, category=args.category,
                                                          compatibility=json.dumps(args.compatibility),
                                                          author=json.dumps(args.author), title=title),
                                    encoding="utf-8", newline="\n")
    if args.scripts:
        (skill / "scripts").mkdir()
        script = args.name.replace("-", "_")
        (skill / "scripts" / f"{script}.py").write_text(SCRIPT_TEMPLATE.format(script=script), encoding="utf-8",
                                                          newline="\n")
    if args.references:
        (skill / "references").mkdir()
        (skill / "references" / "details.md").write_text(f"# {title}: details\n\nLong-form material loaded on demand.\n",
                                                         encoding="utf-8", newline="\n")
    evals = root / "evals" / args.name
    evals.mkdir(parents=True, exist_ok=True)
    (evals / "evals.json").write_text(json.dumps({
        "skill_name": args.name,
        "evals": [
            {"id": 1, "prompt": "A realistic user request that SHOULD trigger this skill", "expected_output":
             "What a correct, complete answer contains", "files": []},
            {"id": 2, "prompt": "A near-miss request that should NOT trigger this skill", "expected_output":
             "Skill not used", "files": [], "should_trigger": False},
        ],
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"created {skill.relative_to(root)} and {evals.relative_to(root)}/evals.json")
    print("next: fill in SKILL.md, then run  uv run tools/validate.py skills/" + args.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
