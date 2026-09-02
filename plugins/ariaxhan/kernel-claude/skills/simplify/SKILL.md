---
name: simplify
description: "Lower cyclomatic complexity with AST-aware measurement, per-function budgets, regression diffs, and a project gate. Triggers: simplify, refactor, complexity, spaghetti."
user-invocable: true
allowed-tools: Agent, Bash, Read, Edit, Grep, Glob
kernel:
  kind: workflow
  version: 1
  side_effects: writes_source
  confirmation: none
---

<skill id="simplify">

<purpose>
AI-written code works but branches like a jungle. This skill forces a measured per-function
number, records its movement, and installs the same check in the project's normal verification.
Prose about "cleaner code" is not accepted.

Adapted from saurabhkumar8112/cyclomatic-complexity-skill (Apache-2.0). The refactoring model
never signs its own result; a verifier re-measures and runs the armed project gate.
</purpose>

<on_start>
agentdb recall "simplify complexity <files/symbols>" --global
</on_start>

<measure>
```bash
# violations, worst first (TSV: file, line, function, ccn, nloc)
${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh <repo-dir>
# only what this branch changed
${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh <repo-dir> <base-ref>
# complete snapshot + before/current diff
${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh --all <repo-dir> > before.tsv
${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh --diff before.tsv <repo-dir>
# CI ratchet: baseline contains only current over-budget debt
${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh --check-baseline .complexity-baseline.tsv <repo-dir>
```

JS/TS uses the project's installed ESLint and parser, so object-literal methods are real
functions. Lizard is the fallback for other languages. Its JS/TS fallback is NOT AST-complete:
it can attribute hundreds of lines to the preceding function and never enter methods inside a
returned object literal. The command names this fallback on stderr. Never treat it as proof for
that pattern: install/configure ESLint, or explicitly skip the file with a reason.

Project config is `.ccnrc` JSON:

```json
{
  "version": 1,
  "default": 15,
  "budgets": { "src/machine.ts:transition": 20 },
  "skip": { "src/legacy-repo.ts:*": "lizard cannot enter createLegacyRepo's returned methods" }
}
```

Selectors are `repo-relative-file:function` globs. `--skip 'selector=reason'` is the one-run
equivalent. A skip without a reason is invalid. Budgets are declared design constraints, not a
way to bless today's number: name why the function earns the higher ceiling in the config diff.

Exit 2 means invalid config or analyzer failure. Exit 3 means no analyzer. Either blocks
verification. Never replace an unavailable parser with an unlabelled hand count.

Ladder (default, project config outranks it):
- 1 to 5: leave alone
- 6 to 10: refactor only if already touching
- 11 to 15: refactor now
- over 15: must split
</measure>

<workflow>
1. Measure. Print the table before touching anything. Rank by CCN descending.
2. Confirm tests exist and pass. None: say so, refactor conservatively, propose one test per
   extracted function.
3. Save `--all` output as the before baseline. Refactor worst first, one function at a time.
4. Re-measure with `--diff before.tsv`. Any `regressed` row is unresolved.
5. Wire the project-owned gate before handoff:
   - add a `complexity` script/check using the project's checked-in runner or native analyzer;
   - seed `.complexity-baseline.tsv` with current over-budget rows only; the CI ratchet
     grandfathers those exact values, rejects increases/new violations, and requires a refreshed
     baseline after reductions or removals;
   - include it in `npm run verify`, Make/just verify, or the existing pre-commit gate;
   - run that exact parent command red against a seeded over-budget fixture, then green;
   - never point CI at a developer's plugin-cache path.
6. Hand off to the verifier. Its fresh diff and armed-gate run are the record.
</workflow>

<tactics order="preference">
1. Guard clauses: invert, return early, kill nesting.
2. Extract function. The name says what, not how. Names are documentation.
3. Lookup table or map instead of if/else or switch chains.
4. Named predicates: `if is_eligible_for_refund(order)` beats a four-clause boolean.
5. Polymorphism or strategy for switch-on-type, only when the switch appears in 2+ places.
6. Flatten loops: extract the body, `continue` instead of nested `if`.
</tactics>

<hard_rules>
- Preserve behavior. Tests before and after. Same inputs, same outputs, same errors.
- Do not game the metric. A dense one-liner hiding six branches is worse than the honest
  if-chain it replaced. Complexity moves into named units; it never disappears into cleverness.
  A CCN drop with a rising token count per line is the tell.
- Do not change public APIs or exported signatures without asking.
- One responsibility per function. If the name needs "and", split again.
- Small functions with clear names beat few functions with section comments.
- No optional finish: a manual complexity command without project verify/pre-commit wiring is incomplete.
- Never introduce the gate red on the existing default branch. Snapshot current debt, declare narrow
  budgets with reasons, then tighten them as functions improve.
</hard_rules>

<verify>
Spawn a verifier that never saw this session's reasoning. It receives: the diff, the before
table, the claimed after table, the test command, and this contract:

```
ACCEPTANCE: no measured function regresses; budgets hold; the project's normal verify path runs the gate
ACCEPT WHEN: fresh --diff says regressed=0; project verify passes; seeded over-budget fixture makes it fail; no exported signature changed
CHECK: ${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh --diff <before.tsv> <repo>; <project verify command>; <seeded failure probe>; git diff <base-ref> -- <files> | grep -E '^[-+](def |export |func |pub fn )'
ESCALATE IF: AST-aware JS/TS parsing is unavailable for object-literal methods, any row regresses, a skip lacks a concrete parser limitation, or a one-liner replaced a branch without a name
DISCOVERY AXIS: invariant
```
Builder and verifier identities go on the receipt. The builder never fills in "behavior verified".
</verify>

<output>
End with, and nothing after it:
```
## Complexity report
Reduced: N · unchanged: N · regressed: 0 · removed: N
Budgets: <config path>; exceptions: <none | selectors + reasons>
Gate: <project verify command> (seeded red -> clean green)
Verified by: <verifier identity>
```
Keep prose minimal. Numbers and diffs do the talking.
</output>

</skill>
