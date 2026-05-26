# Backlog Processing — Phase 3 Implementation Details

Phase 3 scans `.agents/learnings/`, deduplicates entries, scores them for promotion, and flags stale learnings for retirement. This document defines the algorithms and data contracts.

## Scoring Algorithm

Each learning is scored on three dimensions. The composite score determines whether the learning is promoted to Phase 4 (activation).

**Formula:** `score = confidence + citations + recency`

| Dimension | Value | Points |
|-----------|-------|--------|
| Confidence: high | Explicit `confidence: high` in frontmatter or body | 3 |
| Confidence: medium | Explicit `confidence: medium` or no confidence marker | 2 |
| Confidence: low | Explicit `confidence: low` | 1 |
| Citations: default | Every learning gets a baseline citation (represents creation) | 1 |
| Citations: explicit | +1 per explicit citation in `.agents/ao/citations.jsonl` | +1 each |
| Recency: <7 days | File mtime within the last 7 days | 3 |
| Recency: <30 days | File mtime within the last 30 days | 2 |
| Recency: >30 days | File mtime older than 30 days | 1 |

**Promote threshold:** score >= 6 triggers Phase 4 activation.

### Scoring Examples

| Confidence | Explicit Citations | Age | Score | Result |
|------------|-------------------|-----|-------|--------|
| High (3) | 0 (default=1) | <7d (3) | 3 + 1 + 3 = **7** | PROMOTE |
| Medium (2) | 2 (default+2=3) | <7d (3) | 2 + 3 + 3 = **8** | PROMOTE |
| Medium (2) | 0 (default=1) | <7d (3) | 2 + 1 + 3 = **6** | PROMOTE |
| Low (1) | 0 (default=1) | >30d (1) | 1 + 1 + 1 = **3** | no action |
| High (3) | 0 (default=1) | >30d (1) | 3 + 1 + 1 = **5** | no action |

### Implementation

```bash
score_learning() {
  local file="$1"
  local score=0

  # Confidence
  local confidence=$(grep -i 'confidence:' "$file" | head -1 | awk '{print $2}' | tr '[:upper:]' '[:lower:]')
  case "$confidence" in
    high) score=$((score + 3)) ;;
    low)  score=$((score + 1)) ;;
    *)    score=$((score + 2)) ;;  # medium or unspecified
  esac

  # Citations (default = 1, +1 per explicit citation)
  local cite_count=1
  if [ -f .agents/ao/citations.jsonl ]; then
    local explicit=$(grep -c "\"artifact_path\":\"$file\"" .agents/ao/citations.jsonl 2>/dev/null || echo 0)
    cite_count=$((cite_count + explicit))
  fi
  score=$((score + cite_count))

  # Recency (based on file mtime)
  local age_days=$(( ($(date +%s) - $(stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null)) / 86400 ))
  if [ "$age_days" -lt 7 ]; then
    score=$((score + 3))
  elif [ "$age_days" -lt 30 ]; then
    score=$((score + 2))
  else
    score=$((score + 1))
  fi

  echo "$score"
}
```

---

## Deduplication Rules

Phase 3 checks for duplicate learnings before scoring. Duplicates waste scoring budget and pollute the flywheel.

### Exact Title Match

Two learnings with identical `# Learning: <title>` headers are duplicates. Merge unconditionally.

```bash
# Extract titles and find duplicates
grep -rh '^# Learning:' .agents/learnings/*.md \
  | sort | uniq -d
```

### Keyword Overlap

If two learnings share >80% keyword overlap in their first paragraph (excluding stop words), they are **merge candidates** requiring human review.

```bash
# Simplified keyword extraction (first paragraph, no stop words)
extract_keywords() {
  local file="$1"
  sed -n '/^# /,/^$/p' "$file" \
    | tail -n +2 \
    | tr '[:upper:]' '[:lower:]' \
    | tr -cs '[:alpha:]' '\n' \
    | grep -v -w -f /usr/share/dict/stop_words 2>/dev/null \
    | sort -u
}

# Compare two files — output overlap percentage
keyword_overlap() {
  local kw1=$(extract_keywords "$1")
  local kw2=$(extract_keywords "$2")
  local total=$(echo "$kw1" "$kw2" | tr ' ' '\n' | sort -u | wc -l)
  local shared=$(comm -12 <(echo "$kw1" | tr ' ' '\n' | sort) <(echo "$kw2" | tr ' ' '\n' | sort) | wc -l)
  echo $(( shared * 100 / total ))
}
```

If overlap >= 80%, flag as merge candidate.

### Merge Procedure

When merging two duplicate learnings:

1. **Keep the version with the highest confidence** (high > medium > low)
2. **Combine source references** from both files (deduplicate URLs and bead IDs)
3. **Preserve the most recent date** as the merged file's date
4. **Archive the discarded version** to `.agents/learnings/archive/` with a `merged-into: <kept-file>` header appended

---

## Staleness Criteria

A learning is flagged as **stale** when BOTH of these conditions are met:

| Condition | Threshold |
|-----------|-----------|
| Age | >30 days since file creation (based on filename date or file mtime) |
| Citations | Zero entries in `.agents/ao/citations.jsonl` referencing this file |

**Both conditions must be true.** A 60-day-old learning with active citations is NOT stale. A 10-day-old learning with zero citations is NOT stale.

### Staleness Check

```bash
check_staleness() {
  local file="$1"

  # Age check
  local age_days=$(( ($(date +%s) - $(stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null)) / 86400 ))
  if [ "$age_days" -le 30 ]; then
    echo "ACTIVE"
    return
  fi

  # Citation check
  local citations=0
  if [ -f .agents/ao/citations.jsonl ]; then
    citations=$(grep -c "\"artifact_path\":\"$file\"" .agents/ao/citations.jsonl 2>/dev/null || echo 0)
  fi
  if [ "$citations" -gt 0 ]; then
    echo "ACTIVE"
    return
  fi

  echo "STALE"
}
```

**Stale learnings** are retired in Phase 5: moved to `.agents/learnings/archive/` with their original filename preserved.

---

## Last-Processed Marker

Phase 3 uses a marker file to avoid re-scanning already-processed learnings.

| Field | Value |
|-------|-------|
| **Path** | `.agents/ao/last-processed` |
| **Format** | ISO 8601 timestamp (e.g., `2026-03-03T15:30:00-05:00`) |
| **Created on first run** | Default value = 30 days ago |
| **Updated** | At the end of Phase 4 (after activation completes) |

### Behavior

1. Phase 3 reads `.agents/ao/last-processed`
2. If the file does not exist, create it with a timestamp 30 days in the past
3. Scan `.agents/learnings/` for files with mtime **newer** than the marker
4. Only score and deduplicate files that pass the mtime filter
5. After Phase 4 completes, update the marker to the current timestamp

```bash
MARKER=".agents/ao/last-processed"

# Initialize marker if missing (default: 30 days ago)
if [ ! -f "$MARKER" ]; then
  mkdir -p "$(dirname "$MARKER")"
  date -Iseconds -d "-30 days" 2>/dev/null \
    || date -v-30d +%Y-%m-%dT%H:%M:%S%z > "$MARKER"
fi

LAST_PROCESSED=$(cat "$MARKER")

# Find learnings newer than the marker
find .agents/learnings/ -name '*.md' -newer "$MARKER" -type f
```

---

## Citation Tracking

Citations record when a learning is referenced by other artifacts, providing the usage signal for scoring and staleness detection.

| Field | Value |
|-------|-------|
| **Path** | `.agents/ao/citations.jsonl` |
| **Format** | One JSON object per line |

### Line Format

```json
{"artifact_path": "<path>", "session_id": "<session-id>", "cited_at": "<ISO8601>", "workspace_path": "<absolute-workspace>"}
```

### Citation Counting

- **Default citation count = 1** for every learning (represents the creation event itself; not stored in the JSONL file)
- **Explicit citations** are appended to `citations.jsonl` when a learning is referenced in:
  - A council report
  - A research document
  - Session context (via inject or research)

### Write Paths

Citations are recorded by these entry points:

| Writer | Trigger |
|--------|---------|
| `ao forge` | Learning forged into flywheel |
| Session-close hooks | Learning referenced during session |
| `ao metrics cite <learning-path>` | Manual citation by user or agent |

### Example

```jsonl
{"artifact_path":".agents/learnings/2026-02-28-crank-wave-isolation.md","session_id":"session-ag-5k2","cited_at":"2026-03-01T10:15:00-05:00","workspace_path":"/abs/workspace"}
{"artifact_path":".agents/learnings/2026-02-28-crank-wave-isolation.md","session_id":"session-ag-7m1","cited_at":"2026-03-02T14:30:00-05:00","workspace_path":"/abs/workspace"}
{"artifact_path":".agents/learnings/2026-03-01-codex-flag-divergence.md","session_id":"session-ag-9zz","cited_at":"2026-03-03T09:00:00-05:00","workspace_path":"/abs/workspace"}
```

In this example, `crank-wave-isolation.md` has a total citation count of 3 (1 default + 2 explicit), while `codex-flag-divergence.md` has a total citation count of 2 (1 default + 1 explicit).
