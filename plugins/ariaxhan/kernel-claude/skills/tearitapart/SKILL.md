---
name: tearitapart
description: "Critical pre-implementation review. Find what AI breaks. Verdict: PROCEED, REVISE, or RETHINK. Triggers: review plan, tear apart, critique, analyze."
user-invocable: true
allowed-tools: Read, Bash, Grep, Glob
kernel:
  kind: validator
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="tearitapart">

<purpose>
Pre-implementation review. Check Big 5, security, testing, architecture.
Goal: find real problems, not generic concerns.
</purpose>

<skill_load>
Load: skills/quality/SKILL.md, skills/build/reference/testing.md, skills/tearitapart/reference/security.md
Reference: skills/quality/reference/quality-research.md
</skill_load>

<on_start>
```bash
agentdb read-start
```
</on_start>

<phase id="1_gather">
- Read plan/spec
- List files to be touched
- Check git status
- Check AgentDB for prior contracts
- Read _meta/research/ for anti-patterns

output:
  scope: N files
  tier: 1|2|3
  prior_work: contracts, research found
</phase>

<phase id="2_big5">
Run Big 5 checks from skills/quality/SKILL.md:

1. input_validation: Zod schema? Parameterized queries?
2. edge_cases: null, empty, unicode, timeout?
3. error_handling: no empty catch? Logged with context?
4. duplication: same logic repeated?
5. complexity: functions < 30 lines?

Use quick_checks from quality skill for detection.
</phase>

<phase id="3_security">
Load: skills/tearitapart/reference/security.md

critical:
- [ ] No hardcoded secrets
- [ ] Auth tokens in httpOnly cookies
- [ ] Rate limiting
- [ ] HTTPS enforced

injection:
- [ ] SQL: parameterized only
- [ ] XSS: DOMPurify
- [ ] CSRF: tokens on state changes
</phase>

<phase id="4_testing">
Load: skills/build/reference/testing.md

verify:
- Tests exist BEFORE implementation?
- Edge cases covered?
- Assertions specific (not toBeTruthy)?
- Mocks at boundaries only?

red_flags:
- "Will add tests later"
- 100% coverage, weak assertions
- No error path testing
</phase>

<phase id="5_architecture">
Load: skills/architecture/SKILL.md

verify:
- Follows existing patterns?
- Interface stability?
- Modular boundaries?
- Dependency direction correct?
</phase>

<verdict>
<PROCEED>
No Big 5 violations. Security passes. Tests defined.
Output: "PROCEED with caveats: [list]"
</PROCEED>

<REVISE>
1-2 Big 5 violations (fixable). Missing security items.
Output: "REVISE: [changes with file:line]"
</REVISE>

<RETHINK>
3+ Big 5 violations. Fundamental security gaps. No tests.
Output: "RETHINK: [why flawed] → [alternative]"
</RETHINK>

<ask_user>
  Use AskUserQuestion when: verdict is REVISE or RETHINK
  Ask: "Verdict: {REVISE|RETHINK}. Want details on specific findings, or proceed with fixes?"
  Options: show details, proceed with fixes, override and proceed anyway
</ask_user>
</verdict>

<output_format>
Save to `_meta/reviews/{feature}-teardown.md`:

```yaml
# Tear Down: {feature}
reviewed: {timestamp}
tier: {1|2|3}
scope: {N files}

## Big 5
input_validation: pass|fail
edge_cases: pass|fail
error_handling: pass|fail
duplication: pass|fail
complexity: pass|fail

## Verdict: PROCEED | REVISE | RETHINK
{reasoning}

## Action Items
1. {fix with file:line}
```
</output_format>

<on_complete>
```bash
agentdb write-end '{"command":"tearitapart","verdict":"X","big5_violations":N}'
```
</on_complete>

</skill>
