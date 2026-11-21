# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""给“要背的句子”打标：在讲义文字里逐字找得到的标【讲义原话】，找不到的标【转述】。

比对前统一：去掉所有空白，全角字母数字转半角，中英文标点统一，弯引号统一；已有的【…】标记先去掉。

用法：
  python tag_quotes.py --lecture 讲义1.md [讲义2.md …] --sentences 句子.md [--out 打标后.md]

句子文件一行一句，可以带列表符号（“1. ”“- ”）。输出保持原来的列表符号，在句子前加标记。
找不到的句子另外列出最像的一段讲义（前后 30 字），方便人工换成原话。
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata
from pathlib import Path

PUNCT = str.maketrans({"，": ",", "。": ".", "；": ";", "：": ":", "？": "?", "！": "!", "（": "(", "）": ")",
                       "“": '"', "”": '"', "‘": "'", "’": "'", "「": '"', "」": '"', "、": ",", "—": "-", "－": "-"})
# “- ”“1. ”“1) ”后面必须有空白，免得把“1.5 倍”“-1”的开头当成列表符号；“1、”“（1）”可以不带空白
LIST_MARK = re.compile(r"^(\s*(?:(?:[-*+]|\d+[.)])\s+|\d+、\s*|[（(]\d+[）)]\s*))")
OLD_TAG = re.compile(r"^【(?:讲义原话|转述)】\s*")
SEP = "\x00"  # 讲义文件之间的分隔符；句子规范化后不会含它，所以匹配不会跨文件


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).translate(PUNCT)
    return re.sub(r"\s+", "", s)


def build_corpus(texts: list[str]) -> str:
    """每份讲义各自规范化，用 SEP 隔开，一句话只能在某一份讲义里整句命中。"""
    return SEP.join(norm(t) for t in texts)


def tag_line(line: str, corpus: str) -> tuple[str, bool]:
    m = LIST_MARK.match(line)
    prefix = m.group(1) if m else ""
    body = OLD_TAG.sub("", line[len(prefix):].strip())
    found = bool(body) and norm(body) in corpus
    return f"{prefix}{'【讲义原话】' if found else '【转述】'}{body}", found


def nearest(body: str, raw_corpus: str) -> str:
    n = norm(body)
    if not n:
        return ""
    sm = difflib.SequenceMatcher(None, raw_corpus, n, autojunk=False)
    m = sm.find_longest_match(0, len(raw_corpus), 0, len(n))
    a = max(m.a - 30, 0)
    return raw_corpus[a:m.a + m.size + 30].replace(SEP, " ‖ ")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="给要背的句子打【讲义原话】/【转述】")
    ap.add_argument("--lecture", type=Path, nargs="+", required=True)
    ap.add_argument("--sentences", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    corpus = build_corpus([p.read_text(encoding="utf-8") for p in a.lecture])
    out, misses = [], []
    for line in a.sentences.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            out.append(line)
            continue
        tagged, ok = tag_line(line, corpus)
        out.append(tagged)
        if not ok:
            misses.append(tagged)
    text = "\n".join(out) + "\n"
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    total = sum(1 for line in out if line.strip())
    print(f"\n合计 {total} 句：讲义原话 {total - len(misses)}，转述 {len(misses)}", file=sys.stderr)
    for t in misses:
        body = OLD_TAG.sub("", LIST_MARK.sub("", t).strip())
        print(f"  转述：{body}\n    讲义里最像的一段：{nearest(body, corpus)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
