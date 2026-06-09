# Output Format

## Council Report (Markdown) — Validate Mode

```markdown
---
id: council-YYYY-MM-DD-<mode>-<target-slug>
type: council
date: YYYY-MM-DD
---

## Council Consensus: WARN

**Target:** Implementation of user authentication
**Modes:** validate, --mixed
**Judges:** 3 Claude (Opus 4.6) + 3 Codex (GPT-5.3-Codex)

---

### Verdicts

| Vendor | Judge 1 | Judge 2 | Judge 3 |
|--------|---------|---------|---------|
| Claude | PASS | WARN | PASS |
| Codex | WARN | WARN | WARN |

*(With `--preset`, column headers reflect perspective names instead of Judge N)*

---

### Shared Findings

| Finding | Severity | Fix | Ref |
|---------|----------|-----|-----|
| JWT implementation follows best practices | minor | No action needed | src/auth/jwt.py:15 |
| Refresh token rotation is correctly implemented | minor | No action needed | src/auth/refresh.py:42 |
| Rate limiting missing on auth endpoints | significant | Add rate limiting middleware to /auth/* routes | OWASP Authentication Cheatsheet |

### Disagreements

| Issue | Claude | Codex |
|-------|--------|-------|
| Rate limiting | Optional for internal APIs | Required per OWASP |
| Token expiry | 1 hour acceptable | Should be 15 minutes |

### Cross-Vendor Insights

**Claude-only:** Noted UX friction in token refresh flow
**Codex-only:** Flagged potential timing attack in token comparison

---

### Recommendation

Add rate limiting to auth endpoints. Consider reducing token expiry to 30 minutes as compromise.

---

*Council completed in 45s. 6/6 judges responded.*
```

## Brainstorm Report

```markdown
---
id: council-YYYY-MM-DD-<mode>-<target-slug>
type: council
date: YYYY-MM-DD
---

## Council Brainstorm: <Topic>

**Target:** <what we're brainstorming>
**Judges:** <count and vendors>

### Options Explored

| Option | Judge 1 | Judge 2 | Judge 3 |
|--------|---------|---------|---------|
| Option A | Assessment | Assessment | Assessment |
| Option B | Assessment | Assessment | Assessment |

### Recommendation

<synthesized recommendation with reasoning>

*Council completed in Ns. N/N judges responded.*
```

**Write to:** `.agents/council/YYYY-MM-DD-brainstorm-<topic>.md`

## Research Report

```markdown
---
id: council-YYYY-MM-DD-<mode>-<target-slug>
type: council
date: YYYY-MM-DD
---

## Council Research: <Topic>

**Target:** <what we're researching>
**Judges:** <count and vendors>

### Facets Explored

Each judge investigated a different aspect of the topic:

| Facet | Judge | Key Findings |
|-------|-------|-------------|
| <aspect 1> | Judge 1 | <summary> |
| <aspect 2> | Judge 2 | <summary> |
| <aspect 3> | Judge 3 | <summary> |

### Synthesized Findings

<merged findings across all judges, organized by theme>

### Open Questions

- <questions that emerged during research>

### Recommendation

<synthesized recommendation with reasoning>

*Council completed in Ns. N/N judges responded.*
```

**Write to:** `.agents/council/YYYY-MM-DD-research-<topic>.md`

## Debate Report Additions

When `--adversarial` is used, add these sections to any report format:

**Header addition:**
```markdown
**Mode:** {task_type}, --adversarial
**Rounds:** 2 (independent assessment + adversarial debate)
**Fidelity:** full (native teams -- judges retained full R1 context for R2)
```

If debate ran in fallback mode (re-spawned with truncated R1 verdicts), use instead:
```markdown
**Mode:** {task_type}, --adversarial
**Rounds:** 2 (independent assessment + adversarial debate)
**Fidelity:** degraded (fallback -- R1 verdicts truncated for R2 re-spawn)
```

**After the Verdicts table, add:**

```markdown
### Verdict Shifts (R1 -> R2)

| Judge | R1 Verdict | R2 Verdict | Changed? | Reason |
|-------|-----------|-----------|----------|--------|
| Judge 1 (or Perspective) | PASS | WARN | Yes | Accepted Judge 2's finding on rate limiting |
| Judge 2 (or Perspective) | WARN | WARN | No | Confirmed after reviewing counterarguments |
| Judge 3 (or Perspective) | PASS | PASS | No | Maintained -- challenged Judge 2's scope concern |

### Debate Notes

**Key Exchanges:**
- **Judge 1 <- Judge 2:** [what was exchanged and its impact]
- **Judge 3 vs Judge 2:** [where they disagreed and why]

**Steel-Man Highlights:**
- Judge 1 steel-manned: "[strongest opposing argument they engaged with]"
- Judge 2 steel-manned: "[strongest opposing argument they engaged with]"
```

**Convergence Detection:**

If Round 1 had at least 2 judges with different verdicts AND Round 2 is unanimous, add this flag:

```markdown
> **Convergence Detected:** Judges who disagreed in Round 1 now agree in Round 2.
> Review debate reasoning to verify this reflects genuine persuasion, not anchoring.
> Round 1 verdicts preserved above for comparison.
```

**Footer update:**
```markdown
*Council completed in {R1_time + R2_time}. {N}/{N} judges responded in R1, {M}/{N} in R2.*
```
