---
name: review
description: "Code review for PRs or staged changes. >80% confidence threshold. Verdict: APPROVE, REQUEST CHANGES, or COMMENT. Triggers: review, pr, code review."
user-invocable: true
allowed-tools: Read, Bash, Grep, Glob
kernel:
  kind: validator
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="review">

<purpose>
Review code changes for quality, correctness, security.
Only report issues with >80% confidence.

Load: skills/build/reference/testing.md, skills/tearitapart/reference/security.md
Reference: _meta/research/ai-code-anti-patterns.md
</purpose>

<context>
ai_code_stats:
  buggier: 1.7x more issues than human code
  security: 40-62% contain vulnerabilities
  findings: 10.83 per AI PR vs 6.45 human

priority: check Big 5 first (what AI actually breaks)
</context>

<on_start>
```bash
agentdb read-start
```

<identify_scope>
```bash
gh pr diff {number}        # For PRs
git diff --staged          # For staged
git diff HEAD~1            # For recent
```
</identify_scope>

<deterministic_lane>
Machines first, then judgment. Run before reading a single diff hunk:

```bash
"${CLAUDE_PLUGIN_ROOT:-.}/scripts/deterministic-review.sh" <repo-dir> [base-ref]
```

Parallel gitleaks / semgrep(p/security-audit) / eslint / ruff / shellcheck / actionlint /
zizmor / osv-scanner — whatever is installed; diff-scoped when base-ref given; exit 1 on
HIGH (secrets, security SAST, high CVEs). Feed findings.tsv into the review as ground
truth. Lanes marked SKIPPED are reported as NOT CHECKED, never as clean.
</deterministic_lane>
</on_start>

<confidence_threshold>
| Confidence | Category | Report? |
|------------|----------|---------|
| 95%+ | Definite bug | YES |
| 85-95% | Likely issue | YES |
| 70-85% | Possible issue | MAYBE |
| <70% | Style preference | NO |
</confidence_threshold>

<big5 name="BIG 5: AI-SPECIFIC CONCERNS">
Check these FIRST - what AI actually breaks:

<check id="1_input_validation">
- Zod/Pydantic schema for every API endpoint?
- Parameterized queries (no string concat)?
- File uploads validated (size, type, extension)?
detection: grep -r "req\.body" | grep -v "parse\|validate\|z\."
</check>

<check id="2_edge_cases">
- Null/undefined handling present?
- Empty arrays handled (length check)?
- Zero-length strings rejected?
- Timeout handling for external calls?
</check>

<check id="3_error_handling">
- No empty catch blocks?
- Errors logged with context?
- User-facing messages generic?
detection: grep -r "catch.*{}" (empty catch)
</check>

<check id="4_duplication">
- Same logic repeated in multiple places?
- Should be extracted to shared utility?
</check>

<check id="5_complexity">
- Run the configured project verify command first. If complexity is not on that armed path,
  report the enforcement gap; a manual measurement is not a gate.
- Any function above its `.ccnrc` budget? A number, not a guess.
- If a baseline exists, does the diff say `regressed=0`?
- For JS/TS, did stderr name `eslint AST`? Lizard's fallback does not see object-literal methods.
- Nested ternaries > 2 levels?
detection: ${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh <repo> <base-ref>; ${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh --diff <baseline.tsv> <repo>
fix: /kernel:simplify on the listed functions
</check>
</big5>

<checklist>
<section name="Logic & Correctness">
- [ ] Edge cases handled
- [ ] Error paths covered
- [ ] Null checks present
- [ ] Type safety
</section>

<section name="Security">
- [ ] Input validation (Zod schema)
- [ ] No hardcoded secrets
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevented (DOMPurify)
- [ ] Auth tokens in httpOnly cookies
</section>

<section name="Performance">
- [ ] No N+1 queries
- [ ] Appropriate caching
</section>
</checklist>

<refute_before_report>
Before a finding enters the report, check it against
reference/refutation-patterns.md (11 false-alarm families + 5 refutation moves).
A finding matching a family needs evidence distinguishing it from the refuted precedent.
Severity gates from the same file apply: falsification check before CRITICAL, consensus
deflation, authority stripping on CVEs, and the judge's own additions get refuted too.
Refuted candidates go in the report WITH their refutations; if the project keeps a
refutation-corpus file, append new refuted false alarms to it in the same session.
</refute_before_report>

<output_format>
CODE REVIEW
===========
Files: X changed
Findings: Y (Z critical)

CRITICAL
--------
[file:line] Issue (confidence: XX%)
  → Fix: suggestion

HIGH
----
[file:line] Issue (confidence: XX%)
  → Fix: suggestion

Summary: APPROVE | REQUEST CHANGES | COMMENT
</output_format>

<ask_user>
  Use AskUserQuestion when: a finding is between 70-85% confidence (ambiguous)
  Ask: "Found {issue} at {file:line} (confidence {X}%). Intentional, or should I flag it?"
  Options: intentional — skip, flag it, investigate deeper
</ask_user>

<verdict_rules>
Review is finite because its purpose is AUTHORIZATION, not exhaustion. Approve once the change
improves the health of the codebase, not once nothing else can be found. Nothing else can ever
be found. (#204)

- **APPROVE**: no finding clears the block bar. **Open non-blocking comments do NOT prevent
  APPROVE** — say the issue number out loud and approve. Forcing another round to re-check a nit
  costs more than the nit.
- **REQUEST CHANGES**: at least one finding clears the block bar below.
- **COMMENT**: findings worth saying, none blocking, and the author asked for a read rather than
  a decision.

<block_bar>
A finding blocks only with ALL of:
1. pasted output, not a described procedure
2. a distance proof threshold cleared — distance sets how much evidence is needed, never whether
   a finding may block:
   d0 changed code fails · d1 violates a declared invariant · d2 pre-existing defect this change
   exposed, needs a user-visible consequence · d3+ needs outside assumptions, blocks only on an
   executed demonstration or a cited prior failure. Never auto-close d3; taste never clears it,
   a real outcome does.
3. a named observable failure: predict what breaks and how we would see it
4. violates the acceptance profile: tag the finding's `dimension`, and let the profile's
   `blocks_at` map decide the threshold for that dimension. A production-hardening finding on a
   demo is not a blocker however real it is, and a privacy finding on a demo IS one when the
   profile says so. The `stage` label never decides; the dimensions do.

Everything else is filed with its `distance:N` label under the `quarantine` milestone. Recurrence
is signal, silence is a verdict.

Complexity clears the block bar only when changed code exceeds a declared budget, a regression
diff names the increase, or the acceptance record requires the project gate and that armed path
does not run it. A lizard result over JS/TS object-literal methods cannot support APPROVE or FAIL;
it is `NOT CHECKED` until an AST-aware parser runs.
</block_bar>

Read the acceptance record before reviewing: claims, declared invariants, and tradeoffs already
accepted. If the commit carries one, it is FROZEN and adjudication will refuse a FAIL. Reopening
takes `new_failing_input`, `changed_dependency`, `missed_requirement`, `disproven_assumption`,
`profile_changed`, or `owner_promotion`. A new reviewer is not a reopen event.
Never ask a reviewer whether criticism is complete; it cannot answer and will always say no.
</verdict_rules>

<on_complete>
Emit findings as a `kernel.verdict/v1` document and let the acceptance function decide. The
reviewer never grades its own completeness.

```bash
python3 scripts/adjudicate.py findings.json --text --strict   # 0 PASS · 1 FAIL · 2 INVALID
agentdb write-end '{"command":"review","verdict":"X","critical":N,"high":N,"big5_violations":N,"quarantined":N}'
```

`cannot_falsify` is mandatory and non-empty. State what this review structurally could not see
(no real device, conformance only, no live data, a suite that did not finish). Silence about
coverage reads as coverage.
</on_complete>

</skill>
