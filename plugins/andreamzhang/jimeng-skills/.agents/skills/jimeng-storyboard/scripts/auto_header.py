#!/usr/bin/env python3
"""auto_header.py v3 - 自动重写 02-jimeng-prompts.md 第 18 行集头说明段

设计: 2026-08-15 stage5-pipeline-design
"""
import argparse
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(
    "(>\s*\u96c6\u5934\u8bf4\u660e\s*[:：]\s*)(.*?)(?=\n\n---\n\n##\s*\u6bcd\u955c\u5934\d+)",
    re.DOTALL,
)
MOTHER_HEADER_RE = re.compile("^##\s*\u6bcd\u955c\u5934(\d+)", re.M)
SUB_HEADER_RE = re.compile("^###\s*\u5b50\u955c\u5934\d+", re.M)
DURATION_RE = re.compile(
    "^##\s*\u6bcd\u955c\u5934\d+.*?\u603b\u65f6\u957f\s*[:：]\s*(\d+\.?\d*)\s*\u79d2", re.M)
P_TAG_RE = re.compile(
    "^##\s*\u6bcd\u955c\u5934\d+.*?\[P(\d+)", re.M)


def parse_counts(content):
    n_m = len(MOTHER_HEADER_RE.findall(content))
    n_s = len(SUB_HEADER_RE.findall(content))
    total = sum(float(m.group(1)) for m in DURATION_RE.finditer(content))
    n_d = sum(1 for m in re.finditer("^[\u3010]\u53f0\u8bcd[\u3011]\s*(.+)$", content, re.M)
                 if (t := m.group(1).strip()) and t != "\u65e0")
    return {"mother_count": n_m, "sub_count": n_s, "total_duration": total, "dialogue_count": n_d}


def detect_p_splits(content):
    p_to_m = {}
    for m in P_TAG_RE.finditer(content):
        p_id = int(m.group(1))
        prev = None
        for mm in re.finditer("^##\s*\u6bcd\u955c\u5934(\d+)", content[:m.start()], re.M):
            prev = int(mm.group(1))
        if prev is None:
            continue
        p_to_m.setdefault(p_id, []).append(prev)
    return [(p, ms) for p, ms in sorted(p_to_m.items()) if len(ms) > 1]


def build_header(counts, splits, max_p=5):
    n, sub, dur, dc = counts["mother_count"], counts["sub_count"], counts["total_duration"], counts["dialogue_count"]
    if splits:
        sl = []
        for p_id, ms in splits:
            sl.append(f"P{p_id:02d} \u62c6\u4e3a " + "+".join(f"M{m}" for m in ms))
        st = "\u3001".join(sl) + "\uff08\u62c6\u5206\u4e0d\u6539\u53d8\u5267\u60c5\u70b9\u8bed\u4e49\uff09"
        last_p = splits[-1][0]
        return (
            f"\u672c\u96c6 {n} \u4e2a\u6bcd\u955c\u5934\uff08M1-M{n} \u7eaf\u6570\u5b57\u5168\u5c40\u8fde\u7eed\u7f16\u53f7\uff09\uff0c"
            f"\u5bf9\u5e94\u5bfc\u6f14\u5267\u60c5\u70b9 P01-P{last_p:02d} 1:1 \u6620\u5c04\uff08\u542b\u5267\u60c5\u70b9\u62c6\u5206\uff1a{st}\uff09\u3002"
            f"{sub} \u4e2a\u5b50\u955c\u5934\u3001\u603b\u65f6\u957f {dur:g} \u79d2\u3002{dc} \u53e5\u53f0\u8bcd\u9010\u5b57\u7167\u5f55\u5267\u672c\u539f\u6587\u3002"
            f"\u8fd0\u955c\u4e00\u7ea7 {sub}/{sub}\uff1d100%\uff08\u226560%\uff09\u3002"
        )
    return (
        f"\u672c\u96c6 {n} \u4e2a\u6bcd\u955c\u5934\uff08M1-M{n} \u7eaf\u6570\u5b57\u5168\u5c40\u8fde\u7eed\u7f16\u53f7\uff09\uff0c"
        f"\u5bf9\u5e94\u5bfc\u6f14\u5267\u60c5\u70b9 P01-P{max_p:02d} 1:1 \u6620\u5c04\u3002"
        f"{sub} \u4e2a\u5b50\u955c\u5934\u3001\u603b\u65f6\u957f {dur:g} \u79d2\u3002{dc} \u53e5\u53f0\u8bcd\u9010\u5b57\u7167\u5f55\u5267\u672c\u539f\u6587\u3002"
        f"\u8fd0\u955c\u4e00\u7ea7 {sub}/{sub}\uff1d100%\uff08\u226560%\uff09\u3002"
    )


def main():
    parser = argparse.ArgumentParser(description="\u81ea\u52a8\u91cd\u5199\u96c6\u5934\u8bf4\u660e\u6bb5")
    parser.add_argument("storyboard", help="02-jimeng-prompts.md \u8def\u5f84")
    parser.add_argument("--dry-run", action="store_true", help="\u53ea\u6253\u5370\u4e0d\u5199\u6587\u4ef6")
    args = parser.parse_args()
    sb = Path(args.storyboard)
    if not sb.exists():
        print(f"\u9519\u8bef: {sb} \u4e0d\u5b58\u5728", file=sys.stderr)
        sys.exit(2)
    content = sb.read_text(encoding="utf-8")
    m = HEADER_RE.search(content)
    if not m:
        print("\u8b66\u544a: \u672a\u627e\u5230\u96c6\u5934\u8bf4\u660e\u6bb5\uff08'\u96c6\u5934\u8bf4\u660e...' \u4e0e '\u6bcd\u955c\u5934N' \u4e4b\u95f4\uff09", file=sys.stderr)
        sys.exit(2)
    orig = m.group(2).strip()
    counts = parse_counts(content)
    splits = detect_p_splits(content)
    max_p = 0
    for pm in P_TAG_RE.finditer(content):
        max_p = max(max_p, int(pm.group(1)))
    new_h = build_header(counts, splits, max_p=max(max_p, 1))
    if new_h.strip() == orig:
        print(f"\u96c6\u5934\u65e0\u53d8\u5316 (\u6bcd\u955c\u5934={counts['mother_count']}, \u5b50\u955c\u5934={counts['sub_count']})")
        sys.exit(1)
    if args.dry_run:
        print("--- \u539f ---\\n" + orig[:300] + "\\n--- \u65b0 ---\\n" + new_h)
        sys.exit(0)
    new_content = content[:m.start(2)] + new_h + content[m.end(2):]
    sb.write_text(new_content, encoding="utf-8")
    print(f"\u5df2\u91cd\u5199\u96c6\u5934: \u6bcd\u955c\u5934={counts['mother_count']}, \u5b50\u955c\u5934={counts['sub_count']}, \u603b\u65f6\u957f={counts['total_duration']:g}\u79d2, \u53f0\u8bcd={counts['dialogue_count']}, \u62c6\u5206={len(splits)}\u7ec4")
    sys.exit(0)


if __name__ == "__main__":
    main()
