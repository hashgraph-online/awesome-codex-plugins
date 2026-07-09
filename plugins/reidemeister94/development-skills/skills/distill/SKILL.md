---
name: distill
description: "Use when user wants to reduce noise, verbosity, or redundancy in markdown or text files. Use when user says distill, compress, clean up, tighten, denoise, reduce entropy, improve signal-to-noise ratio, or make text more concise. Accepts a file path, a directory (distills all .md/.txt files in it), or no argument (distills all .md/.txt files in the current directory)."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Agent
---

# Distill — Semantic Text Compression

ultrathink

Maximize facts-per-word while preserving every fact and keeping the text readable. Anything predictable from context carries zero information and can be removed.

<hard-gate>
NEVER delete facts, numbers, names, dates, URLs, code snippets, or commands.
NEVER change the meaning of a statement.
NEVER add information not in the original.
NEVER make the text telegraphic — output flows as natural prose.
</hard-gate>

This compresses stated meaning; it does NOT reverse euphemism or detect lies — an information-preserving compressor, not a fact-checker.

## Target Resolution

From `$ARGUMENTS`: empty -> Glob top-level `*.md` + `*.txt` in cwd (non-recursive); directory -> Glob `<dir>/**/*.md` + `<dir>/**/*.txt` (recursive); file -> that single file.

Exclude non-prose files (`requirements*.txt`, `LICENSE*`). No matches -> say `No .md or .txt files found in <path>.` and STOP. Run Steps 1-4 per file, report in Step 5.

## Step 1 — Measure

```bash
FILE="<path>"; echo "BEFORE: $(wc -c < "$FILE") chars | $(wc -w < "$FILE") words | $(wc -l < "$FILE") lines | $(gzip -c "$FILE" | wc -c) gzip"
```

gzip bytes are the entropy proxy: word count alone doesn't distinguish filler from signal, so track gzip before/after as the real-compression measure.

## Step 1.5 — Deterministic Pre-Pass

Extract the fenced python block from `references/deterministic-patterns.md` (the canonical kill-lists) and run it against the file:

```bash
REF="references/deterministic-patterns.md"
awk '/^```python$/{f=1;next} /^```$/{f=0} f' "$REF" | python3 - "<path>"
```

Mechanical kill-lists first; Step 2 is then pure semantic work.

## Step 2 — Distill

Rewrite the file. Read `references/noise-patterns.md` for the semantic noise taxonomy (buzzword replacement, structural padding, non-committal language, repetition, empty conclusions). Lead with the point, state each fact once, keep markdown structure that aids navigation and drop structure that only decorates.

## Step 3 — Post-Verification

Before writing:
1. Tables: count rows matching `|...|...|` in original vs output; restore any dropped.
2. Code blocks: count fenced blocks (``` or `~~~`); counts must match.
3. URLs: every http/https/ftp/mailto in original must appear in output.
4. If the original is under 100 words and already scored slop_score >= 90, apply only minimal changes — already dense.

## Step 4 — Write and Measure

```bash
FILE="<path>"; echo "AFTER: $(wc -c < "$FILE") chars | $(wc -w < "$FILE") words | $(wc -l < "$FILE") lines | $(gzip -c "$FILE" | wc -c) gzip"
```

## Step 5 — Report

Per file report words and gzip bytes before/after with reduction %, noise categories removed, and preserved counts (facts, code blocks, URLs). For a batch, one row per file plus a Total row (sum words before/after; `reduction = (1 - total_after/total_before)*100`).

Reduction under 10% -> mark already dense. Reduction over 60% -> re-verify no facts were lost before reporting.

If the user is unsatisfied, ask which passages lost information, restore them, and re-distill with a lighter touch.
