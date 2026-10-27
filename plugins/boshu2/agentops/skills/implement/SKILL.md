---
name: implement
description: 'Change or repair code, config or services without weakening tests; report what ran and what did not. Use when: implementing a change or fixing a defect.'
practices:
- tdd
- refactoring
- small-batch-flow
hexagonal_role: driving-adapter
consumes: []
produces:
- subject-manifest.v1
output_contract: 'content identity, author context ID and check facts through the native handoff; subject-manifest.v1 at the judgment boundary'
context_rel:
- kind: customer-of
  with: plan
skill_api_version: 1
user-invocable: true
metadata:
  graph_root: true
  tier: execution
  dependencies: []
  capabilities: [execute_one_experiment, collect_factual_evidence]
  effects: [modify_declared_subject, derive_subject_manifest]
  canonical_status: canonical
  disposition: keep
  triggers: ["execute the next wave", "per-lane evidence", "fix this bug", "CI is red", "loosen the assertion"]
---

# Implement

Implement the accepted outcome. Repair ordinary known defects directly. Use the
existing intent; a clear edit needs no Plan first. Implement owns source changes
and factual checks. Read changed paths from Git (`git status --porcelain`,
`git diff --name-only <base>`), never from memory;
`ao provenance manifest --root <repo>` with one `--include <path>` per declared
path digests only the paths you declare and runs no Git. Copy check results from the command output.

## Rules that decide the result

- **Fix the cause, not the oracle.** Never loosen an assertion, tolerance,
  golden, fixture or suppression, or substitute a mock or placeholder, to turn
  a check green; nor change what the check runs against: code that acts
  differently under test or CI, a newly silenced failure path, or a check made
  non-blocking or skipped. A check that fails against accepted behavior points
  at a product defect; changing what the check accepts is an acceptance change
  and needs caller authority.
- **Find live consumers before editing.** Search the callers, readers, scripts,
  docs and tests of every edited function, type, path, format or message. For
  each one, state whether the change affects it and which check covers it. When
  retiring or renaming, consumers include installations, lookups and old-name
  invocations; preserve historical provenance. If the replaced interface never
  merged or shipped and every consumer update fits the scope, update them and
  delete the old version in the same change, with no alias or shim; otherwise
  keep the old version working or report it.
- **Name discriminating checks.** A behavioral change preserves RED
  for the expected missing behavior: name the check that fails before the edit
  and passes after ([Test's proof rule](../test/SKILL.md#critical-constraints)),
  plus the check for each affected consumer.
- **Report only what ran.** Give exact commands and results. List every check
  you did not or could not run as not run. Never call unrun work verified,
  fixed or green. Output can show as soon as a command runs, so keep secrets
  out when you build it: credentials stay in the environment, output that may
  carry tokens goes to a file, and only redacted excerpts are shown.

When changing a public failure path, preserve its native failure signal and
check that its recovery advice matches any work already performed. For uncertain
write outcomes or unattended callers, use only the relevant checks in
[Test's error recovery method](../test/references/error-recovery.md).

For an accepted bounded shortcut, review feedback or a defect your change
introduced, an authorized commit, history rewrite or merge conflict, dependency
upgrade, removal, blocked operation, a decision read from another tool's state
or your own uncertain write, use only the matching [change safety method](references/change-safety.md).
These methods preserve existing authority; they grant no new operation.

For authorized service operations, load only the relevant procedure from
[operations methods](references/operations.md) (reliability, delivery, incident
recovery, resilience, toil); ordinary edits owe no operations phase.

## Workflow

1. Read intent, acceptance, scope and repository boundaries before the first
   write; reuse loaded contracts. [RPI boundaries](../rpi/references/boundaries.md)
   apply when RPI is selected; caller-selected episode tracking follows the
   [session association reference](../agent-native/references/session-associations.md#work-to-session-associations).
   Note the revision and files already modified, staged or untracked; report
   only your own as changed, and ask the caller before editing one holding
   others' edits.
2. Carry the accepted behavior examples forward unchanged. Use repository
   domain names in symbols and tests; check observable outcomes through the
   relevant interface. Run the smallest applicable check before and after
   editing. Pure refactors, relocations or docs may have an honest green
   baseline. Prefer existing tests or small discriminating probes.
3. Make the smallest in-scope change. When repairing discovery or checks,
   preserve the consumer's existing input selection; fixing an error path does
   not authorize a wider scan. Use a negative control when exclusion matters.
   Check a representative change against existing constraints before bulk
   propagation, and the authored source set before broad regeneration. A
   scripted edit across files first confirms that each anchor matches exactly
   once; on zero or several matches, write nothing and re-derive it. Repair
   known failures directly and verify the exact result with a check; a repair
   does not start another review. A disproved assumption may change the
   approach within scope; use Plan only for consequential uncertainty.
4. Read the repository's actual check recipe, including instrumentation and
   environment, rather than reconstructing it from memory. Run targeted tests
   and lint/static checks before broad integration, and required full checks at
   integration. Reuse exact-input receipts only while source, tool and relevant
   environment match. Neither bypass required hooks nor replay a check just to
   rename its receipt. A required CI job's known failure is actionable before
   the run ends: repair it within scope, keep the failed subject's evidence and
   rerun affected checks. Pending jobs do not imply success. A new check, hook
   or lint rule counts once the aggregate command or CI runs it (a Git hook needs
   an install path; `.git/hooks` is not cloned) and it fails on a deliberate
   violation; else list it under `gaps` as not wired. Use a local server already
   on a port only if it provably serves this checkout; stop only processes you started.
5. Refactor while acceptance remains green. Inspect changed tests, fixtures,
   goldens, tolerances, suppressions and specification text against original
   intent before handoff. Reread that intent at its source, not a compacted
   summary, and check the whole delta against it, untracked files included.
   Remove leftovers of abandoned approaches, temporary probes (one shared
   marker lets a single search prove none remain) and files your checks made;
   list any path you cannot explain under `gaps` as a scope amendment.
6. Have the runtime derive actual changed paths and content identity. A delegated
   increment awaiting integration returns an exact commit or runtime-derived
   content digests, author context ID and check facts in the existing handoff.
   Copy that ID from the session, subagent or thread ID the runtime exposes, or
   label a caller-supplied one as supplied; otherwise report it as unknown,
   never made up. The integrating caller derives `subject-manifest.v1` (AgentOps
   schema [subject-manifest.v1.schema.json](https://github.com/boshu2/agentops/blob/main/schemas/subject-manifest.v1.schema.json), AgentOps source checkout only) over the complete final
   subject before judgment; an independently judged increment needs its own
   manifest. Do not generate both merely because work was delegated. Where the
   repository records AgentOps evidence bindings, also run
   `ao provenance evidence-orphans --root <repo-root>` with one `--changed <path>`
   per derived path (it is advisory), keep its actual output and refresh
   flagged bindings after repairs; without `ao`, list it under `not run`.
7. Return the handoff below, then stop.

## Handoff

Keep full logs at their source; do not duplicate inventories or status documents.

```text
changed:   <runtime-derived paths>; identity: <commit or content digests>
author:    <runtime session/subagent/thread ID, "ID (supplied)" or "unknown">; when an integrator or fresh read follows
checks:    <exact command> -> <result>, one per line; before and after for a behavioral change
not run:   <check> -> <reason>; "none" only when every relevant check ran
consumers: <file:line> -> <covering check, or "uncovered">
gaps:      <missing or truncated evidence, known failures, scope amendments needed>
cause:     <defect repairs only: trigger -> mechanism -> symptom at file:line; sites left as follow-up>
```

Report an uncovered live consumer for a caller scope amendment and continue
independent authorized work. Disclose a reversible implementation choice only
when its alternative has a material consequence the caller may want to change;
name the choice, alternative and reason in the handoff, without a fixed worksheet.
Generated companions already included as scope require no new approval; a change
to accepted direction, behavior or acceptance always needs caller authority.

## Diagnosis, scaffolding and delegated work

For an unexplained failure, follow the [diagnosis loop](references/difficult-failures.md#diagnosis-loop)
before repairing: confirm the failing run executes the code you think, ground
the leading cause in an observation, name its strongest rival and test one
prediction the two disagree on. The same file holds the experiments for races,
leaked state, hangs, regressions and failures that cross components.

When scaffolding is the requested change, start from the repository's existing
layout (or the ecosystem's standard one for a new project) and one working
vertical slice; avoid placeholder success paths and a new framework for a
one-off operation. For installers, agent-facing tool servers or a Rust CLI with
local state, see [agent-facing tool scaffolds](references/scaffold/agent-facing-tool-scaffolds.md).

Prefer current-session execution. If delegation is authorized and useful, keep
concurrent writers disjoint and isolated as [Agent Native](../agent-native/SKILL.md)
describes; shared generators and integration serialize. Supply each lane its
intent, acceptance, scope and review owner, then integrate its exact content and
check facts. A selected wave ends with the caller-requested wave result; do not
invent another wave. One fresh review of the integrated candidate can cover
unjudged increments; when the integrator owns that review, workers return their
handoff without commissioning another. Preserve any separately required lane
judgments; a successful process exit is not semantic PASS.

An explicitly requested one-shot adapter dispatches each supplied operation
once, reports its output or error and stops, with no scheduler, retry controller
or store; show its dispatch count and failure reporting with a dry-run or
fixture. Factories require the caller's selection.

## Finish

Specialists advise only; known defects stay implementation work. A genuine
causal stall admits one bounded fresh helper under RPI's
[stall rule](../rpi/SKILL.md#causal-stall-and-bounds); retries renew no bound.

Return facts, not semantic PASS. An implement-only handoff does not authorize
Git, tracker or delivery transitions; existing caller authority remains usable.
A full outcome request finishes on its checks and CI; it continues to one fresh
independent judgment only on [Validate's triggers](../validate/SKILL.md#when-a-fresh-judgment-is-worth-it).
Success is working behavior with usable evidence, not volume of logs or process
artifacts.
