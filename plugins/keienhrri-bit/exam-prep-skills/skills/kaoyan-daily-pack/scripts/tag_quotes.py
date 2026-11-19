# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""给“要背的句子”打标：在讲义文字里逐字找得到的标【讲义原话】，找不到的标【转述】。

比对前统一：去掉所有空白，全角字母数字转半角，中英文标点统一，弯引号统一；已有的【…】标记先去掉。

用法：
  python tag_quotes.py --lecture 讲义1.md [讲义2.md …] --sentences 句子.md [--out 打标后.md]

句子文件一行一句，可以带列表符号（“1. ”“1)”“- ”）。输出保持原来的列表符号，在句子前加标记。
标准错误输出会列出命中句的行号和第一份命中讲义，并给转述句附上最像的一段讲义（前后 30 字）。
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
# 正负号和数字加点后要求有空白，以保留行首的数值。“1)”“1、”“（1）”可以紧接正文。
LIST_MARK = re.compile(r"^(\s*(?:(?:[-*+]|\d+\.)\s+|\d+[)、]\s*|[（(]\d+[）)]\s*))")
OLD_TAG = re.compile(r"^【(?:讲义原话|转述)】\s*")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).translate(PUNCT)
    return re.sub(r"\s+", "", s)


def build_corpus(texts: list[str]) -> list[str]:
    """保留每份讲义的独立边界。"""
    return [norm(text) for text in texts]


def tag_with_source(line: str, corpus: list[str]) -> tuple[str, int | None]:
    m = LIST_MARK.match(line)
    prefix = m.group(1) if m else ""
    body = OLD_TAG.sub("", line[len(prefix):].strip())
    normalized = norm(body)
    source = next((i for i, lecture in enumerate(corpus) if normalized in lecture), None) if normalized else None
    tag = "【讲义原话】" if source is not None else "【转述】"
    return f"{prefix}{tag}{body}", source


def tag_line(line: str, corpus: str | list[str]) -> tuple[str, bool]:
    tagged, source = tag_with_source(line, [corpus] if isinstance(corpus, str) else corpus)
    return tagged, source is not None


def nearest(body: str, corpus: list[str]) -> str:
    normalized = norm(body)
    if not normalized:
        return ""
    best_size, snippet = -1, ""
    for lecture in corpus:
        match = difflib.SequenceMatcher(None, lecture, normalized, autojunk=False).find_longest_match()
        if match.size > best_size:
            best_size = match.size
            snippet = lecture[max(match.a - 30, 0):match.a + match.size + 30]
    return snippet


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="给要背的句子打【讲义原话】/【转述】")
    ap.add_argument("--lecture", type=Path, nargs="+", required=True)
    ap.add_argument("--sentences", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    corpus = build_corpus([p.read_text(encoding="utf-8") for p in a.lecture])
    out, sources, misses = [], [], []
    for number, line in enumerate(a.sentences.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            out.append(line)
            continue
        tagged, source = tag_with_source(line, corpus)
        out.append(tagged)
        if source is None:
            misses.append(tagged)
        else:
            sources.append((number, source))
    text = "\n".join(out) + "\n"
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    total = sum(1 for line in out if line.strip())
    print(f"\n合计 {total} 句：讲义原话 {total - len(misses)}，转述 {len(misses)}", file=sys.stderr)
    for number, source in sources:
        print(f"  第 {number} 行命中讲义 {source + 1}（{a.lecture[source].name}）", file=sys.stderr)
    for t in misses:
        body = OLD_TAG.sub("", LIST_MARK.sub("", t).strip())
        print(f"  转述：{body}\n    讲义里最像的一段：{nearest(body, corpus)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
