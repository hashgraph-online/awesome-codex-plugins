#!/usr/bin/env python3
"""Find "AI slop" in academic prose: stock phrasing, empty emphasis, formulaic rhythm.

Reads Markdown, LaTeX, plain text or .docx. LaTeX math, citations, code, URLs and
comments are ignored so only prose is judged. Reports findings with line numbers,
a rewrite hint for each, rhythm statistics, and a slop index (weighted findings
per 1,000 words, plus rhythm penalties).

Usage:
    python slop_check.py draft.tex
    python slop_check.py paper.md --json > slop.json
    python slop_check.py intro.txt --max 10           # exit 1 if index > 10
    cat abstract.txt | python slop_check.py -

Index bands: < 5 clean · 5-15 some slop · 15-30 heavy · > 30 severe.
Exit codes: 0 at or under --max (default 15), 1 over, 2 bad input. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import zipfile
from dataclasses import asdict, dataclass

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# (regex, weight, category, hint). Weights: 10 chat residue, 3 signature slop, 1.5 common, 0.5 mild.
PATTERNS: list[tuple[str, float, str, str]] = [
    # Chat and assistant residue: never acceptable in a manuscript.
    (r"\b(as an ai( language model)?|i hope this helps|certainly!|great question|let me know if you|"
     r"here(?:'s| is) (?:a|an|the) (?:revised|improved|rewritten) (?:version|draft))\b", 10, "chat-residue",
     "Delete: assistant boilerplate left in the text."),
    (r"\b(i apologi[sz]e|as of my (?:last )?knowledge (?:cutoff|update))\b", 10, "chat-residue",
     "Delete: model disclaimer."),
    # Signature vocabulary.
    (r"\bdelv(?:e|es|ed|ing)\b", 3, "stock-vocabulary", "Say what you examine: 'we analyse', 'we measure'."),
    (r"\b(?:rich |intricate |complex )?tapestry\b", 3, "stock-vocabulary", "Name the actual components or interactions."),
    (r"\b(?:ever-evolving|rapidly evolving|ever-changing) (?:landscape|field|world)\b", 3, "stock-vocabulary",
     "Replace with the concrete change and its timeframe."),
    (r"\bin (?:today's|the modern|the current) (?:world|era|landscape|age)\b", 3, "stock-vocabulary",
     "Cut, or state the specific current condition that matters."),
    (r"\b(?:the )?realm of\b", 3, "stock-vocabulary", "Name the field: 'in protein design', not 'in the realm of'."),
    (r"\bnavigat(?:e|es|ing) the (?:complexities|landscape|challenges)\b", 3, "stock-vocabulary",
     "State the specific difficulty and how it is handled."),
    (r"\b(?:is|serves as|stands as) a testament to\b", 3, "stock-vocabulary", "Say what the evidence shows."),
    (r"\bunderscor(?:e|es|ed|ing) the (?:importance|need|significance|critical)\b", 3, "stock-vocabulary",
     "Show the importance with a consequence or number instead."),
    (r"\bplays? an? (?:pivotal|crucial|vital|key|critical|significant|important) role\b", 3, "stock-vocabulary",
     "Replace with the mechanism: 'X regulates Y', 'X accounts for 40% of Y'."),
    (r"\bpav(?:e|es|ed|ing) the way (?:for|to)\b", 1.5, "stock-vocabulary", "Say what becomes possible, concretely."),
    (r"\bshed(?:s|ding)? (?:new )?light on\b", 1.5, "stock-vocabulary", "Say what was learned: 'shows that', 'explains why'."),
    (r"\b(?:multifaceted|paramount|seamless(?:ly)?|meticulous(?:ly)?|intricacies|holistic)\b", 1.5,
     "stock-vocabulary", "Use a precise word or cut."),
    (r"\b(?:leverag(?:e|es|ed|ing)|harness(?:es|ed|ing)?|unlock(?:s|ed|ing)?|empower(?:s|ed|ing)?)\b", 1.5,
     "stock-vocabulary", "Prefer 'use', 'apply', 'enable' or the specific action."),
    (r"\b(?:showcas(?:e|es|ed|ing)|boast(?:s|ed|ing)?|garner(?:s|ed|ing)?)\b", 1.5, "stock-vocabulary",
     "Prefer 'show', 'have', 'receive'."),
    (r"\b(?:a )?(?:myriad|plethora) of\b", 1.5, "stock-vocabulary", "Give the number or say 'many'."),
    (r"\b(?:game[- ]chang(?:er|ing)|groundbreaking|revolutioni[sz](?:e|es|ed|ing)|paradigm[- ]shift(?:ing)?|"
     r"cutting[- ]edge|unprecedented)\b", 3, "promotional", "Remove hype; let the result carry the claim."),
    (r"\b(?:remarkabl[ey]|incredibl[ey]|truly|undeniabl[ey]|profound(?:ly)?)\b", 1.5, "empty-emphasis",
     "Cut the intensifier or quantify."),
    # Formulaic signposting and filler.
    (r"\bit is (?:important|worth|crucial|essential|interesting) to (?:note|mention|highlight|emphasi[sz]e) that\b", 3,
     "filler", "Delete the frame and state the point."),
    (r"\b(?:it should be noted|it is worth noting|needless to say|it goes without saying)\b", 3, "filler",
     "Delete the frame and state the point."),
    (r"\b(?:in order to)\b", 0.5, "filler", "Use 'to'."),
    (r"\b(?:due to the fact that|in light of the fact that|owing to the fact that)\b", 1.5, "filler", "Use 'because'."),
    (r"\b(?:a wide (?:range|variety|array) of|a diverse (?:range|array) of)\b", 1.5, "filler",
     "Name the members or give the count."),
    (r"\b(?:in (?:the )?(?:realm|context|field|domain|area) of)\b", 0.5, "filler", "Often removable."),
    (r"^\s*(?:in conclusion|in summary|to sum up|overall|ultimately),", 1.5, "signposting",
     "Cut the label; the section heading already signals the conclusion."),
    # Constructions.
    (r"\bnot (?:only|just|merely) [^.;:]{1,80}?,? but (?:also )?", 3, "construction",
     "State both points plainly, or keep the stronger one."),
    (r"\b(?:isn't|is not|wasn't|was not) (?:just|merely|simply) (?:about )?[^.;]{1,60}?[,;—-]+ (?:it's|it is|but)\b", 3,
     "construction", "Drop the 'not X, it's Y' reveal; state Y."),
    # Hedging stacks (hedging itself is fine; stacking two or more is not).
    (r"\b(?:may|might|could) (?:potentially|possibly|perhaps|conceivably)\b", 3, "hedge-stack",
     "Keep one hedge sized to the evidence."),
    (r"\b(?:potentially|possibly) (?:suggest|indicate|imply)s?\b", 1.5, "hedge-stack", "One hedge is enough."),
    (r"\b(?:seems|appears) to (?:potentially|possibly|suggest that it may)\b", 3, "hedge-stack",
     "Keep one hedge sized to the evidence."),
]
SENTENCE_START_TRANSITIONS = re.compile(
    r"^(?:moreover|furthermore|additionally|in addition|consequently|thus|hence|therefore|notably|importantly|"
    r"interestingly|crucially|ultimately|overall|indeed)\b", re.I)
STATS_CONTEXT = re.compile(r"(p\s*[<=>≤]|\bci\b|confidence interval|\bt\(|\bf\(|χ2|chi-square|\bz\s*=|effect size|"
                           r"cohen|odds ratio|hazard ratio|relative risk|\b(?:hr|or|rr|aor|ahr)\b|95\s*%|"
                           r"statistical|anova|regression|test\b|\bα|alpha\s*=)", re.I)
COMPILED = [(re.compile(p, re.I | re.M), w, c, h) for p, w, c, h in PATTERNS]


@dataclass
class Finding:
    line: int
    category: str
    weight: float
    match: str
    hint: str


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Return (line number, prose-only text) pairs with code, math, citations and markup removed."""
    out: list[tuple[int, str]] = []
    in_fence = False
    skip_env = 0
    envs = r"(?:equation|align|gather|multline|eqnarray|verbatim|lstlisting|minted|tikzpicture|tabular|table|figure)\*?"
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw
        if line.strip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if re.search(rf"\\begin\{{{envs}\}}", line):
            skip_env += 1
        if skip_env:
            if re.search(rf"\\end\{{{envs}\}}", line):
                skip_env -= 1
            continue
        line = re.sub(r"(?<!\\)%.*", "", line)                              # LaTeX comments
        line = re.sub(r"\$\$.*?\$\$|\$[^$]*\$|\\\(.*?\\\)|\\\[.*?\\\]", " ", line)  # math
        line = re.sub(r"\\(?:cite[tp]?|citep|citet|ref|eqref|label|autoref|cref|url|href)\*?(?:\[[^\]]*\])*\{[^}]*\}", " ", line)
        line = re.sub(r"\\(?:textbf|textit|emph|underline|section|subsection|subsubsection|paragraph|caption)\*?\{([^}]*)\}",
                      r"\1", line)
        line = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", line)          # remaining commands
        line = re.sub(r"`[^`]*`", " ", line)                                # inline code
        line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)              # markdown links/images
        line = re.sub(r"https?://\S+", " ", line)
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)                       # markdown headings
        line = re.sub(r"[{}]", "", line)
        if line.strip():
            out.append((n, line))
    return out


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\b(e\.g|i\.e|et al|cf|vs|Fig|Figs|Eq|Eqs|Tab|approx|resp|ca|Dr|Mr|Ms|No)\.", r"\1<DOT>", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text)
    return [p.replace("<DOT>", ".").strip() for p in parts if len(p.split()) >= 3]


def analyse(text: str) -> dict:
    lines = prose_lines(text)
    prose = "\n".join(t for _, t in lines)
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", prose)
    n_words = max(len(words), 1)
    findings: list[Finding] = []
    for n, t in lines:
        for rx, w, cat, hint in COMPILED:
            for m in rx.finditer(t):
                findings.append(Finding(n, cat, w, m.group(0).strip(), hint))
        # "significant(ly)" used for emphasis with no statistics nearby
        for m in re.finditer(r"\bsignificant(?:ly)?\b", t, re.I):
            window = t[max(0, m.start() - 120): m.end() + 120]
            if not STATS_CONTEXT.search(window):
                findings.append(Finding(n, "unsupported-significance", 1.5, m.group(0),
                                        "In research writing 'significant' implies a statistical test: add it, or "
                                        "use 'substantial'/'large' with a number."))
    paragraphs = [p for p in re.split(r"\n\s*\n", "\n".join(t for _, t in lines)) if len(p.split()) >= 15]
    sentences = split_sentences(" ".join(prose.split()))
    lengths = [len(s.split()) for s in sentences]
    rhythm: dict[str, float] = {"sentences": len(sentences), "words": n_words}
    penalty = 0.0
    # Rhythm statistics are unreliable on short passages such as a 200-word abstract.
    if len(lengths) >= 10 and n_words >= 250:
        mean, sd = statistics.mean(lengths), statistics.pstdev(lengths)
        cv = sd / mean if mean else 0.0
        rhythm.update(mean_sentence_words=round(mean, 1), sentence_length_cv=round(cv, 2))
        if cv < 0.25:
            penalty += 6
            findings.append(Finding(0, "monotone-rhythm", 0, f"CV={cv:.2f}",
                                    "Sentence lengths are uniform. Mix short declaratives with longer explanatory "
                                    "sentences."))
        starts = sum(bool(SENTENCE_START_TRANSITIONS.match(s)) for s in sentences)
        share = starts / len(sentences)
        rhythm["transition_start_share"] = round(share, 2)
        if share > 0.2:
            penalty += 5
            findings.append(Finding(0, "transition-overuse", 0, f"{share:.0%} of sentences",
                                    "Too many sentences open with 'Moreover/Furthermore/Additionally'. Let logic "
                                    "carry the connection."))
        openers = [" ".join(s.split()[:2]).lower() for s in sentences]
        top = max(set(openers), key=openers.count)
        if openers.count(top) >= max(3, len(sentences) // 5):
            findings.append(Finding(0, "repeated-opener", 0, f"'{top}' x{openers.count(top)}",
                                    "Vary sentence openings."))
            penalty += 2
    if len(paragraphs) >= 4:
        plen = [len(p.split()) for p in paragraphs]
        pcv = statistics.pstdev(plen) / statistics.mean(plen)
        rhythm["paragraph_length_cv"] = round(pcv, 2)
        if pcv < 0.15:
            penalty += 3
            findings.append(Finding(0, "uniform-paragraphs", 0, f"CV={pcv:.2f}",
                                    "Paragraphs are near-identical in length. Size them to their content."))
    dashes = len(re.findall(r"—|(?<=\w) -- (?=\w)|(?<=\w)---(?=\w)", prose))
    per_k = dashes / n_words * 1000
    rhythm["em_dashes_per_1000_words"] = round(per_k, 1)
    if per_k > 6:
        penalty += min(8, per_k - 6)
        findings.append(Finding(0, "em-dash-pileup", 0, f"{dashes} em dashes",
                                "Replace most em dashes with commas, colons, parentheses or full stops."))
    triads = len(re.findall(r"\b\w+(?:ly)?, \w+(?:ly)?,? and \w+(?:ly)?\b", prose))
    rhythm["triads_per_1000_words"] = round(triads / n_words * 1000, 1)
    if triads >= 4 and triads / n_words * 1000 > 8:
        penalty += 3
        findings.append(Finding(0, "rule-of-three", 0, f"{triads} triads",
                                "Lists of three are overused. Keep only the items that matter."))
    weighted = sum(f.weight for f in findings)
    index = round(weighted / n_words * 1000 + penalty, 1)
    band = "clean" if index < 5 else "some slop" if index < 15 else "heavy slop" if index < 30 else "severe slop"
    by_cat: dict[str, int] = {}
    for f in findings:
        by_cat[f.category] = by_cat.get(f.category, 0) + 1
    return {"slop_index": index, "band": band, "by_category": by_cat, "rhythm": rhythm,
            "findings": [asdict(f) for f in sorted(findings, key=lambda f: (f.line, -f.weight))]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="file (.md .tex .txt .docx) or - for stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max", type=float, default=15.0, help="exit 1 if the slop index exceeds this (default 15)")
    args = ap.parse_args()
    try:
        text = read_input(args.path)
    except (OSError, UnicodeDecodeError, KeyError, zipfile.BadZipFile) as exc:
        print(f"error: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2
    result = analyse(text)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for f in result["findings"]:
            where = f"line {f['line']}" if f["line"] else "whole text"
            print(f"{where:>10}  [{f['category']}] {f['match']}\n{'':>12}-> {f['hint']}")
        r = result["rhythm"]
        print(f"\nSlop index {result['slop_index']} ({result['band']}) over {r['words']} words, "
              f"{r['sentences']} sentences. Rhythm: " + ", ".join(f"{k}={v}" for k, v in r.items()
                                                                  if k not in ("words", "sentences")))
    return 1 if result["slop_index"] > args.max else 0


if __name__ == "__main__":
    sys.exit(main())
