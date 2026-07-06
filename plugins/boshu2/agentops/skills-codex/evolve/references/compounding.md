# How Compounding Works

Two mechanisms feed the loop:

**1. Knowledge flywheel (each cycle is smarter):**
```
Session 1:
  ao lookup --query "recent learnings" (nothing yet)  → cycle runs blind
  $rpi fixes test-pass-rate       → post-mortem runs ao forge
  Learnings extracted: "tests/skills/run-all.sh validates frontmatter"

Session 2:
  ao lookup --query "recent learnings" (loads Session 1 learnings)  → cycle knows about frontmatter validation
  $rpi fixes doc-coverage                → approach informed by prior learning
  Learnings extracted: "references/ dirs need at least one .md file"
```

**2. Work harvesting (each cycle discovers the next):**
```
Cycle 1: $rpi fixes test-pass-rate
  → post-mortem harvests: "add missing smoke test for $evolve" → next-work.jsonl

Cycle 2: all GOALS.yaml goals pass
  → $evolve reads next-work.jsonl (exact repo first, then cross-repo '*', then legacy)
  → picks "add missing smoke test"
  → $rpi fixes it → post-mortem harvests: "update SKILL-TIERS count"

Cycle 3: reads next-work.jsonl → picks "update SKILL-TIERS count" → ...
```

The loop keeps running as long as post-mortem keeps finding follow-up work. Each $rpi cycle generates next-work items from its own post-mortem. The system feeds itself.

**Priority cascade:**
```
next-work.jsonl (harvested / queued work)    → exact repo first, then `*`, then legacy
Open beads (br ready)                        → durable tracked backlog
GOALS.yaml directives and failing goals      → explicit fitness gaps
Testing improvements                         → synthesize coverage / regression-test work
Validation + bug-hunt passes                 → tighten gates, discover real defects
Hotspots / TODO / drift / stale docs         → mine weak signals into work
Feature suggestions                          → propose new product work when remediation dries up
multiple empty queue + generator passes      → last-resort dormancy
60-minute circuit breaker                    → stop if no productive cycle in 60 min
kill switch                                  → immediate stop
```

The loop does NOT stop just because goals are met or the current queue is empty. It re-reads harvested work after every `$rpi` cycle, runs generator layers when queues are empty, and only stops after repeated empty queue + generator passes. Idle cycles are NOT committed to git — only appended locally. The idle streak is re-derived from disk at each session start, while `session-state.json` carries pending claim/generator resume state. Use the kill switch for intentional stops.
