---
name: quality
description: "AI code quality checks. The Big 5: input validation, edge cases, error handling, duplication, complexity. Triggers: quality, big 5, ai code, review, validate."
allowed-tools: Read, Grep, Bash
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="quality">

<purpose>
AI code is 1.7x buggier. These 5 checks catch 80% of issues.
Load this skill for any review, validation, or implementation work.
</purpose>

<reference>
Verbose research: skills/quality/reference/quality-research.md
</reference>

<big5>
<check id="1" name="input_validation" detection="grep -r 'req\.body' | grep -v 'parse\|validate\|z\.'">
Every endpoint has Zod/Pydantic schema. Parameterized queries only.
</check>

<check id="2" name="edge_cases" detection="search for array access without length check">
Handle: null, empty array, zero-length string, timeout, unicode.
</check>

<check id="3" name="error_handling" detection="grep -r 'catch.*{}'">
No empty catch. Errors logged with context. User messages generic.
Silent swallowing is the worst variant: a catch/onError that returns a masked or
generic body without first logging method/path/cause hides the root failure behind
a 500 and costs a full re-diagnosis per incident. Every handler logs the cause
before it masks. Missing config/dependency is a NAMED condition in the response
(which var, which service), never a generic error.
</check>

<check id="4" name="duplication" detection="jscpd or manual review">
Same logic in 3+ places = extract to utility.
</check>

<check id="5" name="complexity" detection="eslint complexity rule">
Functions under 30 lines. No nested ternaries > 2 levels.
</check>

<check id="6" name="gate_integrity" detection="seed a known violation and confirm the gate goes red">
A gate nobody has seen fail is not a gate. Before trusting any check you ship or run:
- Prove it red. Seed the exact violation it claims to catch, watch it fail, then unseed.
  A gate that has only ever printed PASS is measuring nothing.
- The checker re-derives its evidence. A hash, a "PASS" string, a file that merely exists,
  or a count supplied by the thing being checked is an assertion, not evidence. Read the
  bytes, run the command, fetch the remote.
- Exit 0 with empty or blank output is a failure, not a pass. Never pipe a gate to
  `tail`/`head`; the pipe reports the pager's exit code.
- A gate that stays green after you delete the code it guards is blind. Delete-and-rerun
  is the cheapest mutation test there is.
- Randomness in a gate makes it a coin flip. Pin the seed or pin the input.
- Absence of a run is red, not pending.
</check>
</big5>

<quick_checks>
```bash
# 1. Missing validation
grep -r "req\.body" --include="*.ts" --include="*.js" | grep -v "parse\|validate\|z\." | head -5

# 2. Empty catch blocks
grep -r "catch.*{}" --include="*.ts" --include="*.js" | head -5

# 3. String concat in queries (SQL injection)
grep -rE "SELECT.*\$\{|INSERT.*\$\{" --include="*.ts" --include="*.js" | head -5
```
</quick_checks>

<data_correctness>
For any pipeline that extracts or transforms figures (financial, metrics, counts):
- Parse deterministically (a real parser, regex, typed loader). The LLM never
  generates, transforms, or "fixes" numeric values.
- Units are explicit at parse time (percent vs fraction, counts vs currency);
  a value never crosses unit categories through arithmetic.
- Tie-out gate: derived aggregates must reproduce the source's own totals before
  any output is shown downstream. A delta between your output and the source is
  assumed to be YOUR normalization bug until proven otherwise.
- Silent-empty guard: "no findings" produced from an empty parse is a failure of
  the parse, not a finding.
</data_correctness>

<verdict>
Any Big 5 violation = NOT READY
Fix before commit. No exceptions.
</verdict>


<on_complete>
agentdb write-end '{"skill":"quality","big5_checked":true,"violations":N}'
</on_complete>

</skill>
