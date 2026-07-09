# Vibe Methodology

Core principles for AI-assisted development. "Vibe" = trust-but-verify.

---

## The 40% Rule

**Never exceed 40% context utilization.**

- Checkpoint at 35%
- Reset via session restart or `$research` artifact
- More context ≠ better results (hallucination risk increases)

---

## Three Levels of Verification

| Level | Vibe | Method | When |
|-------|------|--------|------|
| L1 | Accept | Structural check only | Boilerplate, formatting |
| L2 | Probe | Spot-check key logic | Normal implementation |
| L3 | Audit | Line-by-line review | Security, data handling |

**Default to L2.** Upgrade to L3 for:
- Authentication/authorization
- Financial calculations
- Data persistence
- External API calls

---

## Evidence Hierarchy

Trust in order:

1. **Running code** - Actually execute it
2. **Tests** - Passing tests prove behavior
3. **File contents** - Read the actual source
4. **Documentation** - May be stale
5. **Model claims** - Verify everything

---

## Working Patterns

### Incremental Verification
```
Write small piece → Test → Verify → Repeat
```

Don't write 500 lines then debug. Write 50, verify, continue.

### Checkpoint Often
- After each feature complete
- Before any risky change
- At natural boundaries

### Search Before Implement
```bash
# Always check for prior art
mcp__smart-connections-work__lookup --query="<topic>"
ls .agents/research/ | grep -i "<topic>"
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why Bad | Instead |
|--------------|---------|---------|
| Trust-and-paste | Hallucinations slip through | Always read generated code |
| Context stuffing | Degrades quality | Stay under 40% |
| Fix spiraling | Compounds errors | Reset and rethink |
| Skipping verification | Builds on bad foundation | Verify incrementally |

---

## The Research Discipline

1. **Scope first** - Define what you're looking for
2. **Search smart** - Use semantic search before grep
3. **Read selectively** - Don't load whole files
4. **Cite everything** - `file:line` for all claims
5. **Synthesize** - Connect findings to goal

---

## Session Hygiene

```bash
# Start
gt hook              # Check assigned work
br ready             # What's available

# Work
$research <topic>    # Creates artifact, saves context
$implement <issue>   # Focused execution

# End
bd vc status         # Optional Dolt status check; JSONL auto-sync is automatic
git commit           # Commit changes
git push             # WORK IS NOT DONE UNTIL PUSHED
```

---

## References

- `failure-patterns.md` - 12 specific failure modes
- `context-discovery.md` - 6-tier exploration hierarchy
- `~/.codex/CLAUDE-base.md` - Full vibe methodology
