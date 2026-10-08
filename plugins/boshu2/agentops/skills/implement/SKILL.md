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
  triggers: ["execute the next wave", "per-lane evidence"]
---

# Implement

Implement the accepted outcome. Repair ordinary known defects directly. Use the existing
intent; no Plan, Recall or Learn worksheet is owed for a clear edit. Implement
owns source changes and factual checks; the runtime derives identity and receipts.

## Rules that decide the result

- **Fix the cause, not the oracle.** Never loosen an assertion, tolerance,
  golden, fixture or suppression, or substitute a mock or placeholder, to turn
  a check green. A check that fails against accepted behavior points at a
  product defect; changing what the check accepts is an acceptance change and
  needs caller authority.
- **Find live consumers before editing.** Search the callers, readers, scripts,
  docs and tests of every edited function, type, path, format or message. For
  each one, state whether the change affects it and which check covers it. When
  retiring or renaming, consumers include installations, lookups and old-name
  invocations; preserve historical provenance.
- **Name discriminating checks.** A behavioral change preserves RED
  for the expected missing behavior: name the check that fails before the edit
  and passes after, plus the check for each affected consumer.
- **Report only what ran.** Give exact commands and results. List every check
  you did not or could not run as not run. Never call unrun work verified,
  fixed or green.

For authorized service operations, load only the relevant procedure from
[operations methods](references/operations.md) (reliability, delivery, incident
recovery, resilience, toil); ordinary edits owe no operations phase.

## Workflow

1. Read intent, acceptance, scope and repository boundaries before the first
   write; reuse loaded contracts. RPI [boundaries](../rpi/references/boundaries.md)
   apply when that workflow is explicitly selected. Caller-selected episode
   tracking follows the [session association reference](../agent-native/references/session-associations.md#work-to-session-associations);
   keep unknowns explicit and invent no parentage or second tracker.
2. Carry the accepted behavior examples forward unchanged. Use repository
   domain names in symbols and tests; check observable outcomes through the
   relevant interface. Run the smallest applicable check before and after
   editing. Pure refactors, relocations or docs may have an honest green
   baseline. Prefer existing tests or small discriminating probes.
3. Make the smallest in-scope change. When repairing discovery or checks,
   preserve the consumer's existing input selection; fixing an error path does
   not authorize a wider scan. Use a negative control when exclusion matters.
   Check a representative change against existing constraints before bulk
   propagation, and the authored source set before broad regeneration. Repair
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
   rerun affected checks. Pending jobs do not imply success.
5. Refactor while acceptance remains green. Inspect changed tests, fixtures,
   goldens, tolerances, suppressions and specification text against original
   intent before handoff.
6. Have the runtime derive actual changed paths and content identity. A delegated
   increment awaiting integration returns an exact commit or runtime-derived
   content digests, author context ID and check facts in the existing handoff.
   The integrating caller derives `subject-manifest.v1` (AgentOps schema
   `schemas/subject-manifest.v1.schema.json`) over the complete final subject
   before judgment; an independently judged increment needs its own manifest.
   Do not generate both merely because work was delegated.
7. At that boundary, when the repository records AgentOps evidence bindings
   and changed paths affect bound acceptance evidence, run
   `ao provenance evidence-orphans --root <repo-root>` with one `--changed
   <path>` per derived path, retain its actual output and refresh affected
   bindings after repairs. Without `ao`, list the orphan scan under `not run`.
   Never invent or suppress the orphan list.
8. Return the handoff below, then stop.

## Handoff

Keep full logs at their source; do not duplicate inventories or status documents.

```text
changed:   <runtime-derived paths>; identity: <commit or content digests>
checks:    <exact command> -> <result>, one per line; before and after for a behavioral change
not run:   <check> -> <reason>; "none" only when every relevant check ran
consumers: <file:line> -> <covering check, or "uncovered">
gaps:      <missing or truncated evidence, known failures, scope amendments needed>
```

Report an uncovered live consumer for a caller scope amendment and continue
independent authorized work. Generated companions already included as scope
require no new approval. Acceptance changes always require caller authority.

## Diagnosis, scaffolding and delegated work

For an unexplained failure, first match the reported symptom and reduce the
reproduction. State one causal prediction, test it with a discriminating check,
and repair the cause supported by the result. Rerun the original scenario.
Do not keep collecting hypotheses after the cause is understood. This compact
diagnosis path is informed by
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills).

When scaffolding is the requested change, start from the repository's existing
layout and a working vertical slice. See [scaffold references](references/scaffold/agent-facing-tool-scaffolds.md)
only for the relevant tool shape, and [generic scaffold examples](references/scaffold/generic-templates.md)
when the repository has no suitable pattern. Avoid placeholder success paths and
a new framework for a one-off operation.

Prefer current-session execution. If delegation is authorized and useful,
partition independent writes in isolated workspaces; shared generators and
integration serialize. Supply each lane its intent, acceptance, scope and review
owner, then integrate its exact content and check facts. A selected wave ends with the
caller-requested wave result; do not invent another wave. One fresh review of
the integrated candidate can cover unjudged increments; when the integrator
owns that review, workers return their handoff without commissioning another.
Preserve any separately required lane judgments; a successful process exit is
not semantic PASS.
[Agent Native](../agent-native/SKILL.md) supplies optional dispatch mechanics.

An explicitly requested one-shot adapter dispatches each supplied operation
once, reports its output or error, and stops. Show dispatch count and failure
reporting with a dry-run or fixture. It does not silently acquire a scheduler,
retry controller or store. Factories require the caller's selection.

## Finish

Specialists advise only. Known defects stay implementation work; a genuine
causal stall permits at most one bounded fresh helper within caller authority.
Respect remaining caller/native bounds and reserve finishing capacity; retries reset neither.

Return facts, not semantic PASS. An implement-only handoff does not authorize
Git, tracker or delivery transitions; existing caller authority remains usable.
A full outcome request finishes on its checks and CI. It continues to one fresh
independent judgment only when the caller asks, a mistake cannot be cheaply
undone after it lands, or no deterministic check covers the changed behavior.
RPI is optional and explicitly selected. Success is working behavior with usable
evidence, not volume of logs or process artifacts.
