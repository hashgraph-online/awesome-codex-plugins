#!/usr/bin/env python3
"""Content-marker finalization check.

Scans the artifacts a course has produced for unresolved honesty markers —
`[NEEDS PROFESSOR INPUT: ...]` (institutional/contextual facts the suite refuses to
invent) and `[VERIFY: ...]` (domain claims the model could not confirm). These markers
are correct and expected in a draft; the point of this check is to make them VISIBLE at
finalization so a syllabus never reaches students with an unfilled policy, and a lesson
never goes out with an unverified claim. It is the gate-level counterpart to the
dashboard's display of these markers.

Usage:
  python3 scripts/check_content_markers.py <passport.yaml> [--strict]
  python3 scripts/check_content_markers.py --files a.md b.md [--strict]

Default: advisory (lists every marker with file:line, exit 0). `--strict` exits 1 if any
unresolved marker remains — use when finalizing (Stage 5 / Quality Gate T-checks).

Exit: 0 = ok (or advisory) · 1 = markers found under --strict · 2 = error
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MARKER = re.compile(r"\[(NEEDS PROFESSOR INPUT|VERIFY|MATERIAL GAP)\b[^\]]*\]")


def artifact_paths(passport_path):
    from check_passport import load_passport
    p = load_passport(passport_path)
    base = Path(passport_path).parent
    paths = []
    for a in p.get("artifacts") or []:
        if a.get("path"):
            paths.append(base / a["path"])
    for w in p.get("schedule") or []:
        for r in w.get("artifact_refs") or []:
            paths.append(base / r)
    # de-dup, keep only existing markdown/text
    seen, out = set(), []
    for fp in paths:
        if fp in seen:
            continue
        seen.add(fp)
        if fp.exists() and fp.suffix in (".md", ".txt", ""):
            out.append(fp)
    return out


def scan(files):
    findings = []
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in MARKER.finditer(line):
                findings.append({"file": str(fp), "line": i, "marker": m.group(0)})
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("passport", nargs="?")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.files:
            files = [Path(f) for f in args.files]
        elif args.passport:
            files = artifact_paths(args.passport)
        else:
            ap.error("provide a passport or --files")
            return 2
    except Exception as ex:
        print(f"error: {type(ex).__name__}: {ex}", file=sys.stderr)
        return 2

    findings = scan(files)
    for f in findings:
        print(f"[{f['marker'][1:].split(':')[0].split(']')[0]}] {f['file']}:{f['line']}  {f['marker']}")
    n = len(findings)
    needs = sum(1 for f in findings if f["marker"].startswith("[NEEDS"))
    verify = sum(1 for f in findings if f["marker"].startswith("[VERIFY"))
    print(f"{n} unresolved marker(s): {needs} NEEDS PROFESSOR INPUT, {verify} VERIFY, "
          f"{n - needs - verify} other across {len(files)} artifact(s)")
    if n and args.strict:
        print("STRICT: unresolved markers block finalization", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
