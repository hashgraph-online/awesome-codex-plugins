# FIRE Loop Specification

> **Find-Ignite-Reap-Escalate**: The Brownian Ratchet engine powering autonomous execution.

## Overview

FIRE is the reconciliation loop that extracts progress from chaos. Like a forge that transforms raw ore into refined steel, FIRE continuously drives an epic toward completion through parallel attempts filtered by validation.

**Design philosophy**: Chaos + Filter + Ratchet = Progress.

```
    ┌──────────────────────────────────────────────────────────┐
    │                       FIRE LOOP                          │
    │                                                          │
    │     FIND ────► IGNITE ────► REAP ────► ESCALATE          │
    │    (state)    (chaos)    (ratchet)   (recovery)          │
    │       │                                   │              │
    │       └───────────────────────────────────┘              │
    │                      (loop)                              │
    │                                                          │
    │     EXIT when: all children closed                       │
    └──────────────────────────────────────────────────────────┘
```

## The Brownian Ratchet

| Phase | Ratchet Role | Description |
|-------|--------------|-------------|
| **FIND** | Observe | Read current state, identify ready work |
| **IGNITE** | **Chaos** | Spark parallel polecats, embrace variance |
| **REAP** | **Filter + Ratchet** | Harvest results, validate, merge (permanent) |
| **ESCALATE** | Recovery | Handle failures, retry or escalate to human |

**Key insight**: Polecats can fail independently. Each successful merge ratchets forward. The system extracts progress from parallel attempts, filtering failures automatically.

---

## Loop Phases

### FIND Phase

**Purpose**: Build current state snapshot. What's ready? What's burning? What's done?

**Commands**:

```bash
br ready --parent=<epic>                    # Ready to ignite
br list --parent=<epic> --status=in_progress  # Currently burning
br list --parent=<epic> --status=closed       # Reaped
bd blocked --parent=<epic>                    # Waiting on deps
gt convoy list                               # Active convoys  <!-- FUTURE: gt convoy not yet implemented -->
```

**State object**:

```yaml
fire_state:
  epic_id: gt-0100
  total_children: 8

  # Work pools
  ready: [gt-0101, gt-0102]      # Can ignite
  burning: [gt-0103, gt-0104]    # In-flight
  reaped: [gt-0105, gt-0106]     # Completed
  blocked: [gt-0107, gt-0108]    # Waiting

  # Derived
  remaining: 6                    # total - reaped
  capacity: 2                     # MAX_POLECATS - burning
  complete: false                 # remaining == 0
```

**Token cost**: ~200-300 tokens

---

### IGNITE Phase

**Purpose**: Spark parallel polecats. This is the CHAOS - multiple independent attempts.

**Decision logic**:

```python
def ignite_phase(state, retry_queue):
    to_ignite = []

    # Priority 1: Scheduled retries that are due
    for issue, scheduled_time in retry_queue:
        if now() >= scheduled_time:
            to_ignite.append(issue)
            retry_queue.remove(issue)

    # Priority 2: Fresh ready issues
    for issue in state.ready:
        if issue not in to_ignite:
            to_ignite.append(issue)

    # Respect capacity
    to_ignite = to_ignite[:state.capacity]

    # IGNITE - spark the chaos
    for issue in to_ignite:
        gt_sling(issue, rig)

    return to_ignite
```

**Commands**:

```bash
# Batch ignite - preferred (each issue gets own polecat)
gt sling <issue1> <issue2> <issue3> <rig>

# Single ignite
gt sling <issue> <rig>

# Find stranded convoys (ready work, no workers)
gt convoy stranded                           # FUTURE: gt convoy not yet implemented
```

**Token cost**: ~50 tokens per dispatch

---

### REAP Phase

**Purpose**: Harvest results. This is the FILTER + RATCHET - validate completions, merge permanently.

The REAP phase combines monitoring and collection into a single harvest operation:

1. **Monitor** - Poll for completion
2. **Validate** - Verify work quality (the FILTER)
3. **Merge** - Lock progress (the RATCHET)

**Monitoring**:

```bash
# Primary: Convoy dashboard (lowest token cost)
gt convoy status <convoy-id>                 # FUTURE: gt convoy not yet implemented

# Secondary: Individual polecat check
gt polecat status <rig>/<name>

# Tertiary: Peek at work (debugging only)
gc session peek <agent> --lines 20
```

**Poll interval**: 30 seconds

| Convoy Status | Meaning | Action |
|---------------|---------|--------|
| `running` | Polecats burning | Continue monitoring |
| `partial` | Some done | Reap completed, continue |
| `complete` | All done | Reap all |
| `failed` | Some failed | Reap successes, escalate failures |
| `stalled` | No progress 5+ polls | Investigate |

**Validation (the FILTER)**:

```python
def validate_completion(issue, polecat):
    """Filter: only valid completions ratchet forward."""

    # Check beads status
    status = bd_show(issue).status
    if status != 'closed':
        return False, "Status not closed"

    # Check git work exists
    commits = git_log(polecat_path, count=1)
    if not commits:
        return False, "No commits found"

    # Check commit references issue
    if issue not in commits[0].message:
        return False, "Commit doesn't reference issue"

    return True, "Validated"
```

**Merge (the RATCHET)**:

```bash
# Polecats self-merge via gt done:
# push → submit to merge queue → exit

# Post-merge cleanup
gt polecat gc <rig>  # Clean merged branches
```

**Key property**: Once merged, work is PERMANENT. The ratchet doesn't go backward.

**Token cost**: ~250 tokens per reap cycle

---

### ESCALATE Phase

**Purpose**: Handle failures with backoff and human escalation. Failed attempts re-enter the chaos pool or get escalated.

**Retry policy**:

| Attempt | Backoff | Action |
|---------|---------|--------|
| 1 | 30s | Re-ignite fresh polecat |
| 2 | 60s | Re-ignite with context |
| 3 | 120s | Re-ignite with explicit hints |
| 4+ | - | **ESCALATE**: BLOCKER + mail human |

**Backoff calculation**:

```python
def calculate_backoff(attempt):
    """Exponential backoff: 30s * 2^(attempt-1)"""
    return 30 * (2 ** (attempt - 1))
```

**Retry (back to chaos pool)**:

```bash
# Re-ignite with failure context
bd comments add <issue> "Previous attempt failed: <reason>. Try: <hint>"
gt sling <issue> <rig>
```

**Escalation (exit chaos pool)**:

```bash
# Mark as blocker
bd update <issue> --labels=BLOCKER

# Document failure history
bd comments add <issue> "AUTO-ESCALATED: Failed 3 attempts.
Reasons: 1) <reason1> 2) <reason2> 3) <reason3>
Human review required."

# Mail human
gt mail send --human -s "BLOCKER: <issue> failed 3 attempts" -m "..."

# Continue with other issues (don't halt epic)
```

**Token cost**: ~100 tokens per escalation

---

## State Machine

```
                    ┌─────────────────────────────────┐
                    │                                 │
                    ▼                                 │
┌────────┐    ┌─────────┐    ┌────────┐    ┌──────────┐
│  FIND  │───►│  IGNITE │───►│  REAP  │───►│ ESCALATE │
└────────┘    └─────────┘    └────────┘    └──────────┘
     │           chaos        ratchet          │
     │                                         │
     │ (all reaped)                            │
     ▼                                         │
┌────────┐                                     │
│  EXIT  │◄────────────────────────────────────┘
└────────┘         (retry scheduled)
```

---

## Loop Invariants

1. **Progress**: Each iteration must make progress OR escalate
2. **Bounded**: Retry counts are bounded, escalation is guaranteed
3. **Idempotent**: Re-running FIND produces same state for same beads
4. **Recoverable**: State can be reconstructed from beads alone
5. **Ratchet**: Merged work never goes backward

---

## Concurrency Model

**Single Mayor, Ephemeral Polecats**:

```
Mayor (FIRE Loop)
    │
    ├── Polecat 1 (burning gt-0101) → reaped → nuked
    ├── Polecat 2 (burning gt-0102) → reaped → nuked
    ├── Polecat 3 (burning gt-0103) → failed → escalated
    └── Polecat 4 (burning gt-0104) → reaped → nuked
```

**Polecat lifecycle**:
1. `gt sling` ignites polecat with hooked work
2. Polecat executes via `/implement`
3. On completion: `gt done` → push → merge queue → exit
4. Witness nukes sandbox after merge
5. No idle state - polecats don't wait

**Coordination via beads**:
- Mayor updates status via `bd update`
- Polecats work independently
- Issue state auto-syncs via JSONL; use `bd vc status` only to inspect Dolt state

---

## Token Budget

Per FIRE iteration (30s):

| Phase | Tokens | Notes |
|-------|--------|-------|
| FIND | ~300 | bd queries |
| IGNITE | ~100 | gt sling commands |
| REAP | ~250 | monitoring + validation |
| ESCALATE | ~100 | if failures |
| **Total** | ~750 | per iteration |

**Per hour**: ~90,000 tokens (120 iterations)
**Per 8-hour run**: ~720,000 tokens

Sustainable for long-running autonomous execution.

---

## Error Recovery

**Mayor session crash**:
```bash
# State is in beads, not memory
/crank <epic> <rig>  # Resumes from beads state
```

**Polecat stalled**:
```bash
gt polecat stale <rig>                    # Find stale
gt polecat check-recovery <rig>/<name>    # Decide: recover | nuke
gt polecat nuke <rig>/<name> --force      # Destroy
gt sling <issue> <rig>                    # Re-ignite
```

**Beads sync conflict**:
```bash
git -C "$(ao beads dir)" checkout --theirs issues.jsonl
git -C "$(ao beads dir)" add issues.jsonl
BEADS_DIR="$(ao beads dir)" br doctor
```

---

## Tuning Parameters

| Parameter | Default | Tuning Guidance |
|-----------|---------|-----------------|
| `MAX_POLECATS` | 4 | Increase for large epics, decrease for complex issues |
| `POLL_INTERVAL` | 30s | Decrease for fast issues, increase to save tokens |
| `MAX_RETRIES` | 3 | Increase for flaky tests, decrease for clean codebases |
| `BACKOFF_BASE` | 30s | Increase for rate-limited APIs |
| `STALL_THRESHOLD` | 5 polls | Decrease for tight deadlines |
