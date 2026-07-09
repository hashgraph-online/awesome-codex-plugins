# Context Gathering

How to collect rich context from multiple sources for retrospectives.

## Target Identification

### If Epic ID Provided

```bash
bd show $ARGUMENTS
# Extract child issue IDs, query each for comments
```

### If Topic/Plan Provided

```bash
ls .agents/plans/*$ARGUMENTS* 2>/dev/null
ls .agents/research/*$ARGUMENTS* 2>/dev/null
```

### If No Argument

```bash
br list --status closed | head -10
```

---

## Conversation Analysis

If a session ID is available, analyze the Codex conversation to extract:
- Decisions made during implementation
- Friction encountered (errors, retries, workarounds)
- Patterns discovered or followed
- Lessons learned

```bash
# Analyze specific session
python3 ~/.codex/scripts/analyze-sessions.py --session=$SESSION_ID

# Analyze with extraction limits for large sessions
python3 ~/.codex/scripts/analyze-sessions.py --session=$SESSION_ID --limit=50
```

### Conversation Data → Retro Output Mapping

| Conversation Data | Retro Output |
|-------------------|--------------|
| `DecisionExtraction` | `.agents/council/` - Decisions section |
| `QualityResult.issues` | Friction detection |
| `DocExtraction(type="warning")` | `.agents/learnings/` |
| `DecisionExtraction(type="pattern")` | `.agents/patterns/` |
| `DecisionExtraction(type="lesson")` | What Worked / What Didn't |

### Session ID Sources

1. **Environment variable**: `$CLAUDE_SESSION_ID` (set by Codex)
2. **Recent session detection**: Find most recent `.jsonl` in `~/.codex/projects/`
3. **Beads comment**: Sessions may be recorded in crank state

### When No Session Available

Fall back to git analysis and beads comments. Note in retro that conversation
analysis was unavailable.

---

## Git Commit Analysis

```bash
git log --oneline --since="7 days ago" | grep -E "(ai-platform-[a-z0-9]+|$TOPIC)"
git show <commit-hash> --stat
```

**Extract:** Files modified, commit messages, lines changed.

---

## Beads Comments

```bash
bd show <epic-id>
bd show <child-id>
```

**Extract:** Decisions, blockers, workarounds, root causes.

---

## Blackboard State

```bash
ls .agents/blackboard/
cat .agents/blackboard/crank-state.json 2>/dev/null
```

---

## Closure Integrity Quick-Check

When retrospecting an epic, run lightweight closure checks before extracting learnings. Full audit lives in `skills/post-mortem/references/closure-integrity-audit.md`; retro uses the subset below.

### Phantom Bead Detection

```bash
EPIC_ID="$ARGUMENTS"
for child in $(bd children "$EPIC_ID" 2>/dev/null | grep -oP '\S+' | head -1); do
  TITLE=$(bd show "$child" 2>/dev/null | head -1 | sed 's/^.*· //' | sed 's/ \[.*$//')
  if echo "$TITLE" | grep -qP '^(task|fix|update|todo|item|work)$'; then
    echo "WARN: $child has generic title '$TITLE' — possible phantom closure"
  fi
done
```

### Multi-Wave Regression Scan

For crank epics, check if later waves reverted earlier waves' work:

```bash
# Quick heuristic: count net lines added per scoped file across all wave commits
# If a file has 0 net additions but was touched in multiple waves, flag it
for f in $(git diff --name-only HEAD~5 2>/dev/null | sort -u); do
  ADDS=$(git log --oneline --numstat HEAD~5..HEAD -- "$f" 2>/dev/null | awk '/^[0-9]/{s+=$1}END{print s+0}')
  DELS=$(git log --oneline --numstat HEAD~5..HEAD -- "$f" 2>/dev/null | awk '/^[0-9]/{s+=$2}END{print s+0}')
  TOUCHES=$(git log --oneline HEAD~5..HEAD -- "$f" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$TOUCHES" -gt 1 ] && [ "$ADDS" -le "$DELS" ]; then
    echo "WARN: $f touched $TOUCHES times but net additions <= deletions — possible wave regression"
  fi
done
```

**Why:** In na-vs9.4, Wave 2 removed 15 lines that Wave 1 added. Both waves passed tests independently. This check catches the pattern mechanically.

### Retro Integration

- Include closure warnings in **What Could Be Improved** section
- If phantom beads found, add learning: "Require meaningful titles and descriptions for all child beads before closing epic"
- If wave regressions found, add learning: "Add cross-wave diff validation to crank post-wave checks"

---

## Friction Detection

### Friction Keywords

```bash
# Look for friction keywords in comments
grep -i "error\|failed\|retry\|workaround\|fixed by\|root cause" <comments>

# Look for fix commits
git log --oneline | grep -i "fix\|revert\|hotfix\|patch"
```

### Search Prior Solutions

```bash
ls .agents/learnings/ | grep -i "$TOPIC"
ls .agents/patterns/ | grep -i "$TOPIC"
```

**If found:** Reference in proposal.
**If not found:** Mark as "NEW" for learning extraction.

### Friction Categories

| Category | Indicators |
|----------|------------|
| Retry/Failure | "Error:", "Failed:", test failures |
| Manual Fix | User corrections after agent action |
| Blocking | Dependency issues |
| Pattern Deviation | Didn't follow established pattern |
| Missing Information | Had to search for docs |

### Friction → Fix Mapping

| Friction | Fix Location |
|----------|--------------|
| Command unclear | `.codex/commands/*.md` |
| Skill trigger missed | `.codex/skills/**/*.md` |
| Pattern not followed | `.agents/patterns/*.md` |
| Convention violated | `CLAUDE.md` |

---

## Supersession Check

### Search Existing Artifacts

```bash
mcp__smart-connections-work__lookup --query="$TOPIC" --limit=10
grep -rl "$TOPIC" .agents/learnings/ .agents/patterns/ 2>/dev/null
```

### Supersession Criteria

| Criterion | Supersede? |
|-----------|------------|
| Same topic, newer insight | Yes |
| Same topic, complementary | No (cross-reference) |
| Obsolete/incorrect info | Yes |

### Metadata

Old artifact:
```yaml
superseded_by: .agents/learnings/YYYY-MM-DD-new.md
```

New artifact:
```yaml
supersedes: .agents/learnings/YYYY-MM-DD-old.md
```
