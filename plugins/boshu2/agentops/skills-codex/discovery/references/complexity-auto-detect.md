# Complexity Auto-Detect in /discovery

## Precedence Contract

When `/discovery` auto-detects complexity, it uses **issue count** from the plan output. When `/rpi` classifies complexity, it uses **goal-string keywords**. These two systems can disagree.

### Resolution Order

1. **Explicit flag wins:** `--complexity=<level>` or `--deep`/`--fast-path` overrides everything.
2. **`/rpi` keyword classification** sets the initial level and passes it to `/discovery` via `--complexity=<level>`.
3. **`/discovery` issue-count reclassification** can **upgrade** but never **downgrade** the level.

### Example Scenarios

| `/rpi` keyword result | `/discovery` issue count | Final complexity |
|----------------------|-------------------------|-----------------|
| `fast` (short goal) | 1-2 issues | `fast` |
| `fast` (short goal) | 7+ issues | `full` (upgraded) |
| `standard` | 3-6 issues | `standard` |
| `standard` | 7+ issues | `full` (upgraded) |
| `full` (keyword hit) | 1-2 issues | `full` (no downgrade) |

### Rationale

Goal-string keywords are a heuristic — short goals can still produce complex epics. Issue count is a concrete signal from actual planning output. Allowing upgrades but not downgrades prevents under-ceremony for unexpectedly complex work while respecting explicit `--deep` signals.
