---
name: implement
description: 'Implement accepted behavior, repair defects or execute a selected wave with per-lane evidence. Use when: coding is authorized and ready; return facts, not a binding verdict.'
---
# Implement

Implement the accepted outcome. Repair ordinary known defects directly. Use the existing
intent; no Plan, Recall or Learn worksheet is owed for a clear edit. Implement
owns source changes and factual checks; the runtime derives identity and receipts.

## Workflow

1. Read intent, acceptance, scope and the RPI [boundaries](../rpi/references/boundaries.md)
   before the first write; reuse contracts already loaded in this context.
   When the caller selected episode tracking, obtain permitted work/source
   references before execution and return observed runtime/context identity at
   startup through the native recording channel. Unknowns and recording failures
   stay explicit; do not invent parentage or a second tracker. The optional
   [session association reference](../cass/references/SESSION_FORMATS.md#work-to-session-associations)
   supplies mechanics for that selected workflow.
2. Carry the accepted behavior examples forward unchanged. Use repository
   domain names in symbols and tests; check observable outcomes through the
   relevant interface. Find nearby validation scripts and tests that consume the edited paths or
   contract wording. Keep their exact commands and the required integration
   recipe in one short check list in the existing handoff; reuse it, updating
   only when inputs or scope change. Run the smallest applicable check before
   editing and after the change. Behavioral changes preserve RED for
   the expected missing behavior; a pure refactor, relocation or documentation
   change may have an honest green baseline. Avoid building elaborate fixtures
   when an existing test or small discriminating probe answers the question.
3. Make the smallest in-scope change. When repairing discovery or checks,
   preserve the consumer's existing input selection; fixing an error path does
   not authorize a wider scan. Use a negative control when exclusion matters.
   Fix known failures directly and rerun the affected check. A disproved
   assumption may change the approach within accepted scope; use Plan only
   for consequential uncertainty.
4. Use targeted tests and applicable repository lint/static checks before
   broad integration. Read the repository's actual check recipe, including
   instrumentation and environment, rather than reconstructing it from memory.
   Run required full checks at integration, not after each small edit. Reuse
   exact-input receipts only while source, tool and relevant environment match.
   Distinguish repository-mandated hook checks from discretionary repeats;
   neither bypass required hooks nor replay a check just to rename its receipt.
5. Refactor while acceptance remains green. Inspect changed tests, fixtures,
   goldens, tolerances, suppressions and specification text against original
   intent. Mocks, placeholders or weakened oracles cannot substitute for the
   requested behavior.
6. Have the runtime derive actual changed paths and content identity. A delegated
   increment awaiting integration returns an exact commit or runtime-derived
   content digests, author context ID and check facts in the existing handoff.
   The integrating caller derives `subject-manifest.v1` over the complete final
   subject before judgment; an independently judged increment needs its own
   manifest. Do not generate both merely because work was delegated.
   At that boundary, when changed paths affect bound acceptance evidence, run
   `ao provenance evidence-orphans --root <repo-root>` with one `--changed
   <path>` per derived path and retain its actual output. Refresh affected
   bindings after repairs; never invent or suppress the orphan list.
7. Return identity, check commands/results, useful failures and accessible
   evidence references through the native handoff, then stop. Full logs stay
   at their source; do not copy them into another inventory or status document.
   Missing or truncated evidence stays explicit.

## Diagnosis, scaffolding and delegated work

For an unexplained failure, first match the reported symptom and reduce the
reproduction. State one causal prediction, test it with a discriminating check,
and repair the cause supported by the result. Rerun the original scenario.
Do not keep collecting hypotheses after the cause is understood. This compact
diagnosis path is informed by
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills).

When scaffolding is the requested change, start from the repository's existing
layout and a working vertical slice. See [scaffold references](references/scaffold/agent-facing-tool-scaffolds.md)
only for the relevant tool shape. Avoid placeholder success paths and a new
framework for a one-off operation.

Prefer current-session execution. If delegation is authorized and useful,
partition independent writes in isolated workspaces; shared generators and
integration serialize. Supply each lane its intent, acceptance and scope, then
integrate its exact content and check facts. A selected wave ends with the
caller-requested wave result; do not invent another wave. One fresh review of
the integrated candidate can cover unjudged increments. Preserve any separately
required lane judgments; a successful process exit is not semantic PASS.
[Agent Native](../agent-native/SKILL.md) supplies optional dispatch mechanics.

An explicitly requested one-shot adapter dispatches each supplied operation
once, reports its output or error, and stops. Show dispatch count and failure
reporting with a dry-run or fixture. It does not silently acquire a scheduler,
retry controller or store. Factories require the caller's selection.

## Scope and finish

Report an uncovered live consumer as `file:line` for a caller scope amendment;
continue independent authorized work. Generated companions already included as
scope require no new approval. Acceptance changes always require caller authority.

Specialists advise only. Known defects stay implementation work; a genuine
causal stall follows RPI's at-most-one bounded helper rule. Respect remaining
caller/native bounds and reserve finishing capacity. No retry resets them.

Return facts, not semantic PASS. An implement-only handoff does not authorize
Git, tracker or delivery transitions; existing caller authority remains usable.
A full outcome request uses RPI through fresh final judgment. Success is working
behavior with usable evidence, not volume of logs or process artifacts.

[Generic scaffold examples](references/scaffold/generic-templates.md) are
optional starting points when the repository has no suitable existing pattern.
