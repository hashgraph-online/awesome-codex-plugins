---
name: forge
description: "Run forge."
---
# Forge Skill

**Typically runs automatically via SessionEnd hook.**

> **Loop position:** capture sub-step of move 7 in the [operating loop](../../docs/architecture/operating-loop.md). Extracts candidate learnings from transcripts; the [promotion ratchet](../../docs/architecture/operating-loop.md#the-promotion-ratchet) decides which ones survive (one-offs die at handoff; repeats promote to `.agents/learnings/`). Forge is the funnel, not the filter.

Extract knowledge from session transcripts.

## How It Works

The SessionEnd hook runs:
```bash
ao forge transcript --last-session --queue --quiet
```

This queues the session for knowledge extraction.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--promote` | off | Process pending extractions from `.agents/knowledge/pending/` and promote to `.agents/learnings/`. Absorbs the former extract skill. |

## Promote Mode

Given `$forge --promote`:

### Promote Step 1: Find Pending Files

```bash
ls -lt .agents/knowledge/pending/*.md 2>/dev/null
ls -lt .agents/ao/pending.jsonl 2>/dev/null
```

If no pending files found, report "No pending extractions" and exit.

### Promote Step 2: Process Each Pending File

For each file in `.agents/knowledge/pending/`:
1. Read the file content
2. Validate it has required fields (`# Learning:`, `**Category**:`, `**Confidence**:`)
3. Copy to `.agents/learnings/` (preserving filename)
4. Remove the source file from `.agents/knowledge/pending/`

### Promote Step 3: Process Pending Queue

```bash
if [ -f .agents/ao/pending.jsonl ] && [ -s .agents/ao/pending.jsonl ]; then
  # Process each queued session
  cat .agents/ao/pending.jsonl
  # After processing, clear the queue
  > .agents/ao/pending.jsonl
fi
```

### Promote Step 4: Report

```
Promoted N learnings from pending → .agents/learnings/
Queue cleared.
```

**Done.** Return immediately after reporting.

---

## Manual Execution

Given `$forge [path]`:

### Step 1: Identify Transcript

**With ao CLI:**
```bash
# Mine recent sessions
ao forge transcript --last-session

# Mine specific transcript
ao forge transcript <path>
```

**Without ao CLI:**
Look at recent conversation history and extract learnings manually.

### Step 2: Extract Knowledge Types

Read `skills/forge/references/uncaptured-lesson-patterns.md` for signal patterns and the 26 known uncaptured lesson categories.

Look for these patterns in the transcript:

| Type | Signals | Weight |
|------|---------|--------|
| **Decision** | "decided to", "chose", "went with" | 0.8 |
| **Learning** | "learned that", "discovered", "realized" | 0.9 |
| **Failure** | "failed because", "broke when", "didn't work" | 1.0 |
| **Pattern** | "always do X", "the trick is", "pattern:" | 0.7 |

**Uncaptured Lesson Matching:** During transcript scanning, match events against the 26 known uncaptured lesson patterns (see `references/uncaptured-lesson-patterns.md`). Pre-fill learning templates with matched pattern metadata (category, base confidence, pattern number tag).

### Step 3: Write Candidates

**Write to:** `.agents/forge/YYYY-MM-DD-forge.md`

```markdown
# Forged: YYYY-MM-DD

## Decisions
- [D1] <decision made>
  - Source: <where in conversation>
  - Confidence: <0.0-1.0>

## Learnings
- [L1] <what was learned>
  - Source: <where in conversation>
  - Confidence: <0.0-1.0>

## Failures
- [F1] <what failed and why>
  - Source: <where in conversation>
  - Confidence: <0.0-1.0>

## Patterns
- [P1] <reusable pattern>
  - Source: <where in conversation>
  - Confidence: <0.0-1.0>
```

### Step 4: Index for Search

```bash
if command -v ao &>/dev/null; then
  ao forge markdown .agents/forge/YYYY-MM-DD-forge.md 2>/dev/null
else
  # Without ao CLI: auto-promote high-confidence candidates to learnings
  mkdir -p .agents/learnings .agents/ao
  for f in .agents/forge/YYYY-MM-DD-*.md; do
    [ -f "$f" ] || continue
    # Extract confidence (numeric or categorical)
    CONF=$(grep -i "confidence:" "$f" | head -1 | awk '{print $NF}')
    # Normalize categorical to numeric: high=0.9, medium=0.6, low=0.3
    case "$CONF" in
      high) CONF_NUM=0.9 ;; medium) CONF_NUM=0.6 ;; low) CONF_NUM=0.3 ;; *) CONF_NUM=$CONF ;;
    esac
    # Auto-promote if confidence >= 0.7, prepending required frontmatter
    if (( $(echo "$CONF_NUM >= 0.7" | bc -l) )); then
      { printf -- '---\ntype: learning\nsource: forge\ndate: %s\nmaturity: provisional\nutility: 0.5\n---\n' "$(date +%Y-%m-%d)"; cat "$f"; } > .agents/learnings/"$(basename "$f")"
      TITLE=$(head -1 "$f" | sed 's/^# //')
      echo "{\"file\": \".agents/learnings/$(basename $f)\", \"title\": \"$TITLE\", \"keywords\": [], \"timestamp\": \"$(date -Iseconds)\"}" >> .agents/ao/search-index.jsonl
      echo "Auto-promoted (confidence $CONF): $(basename $f)"
    fi
  done
  echo "Forge indexing complete (ao CLI not available — high-confidence candidates auto-promoted)"
fi
```

### Step 5: Update Capture Tracking

After extracting learnings that match uncaptured lesson patterns (Step 2), record which patterns were captured. This state lives in `.agents/forge/capture-tracking.json` (a runtime artifact, never in `skills/`).

```bash
mkdir -p .agents/forge
```

1. Read `.agents/forge/capture-tracking.json` if it exists, otherwise start with `{}`
2. For each matched pattern, add or update an entry keyed by pattern number:
   ```json
   {
     "3": {"captured": true, "date": "2026-03-30", "learning_path": ".agents/learnings/tooling/use-bin-cp.md"},
     "7": {"captured": true, "date": "2026-03-29", "learning_path": ".agents/learnings/operations/worktree-commit.md"}
   }
   ```
3. Write the updated JSON back to `.agents/forge/capture-tracking.json`

Pattern numbers correspond to the numbered headings in `references/uncaptured-lesson-patterns.md` (1-30, 26 total patterns).

### Step 6: Report Results

Tell the user:
- Number of items extracted by type
- Location of forge output
- Candidates ready for promotion to learnings
- **Capture progress:** "X/26 uncaptured lesson patterns captured" (read from `.agents/forge/capture-tracking.json`)

## The Quality Pool

Forged candidates enter at Tier 0 (`.agents/forge/`), then promote to Tier 1
(`.agents/learnings/`) via human review, 2+ citations, or auto-promote when
confidence >= 0.7 (ao-free fallback).

## Key Rules

- **Runs automatically** - usually via hook
- **Extract, don't interpret** - capture what was said
- **Score by confidence** - not all extractions are equal
- **Queue for review** - candidates need validation

## Examples

See [references/examples.md](references/examples.md) for the SessionEnd hook
invocation walkthrough and manual transcript-mining walkthrough.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| No extractions found | Transcript lacks knowledge signals or ao CLI unavailable | Check transcript contains decisions/learnings; verify ao CLI installed |
| Low confidence scores | Weak signals or vague conversation | Focus sessions on concrete decisions and explicit learnings |
| forge --queue fails | CLI not available or permission error | Manually append to `.agents/ao/pending.jsonl` with session metadata |
| Duplicate forge outputs | Same session forged multiple times | Check forge filenames before writing; ao CLI handles dedup automatically |

## Reference Documents

- [references/uncaptured-lesson-patterns.md](references/uncaptured-lesson-patterns.md) — signal patterns and 26 known uncaptured lesson categories for transcript mining
- [references/feedback-compiler-drafts.md](references/feedback-compiler-drafts.md) — auto-drafted learning workflow (F5.4 fail->pass ledger transitions, `cli/internal/feedbackcompiler`)
