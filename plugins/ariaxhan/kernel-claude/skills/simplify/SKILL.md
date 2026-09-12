---
name: simplify
description: "Simplify code, plans and systems without losing required outcomes; delete machinery that earns nothing; for code, AST-measured complexity with regression gates. Triggers: simplify, refactor, complexity, overengineered, dead code, useless guard."
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
Simplification makes the road easier; it does not change the destination. Preserve every required
outcome, feature, behavior, and explicit constraint. Simplify only how they are delivered: fewer
branches, concepts, components, dependencies, states, handoffs, and duplicated mechanisms.

For code, this skill forces a measured per-function number, records its movement, and installs the
same check in the project's normal verification. Prose about "cleaner code" is not accepted.

Adapted from saurabhkumar8112/cyclomatic-complexity-skill (Apache-2.0). The refactoring model
never signs its own result; a verifier re-measures and runs the armed project gate.
</purpose>

<on_start>
agentdb recall "simplify complexity <files/symbols>" --global
</on_start>

<mode>
Pick one at the top of the run and say which:
- `code` — source changes. Full measure + gate path below.
- `system` — plans, roadmaps, backlogs, docs, pipelines, process. Preservation contract and
  deletion doctrine apply; the complexity table does not. Never emit `Reduced: 0 · regressed: 0`
  for work with no functions in it; use the system report block.
Mixed work runs both blocks, never one blurred into the other.
</mode>

<deletion_doctrine>
Deletion beats repair. When something is broken, the first question is whether it should exist.

- Broken test: is the test wrong? A test asserting behavior nobody requires, or coupling to an
  implementation detail, gets deleted, not repaired. Delete the test, keep the behavior test.
- Broken guard, hook, lint rule, or check: does it prevent a real failure that actually happened?
  No evidence of a caught failure and it costs every run -> delete it. A guard that fires on
  correct work is worse than no guard: it trains everyone to override.
- Broken feature path nothing reaches: delete the path, not patch it.
- Machinery with a cleaner replacement already present: delete the old one in the same change.

Cut fast and hard. Do not stage a deprecation for code only this repo calls.

Repair instead of deleting only when: it is on the preservation contract; or it is the sole
defense against an irreversible failure (data loss, secret leak, production destruction); or
deleting it breaks a published API or another repo's contract. Name which one applies.

Every deletion is recorded: what, why it earned nothing, what now covers the case (or that
nothing needs to). Deleting an item on the preservation contract is a scope cut, not a
simplification, and is forbidden.
</deletion_doctrine>

<preflight>
Run before measuring. A mid-run analyzer failure is a preventable state, not a surprise.
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh --engine auto <repo-dir> >/dev/null   # exit 3 = no analyzer
git fetch -q origin && git diff --quiet origin/<default> -- .complexity-baseline.tsv .ccnrc \
  || echo "baseline/config differs from the default branch: refresh before measuring"
```
- No analyzer (exit 3) or invalid config (exit 2): stop and install it. Never hand-count.
- JS/TS without project ESLint: the lizard fallback cannot see object-literal methods. Install
  ESLint or skip the file with that exact reason. Never call the fallback proof.
- The baseline is a committed file measured against the current default branch. A baseline from a
  stale checkout is not a baseline; refresh it from `origin/<default>` first and say so.
- Sandboxed workspace: `complexity.py` redirects an unwritable uv cache to tmp on its own.
</preflight>

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

Ladder (default, project config outranks it):
- 1 to 5: leave alone
- 6 to 10: refactor only if already touching
- 11 to 15: refactor now
- over 15: must split
</measure>

<workflow>
1. Write the preservation contract to `.simplify-contract.md` before editing: every required
   outcome, feature, behavior, explicit constraint, and acceptance condition from the request and
   current source of truth, one checkable line each, with its source. Deferred is not preserved
   unless the source already defers it. A contract held only in the model's head is not a
   contract; the verifier diffs this file.
2. Trace each contract line to a concrete part of the proposed result, in the file. Any line with
   no route invalidates the simplification. Never redefine product scope, success, or priority to
   make the implementation smaller.
3. List deletion candidates against `<deletion_doctrine>`: dead paths, tests asserting nothing
   required, guards with no caught-failure evidence, superseded machinery. Cut them first; the
   cheapest complexity reduction is code that stops existing.
4. `code` mode: run preflight, then measure. Print the table before touching anything, ranked by
   CCN descending. `system` mode: skip to 8.
5. Confirm tests exist and pass. None: say so, refactor conservatively, propose one test per
   extracted function.
6. Save `--all` output as the before baseline. Refactor worst first, one function at a time.
7. Re-measure with `--diff before.tsv`. Any `regressed` row is unresolved.
8. Wire the project-owned gate before handoff:
   - add a `complexity` script/check using the project's checked-in runner or native analyzer;
   - seed `.complexity-baseline.tsv` with current over-budget rows only; the CI ratchet
     grandfathers those exact values, rejects increases/new violations, and requires a refreshed
     baseline after reductions or removals;
   - commit the baseline and record the ref it was measured against;
   - include it in `npm run verify`, Make/just verify, or the existing pre-commit gate;
   - run that exact parent command red against a seeded over-budget fixture, then green;
   - never point CI at a developer's plugin-cache path.
9. Re-check `.simplify-contract.md` line by line against the result. Anything dropped, weakened,
   postponed, or made optional is a regression, even when the complexity score improves. Every
   surviving line that moved to a later phase names its delivery route and acceptance condition
   in the file, or it was cut.
10. Hand off to the verifier. Its fresh diff, contract check, deletion review, and armed-gate run
    are the record.
</workflow>

<tactics order="preference">
1. Delete it. Nothing is simpler than absent code.
2. Guard clauses: invert, return early, kill nesting.
3. Extract function. The name says what, not how. Names are documentation.
4. Lookup table or map instead of if/else or switch chains.
5. Named predicates: `if is_eligible_for_refund(order)` beats a four-clause boolean.
6. Polymorphism or strategy for switch-on-type, only when the switch appears in 2+ places.
7. Flatten loops: extract the body, `continue` instead of nested `if`.
</tactics>

<hard_rules>
- Preserve the destination: every requested outcome and feature remains required and reachable.
  Simplify architecture and execution, never the user's ambition or product scope.
- Preserve behavior that anything requires. Tests before and after. Same inputs, same outputs,
  same errors.
- Removal is allowed, and preferred, for duplication, dead paths, unearning guards, and machinery
  whose absence cannot change any contract line. "Not now," "later," "manual for the pilot," and
  narrower audiences/products are scope cuts when the source of truth did not already say them.
- Do not use sequencing as deletion. Later phases must still name their delivery route and
  acceptance condition; evidence gates may reorder work, but cannot cancel it.
- Do not game the metric. A dense one-liner hiding six branches is worse than the honest
  if-chain it replaced. Complexity moves into named units; it never disappears into cleverness.
  A CCN drop with a rising token count per line is the tell.
- Do not change public APIs or exported signatures without asking.
- One responsibility per function. If the name needs "and", split again.
- Small functions with clear names beat few functions with section comments.
- No optional finish: a manual complexity command without project verify/pre-commit wiring is
  incomplete.
- Never introduce the gate red on the existing default branch. Snapshot current debt, declare
  narrow budgets with reasons, then tighten them as functions improve.
- The verifier is a different agent than the builder. `self`, `builder self-measure`, `primary
  lane validation`, a script the builder wrote this session, and an unfilled `<verifier identity>`
  placeholder are all invalid signatures. An unsigned report is an unfinished run.
</hard_rules>

<verify>
Spawn a verifier that never saw this session's reasoning. It receives: the diff,
`.simplify-contract.md`, the deletion list, the before table, the claimed after table, the test
command, and this contract:

```
ACCEPTANCE: every contract line has an equally strong delivery route; every deletion is justified under the deletion doctrine; no measured function regresses; budgets hold; the project's normal verify path runs the gate
ACCEPT WHEN: contract file checks line by line with zero removed, weakened, newly deferred, or optional outcomes; every deleted test/guard/path names what it failed to earn and what covers the case now; fresh --diff says regressed=0; project verify passes; seeded over-budget fixture makes it fail; no exported signature changed
CHECK: diff .simplify-contract.md against the source of truth and the result line by line; ${CLAUDE_PLUGIN_ROOT}/scripts/complexity.sh --diff <before.tsv> <repo>; <project verify command>; <seeded failure probe>; git diff <base-ref> --diff-filter=D --name-only; git diff <base-ref> -- <files> | grep -E '^[-+](def |export |func |pub fn )'
ESCALATE IF: any contract line lacks a route or became weaker/later/optional; a deletion removed the only defense against an irreversible failure; AST-aware JS/TS parsing is unavailable for object-literal methods; any row regresses; a skip lacks a concrete parser limitation; or a one-liner replaced a branch without a name
DISCOVERY AXIS: invariant
```
Builder and verifier identities go on the receipt and must differ. The builder never fills in
"behavior verified".
</verify>

<output>
End with the block for the mode you ran, and nothing after it.

`code`:
```
## Complexity report
Reduced: N · unchanged: N · regressed: 0 · removed: N
Deleted: <file:symbol - what it failed to earn> | none
Destination: N/N contract lines preserved · weakened/deferred/removed: 0 (.simplify-contract.md)
Budgets: <config path>; exceptions: <none | selectors + reasons>
Gate: <project verify command> (seeded red -> clean green), baseline @ <ref>
Verified by: <verifier identity, not the builder>
```

`system`:
```
## Simplification report
Destination: N/N contract lines preserved · weakened/deferred/removed: 0 (.simplify-contract.md)
Removed: <duplicated mechanism / dead step / unearning gate - why it earned nothing> | none
Collapsed: <what merged into what>
Sequenced: <item - later phase, its delivery route, its acceptance condition> | none
Verified by: <verifier identity, not the builder>
```
Keep prose minimal. Numbers and diffs do the talking.
</output>

</skill>
