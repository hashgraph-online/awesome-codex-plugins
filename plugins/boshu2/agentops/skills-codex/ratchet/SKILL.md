---
name: ratchet
description: "Run ratchet."
---
# Ratchet Skill

Track progress through the RPI workflow with permanent gates.

**Note:** `$ratchet` tracks and locks progress. It does not “run the loop” by itself—pair it with `$crank` (epic loop) or `$swarm` (Ralph loop) to actually execute work.

## The Brownian Ratchet

```
Progress = Chaos × Filter → Ratchet
```

| Phase | What Happens |
|-------|--------------|
| **Chaos** | Multiple attempts (exploration, implementation) |
| **Filter** | Validation gates (tests, $vibe, review) |
| **Ratchet** | Lock progress permanently (merged, closed, stored) |

**Key insight:** Progress is permanent. You can't un-ratchet.

## Execution Steps

Given `$ratchet [command]`:

### status - Check Current State

```bash
ao ratchet status 2>/dev/null
```

Or check the chain manually:
```bash
cat .agents/ao/chain.jsonl 2>/dev/null | tail -10
```

### check [step] - Verify Gate

```bash
ao ratchet check <step> 2>/dev/null
```

Steps: `research`, `plan`, `implement`, `vibe`, `post-mortem`

### record [step] - Record Completion

```bash
ao ratchet record <step> --output "<artifact-path>" 2>/dev/null
```

Or record manually by writing to chain:
```bash
echo '{"step":"<step>","status":"completed","output":"<path>","time":"<ISO-timestamp>"}' >> .agents/ao/chain.jsonl
```

### skip [step] - Skip Intentionally

```bash
ao ratchet skip <step> --reason "<why>" 2>/dev/null
```

## Workflow Steps

| Step | Gate | Output |
|------|------|--------|
| `research` | Research artifact exists | `.agents/research/*.md` |
| `plan` | Plan artifact exists | `.agents/plans/*.md` |
| `implement` | Code + tests pass | Source files |
| `vibe` | $vibe passes | `.agents/vibe/*.md` |
| `post-mortem` | Learnings extracted | `.agents/learnings/*.md` |

## Chain Storage

Progress stored in `.agents/ao/chain.jsonl`:
```json
{"step":"research","status":"completed","output":".agents/research/auth.md","time":"2026-01-25T10:00:00Z"}
{"step":"plan","status":"completed","output":".agents/plans/auth-plan.md","time":"2026-01-25T11:00:00Z"}
{"step":"implement","status":"in_progress","time":"2026-01-25T12:00:00Z"}
```

## Key Rules

- **Progress is permanent** - can't un-ratchet
- **Gates must pass** - validate before proceeding
- **Record everything** - maintain the chain
- **Skip explicitly** - document why if skipping a step

## Examples

### Check RPI Progress

**User says:** `$ratchet status`

**What happens:**
1. Agent calls `ao ratchet status 2>/dev/null` to check current state
2. CLI reads `.agents/ao/chain.jsonl` and parses progress
3. Agent reports which steps are completed, in-progress, or pending
4. Agent shows output artifact paths for completed steps
5. Agent identifies next gate to pass

**Result:** Single-screen view of RPI workflow progress, showing which gates passed and what's next.

### Record Step Completion

**Skill says:** After `$research` completes

**What happens:**
1. Agent calls `ao ratchet record research --output ".agents/research/auth.md"`
2. CLI appends completion entry to `.agents/ao/chain.jsonl`
3. Agent locks research step as permanently completed
4. Agent proceeds to plan phase knowing research gate passed

**Result:** Progress permanently recorded, gate locked, workflow advances without backsliding.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| ao ratchet status fails | ao CLI not available or chain.jsonl missing | Manually check `.agents/ao/chain.jsonl` or create empty file |
| Step already completed error | Attempting to re-ratchet locked step | Use `ao ratchet status` to check state; skip if already done |
| chain.jsonl corrupted | Malformed JSON entries | Manually edit to fix JSON; validate each line with `jq -c '.' <file>` |
| Out-of-order steps | Implementing before planning | Follow RPI order strictly; use `--skip` only with explicit reason |

## Local Resources

### scripts/

- `scripts/validate.sh`


