# /vibe Examples

## Security Audit with Spec Compliance

**User says:** `/vibe --preset=security-audit src/auth/`

**What happens:**
1. Agent searches for spec (checks `bd show`, `.agents/plans/`, git log)
2. Agent runs complexity analysis (radon/gocyclo) on `src/auth/`
3. Agent runs constraint tests (`internal/constraints/*_test.go`) if present
4. Agent runs `codex review --uncommitted` for diff-focused review
5. Agent invokes `/council --deep --preset=security-audit validate src/auth/` with spec in packet
6. Spec found: 3 judges use security-audit personas + spec-compliance judge added (4 total)
7. Report written to `.agents/council/<timestamp>-vibe-src-auth.md`

**Result:** Security-focused review with attacker/defender/compliance perspectives and spec validation.

## Developer-Experience Code Review (PRODUCT.md detected)

**User says:** `/vibe recent`

**What happens:**
1. Agent detects `PRODUCT.md` in project root
2. Agent searches for spec (found: bead na-0042)
3. Agent runs complexity + constraint tests + codex review
4. Agent invokes `/council --deep --preset=code-review --perspectives="api-clarity,error-experience,discoverability" validate recent`
5. Auto-escalation: 6 judges spawn (3 code-review + 3 DX perspectives)
6. Judges review against spec + developer experience criteria

**Result:** Code review augmented with API clarity, error messages, and discoverability checks.

## Fast Inline Check (No Spawning)

**User says:** `/vibe --quick recent`

**What happens:**
1. Agent runs complexity analysis inline (radon/gocyclo)
2. Agent runs constraint tests and codex review
3. Agent performs structured self-review using council schema (no subprocess spawning)
4. Report written to `.agents/council/<timestamp>-vibe-recent.md` labeled `Mode: quick (single-agent)`

**Result:** Sub-60s validation for routine pre-commit checks, no multi-agent overhead.
