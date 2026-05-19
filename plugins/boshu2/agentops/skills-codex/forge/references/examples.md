# Forge Examples

Concrete walkthroughs of the two main forge invocation paths.

## SessionEnd Hook Invocation

**Hook triggers:** `session-end.sh` runs when session ends

**What happens:**
1. Hook calls `ao forge transcript --last-session --queue --quiet`
2. CLI analyzes session transcript for decisions, learnings, failures, patterns
3. CLI writes session ID to `.agents/ao/pending.jsonl` queue
4. Next session start triggers `/forge --promote` to process the queue

**Result:** Session transcript automatically queued for knowledge extraction without user action.

## Manual Transcript Mining

**User says:** `/forge <path>` or "mine this transcript for knowledge"

**What happens:**
1. Agent identifies transcript path or uses `ao forge transcript --last-session`
2. Agent scans transcript for knowledge patterns (decisions, learnings, failures, patterns)
3. Agent scores each extraction by confidence (0.0-1.0)
4. Agent writes candidates to `.agents/forge/YYYY-MM-DD-forge.md`
5. Agent indexes forge output with `ao forge markdown`
6. Agent reports extraction counts and candidate locations

**Result:** Transcript mined for reusable knowledge, candidates ready for human review or 2+ citations promotion.
