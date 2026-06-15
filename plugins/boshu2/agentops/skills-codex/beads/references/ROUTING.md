# Beads Routing Architecture

**For:** AI agents working in multi-workspace environments (Gas Town)
**Applies to:** Two-level beads deployments with Town + Rig structure

## Overview

In multi-agent environments, beads operates at two levels with automatic prefix-based routing.

## Two-Level Architecture

| Level | Location | sync-branch | Prefix | Purpose |
|-------|----------|-------------|--------|---------|
| Town | `~/gt/.beads/` | NOT set | `hq-*` | Mail, HQ coordination |
| Rig | `<rig>/crew/*/.beads/` | `beads-sync` | Olympian prefix | Project issues |

**Key points:**
- **Town beads**: Mail and coordination. Commits to main (single clone, no sync needed)
- **Rig beads**: Project work in git worktrees (crew/*, polecats/*)
- The rig-level `<rig>/.beads/` is **gitignored** (local runtime state)
- Rig beads use `beads-sync` branch for multi-clone coordination

## Prefix-Based Routing

`bd` commands automatically route to the correct rig based on issue ID prefix:

```bash
bd show gt-xyz   # Routes to daedalus beads
bd show ap-abc   # Routes to compile beads
bd show hq-123   # Routes to town beads
```

**How it works:**
- Routes defined in `~/gt/.beads/routes.jsonl`
- `gt rig add` auto-registers new rig prefixes
- Each rig's prefix (e.g., `gt-`) maps to its beads location

**Debug routing:**
```bash
BD_DEBUG_ROUTING=1 bd show <id>
```

**Conflicts:** If two rigs share a prefix, use `bd rename-prefix <new>` to fix.

### Common Prefixes

| Prefix | Rig | Prefix | Rig |
|--------|-----|--------|-----|
| `hq` | town (coordination) | `gt` | daedalus |
| `ap` | compile | `ho` | argus |
| `be` | chronicle | `gitops` | gitops |
| `starport` | starport | `fr` | cyclopes |

## Creating Beads for Rig Work

**HQ beads (`hq-*`) CANNOT be hooked by polecats!**

`gt sling` uses `bd update` which lacks cross-database routing. Beads must exist
in the target rig's database to be hookable.

| Work Type | Create From | Gets Prefix | Can Sling? |
|-----------|-------------|-------------|------------|
| Mayor coordination | `~/gt` | `hq-*` | No |
| Rig bug/feature | Rig's beads | `gt-*`, `ap-*`, etc. | Yes |

**From Mayor, to create a slingable bead:**

```bash
# Use BEADS_DIR to target the rig's beads database
BEADS_DIR=~/gt/daedalus/mayor/rig/.beads br create --title="Fix X" --type=bug
# Creates: gt-xxxxx (daedalus prefix)

BEADS_DIR=~/gt/compile/mayor/rig/.beads br create --title="Add Y" --type=feature
# Creates: ap-xxxxx (compile prefix)
```

**Then sling normally:**
```bash
gt sling gt-xxxxx daedalus   # Works - bead is in daedalus's database
gt sling ap-xxxxx compile     # Works - bead is in compile's database
```

## Common Gotchas

### Wrong Prefix for Rig Work

Creating from `~/gt` gives `hq-*` which polecats can't hook.

- **WRONG:** `br create --title="daedalus bug"` from town root
  - Creates `hq-xxx` (unhookable by polecats)
- **RIGHT:** `BEADS_DIR=~/gt/daedalus/mayor/rig/.beads br create ...`
  - Creates `gt-xxx` (slingable)

### GitHub URLs

Use `git remote -v` to verify repo URLs - never assume orgs like `anthropics/`.

### Temporal Language Inverts Dependencies

"Phase 1 blocks Phase 2" is backwards in dependency semantics:

```bash
# WRONG (temporal thinking: "1 before 2")
br dep add phase1 phase2

# RIGHT (requirement thinking: "2 needs 1")
br dep add phase2 phase1
```

**Rule:** Think "X needs Y", not "X comes before Y". Verify with `bd blocked`.

## Sync Behavior by Level

### Town Level
- Single clone, no sync branch needed
- Commits directly to main
- Used for: mail, HQ coordination beads

### Rig Level
- Multiple worktrees (crew/*, polecats/*)
- Uses `beads-sync` branch for coordination
- Coordination happens through normal git workflows plus automatic JSONL sync
- Use `bd vc status` to inspect Dolt state when you need backend visibility

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bead not found | Check prefix matches rig: `BD_DEBUG_ROUTING=1 bd show <id>` |
| Can't sling HQ bead | Create bead in rig's database with `BEADS_DIR` |
| Prefix conflict | Run `bd rename-prefix <new>` on one rig |
| Sync fails | Ensure `beads-sync` branch exists: `git branch beads-sync` |
