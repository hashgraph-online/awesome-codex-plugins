---
name: plan
description: 'Define intended behavior, review write scope and assess reversible decisions. Use when: discovery needs clarification or resumption before one complete slice; stop once actionable.'
---
# Plan

Own discovery from the caller's question to one actionable slice. Shape only
missing intent. Prefer the caller's tracker, if any; otherwise use
the conversation or supplied text. Planning produces no AgentOps packet.
A clear change can proceed directly. Use established domain names throughout
intent, examples, code and validation. Load a specialist only for the question
it can answer; none is a required planning stage.

## Workflow

1. Read accepted intent, the compact existing plan or native handoff, and the
   relevant source owners and active constraints. On replacement or resumption,
   use [Resume discovery](#resume-discovery) before choosing a next action.
   Identify the caller-visible outcome and classify only uncertainty that could
   change the next slice using [Route uncertainty](#route-uncertainty).
2. Describe the intended observable behavior before implementation. Reuse
   acceptance already supplied in the conversation or bead; clarify only what
   prevents action or judgment. Name the actor or caller, the event and the
   observable result. One example often suffices; use Given/When/Then for
   branching behavior and consequential boundaries. Include non-goals only
   where they prevent a plausible scope mistake in that existing source.
   If the caller requests both code and a retrospective, distinguish code
   acceptance, delivery facts and the later analysis in that same intent.
   Code judgment consumes acceptance and checks; the retrospective consumes
   the known outcome and judgment. Keep both requested deliverables required
   for the overall goal without making either depend on its own conclusion.
   Scope includes the hand-edited owners, affected tests/live consumers and
   generator-owned companions as a class; it is authority, not a predicted
   file count. A consequential assumption deserves an early discriminating
   check, not a general checklist or exhaustive survey.
3. Refine one narrow but complete vertical slice, including its affected layers,
   live consumers and useful check. It must produce an independently observable
   result, not just a schema, interface or plan for another layer. Keep later
   work coarse in the existing intent; sharpen it only when new evidence makes
   the next slice actionable. For a mechanical cross-cutting migration that
   cannot stay working slice by slice, preserve compatibility with an
   expand/migrate/contract approach and state where integration is required.
   Include recapture of affected bound evidence where necessary; use
   `ao provenance evidence-orphans` when applicable, not a mandatory ledger.
4. When evidence disproves an approach, briefly retain the failed assumption,
   evidence and revised check in the existing intent or handoff. Approach
   changes within accepted outcome and scope need no new permission; acceptance
   or scope expansion requires caller authority. Never relabel a failed
   acceptance condition as a caveat to obtain green.
5. Give another context exact intent references and the evidence it needs to
   act, its write scope and who owns integration and final review. Keep approach
   notes separate from frozen acceptance. Pass the next decision and relevant
   source references, not the entire research history. A new goal does not
   clear an existing conversation, and a fresh context can still have large
   startup instructions, tool catalogs and retrieved inputs.

Stop planning once the implementer can act and the validator can judge. More
research, decomposition or review must resolve a named remaining uncertainty.
An optional [probe or prototype](references/ground-truth-routing.md) can test a
named assumption. An optional [challenge](references/challenge.md) can examine
consequential uncertainty that survives source checks and relevant observations.
[Memory recall](../memory/references/recall.md) is useful only when
prior evidence could change the next action.

## Route uncertainty

Keep these distinctions in the existing intent only where they affect action;
they are not four required worksheets or successive stages.

| Uncertainty | Next action |
|---|---|
| Source-answerable fact | Inspect the smallest authoritative source and cite it. [Research](../research/SKILL.md) owns deeper tracing and evidence synthesis; [Domain](../domain/SKILL.md) owns ambiguous vocabulary and rule boundaries. Do not ask the caller to recite a retrievable fact. |
| Consequential caller choice | Recover existing authorization first. Ask one focused question only when goal, behavior, preference or authority still needs the caller. Include the concrete tradeoff; an agent cannot supply the caller's answer. |
| Assumption requiring a probe | State the competing predictions and smallest observation that distinguishes them. Use the optional probe method; a persuasive design or agent vote cannot settle unobserved behavior. |
| Safely deferred decision | State why it does not block this slice and the event or evidence that would make it relevant. Keep it coarse; deferral cannot hide an unanswered acceptance condition. |

Resolve reversible implementation details within accepted scope. Mark inference
and missing evidence explicitly; do not promote either into a source fact or a
settled caller choice. An optional challenge returns advice or a next
discriminator, never permission or acceptance.

## Resume discovery

Recover the current outcome, accepted examples and source identity from the
existing plan or native handoff. Reuse settled domain terms and caller choices
with their source pointers; do not repeat an interview or load the full transcript.
Read details on demand only if a missing fact or new contradiction can change
the next decision.
Before reusing inherited prototype evidence, follow
[Reuse after source drift](references/ground-truth-routing.md#reuse-after-source-drift).

Check active assignments, write scopes and integration/review ownership against
the native tracker or runtime before suggesting more work. Handoff facts are
recovery pointers, not a second authoritative assignment or status ledger. If
the native source is unavailable or contradicts the handoff, report that gap
and resolve it before dependent dispatch or overlapping writes; independently
safe discovery can continue.

Leave a compact update in that same source when interruption or replacement
would otherwise lose a decision: accepted outcome/reference; settled choices
and evidence; active assignment references and scopes; the one open question
and next discriminator; deferred decisions and their revisit triggers. Include
known failed assumptions and relevant contrary evidence. An unchanged recovery
needs no duplicate artifact. Preserve native ownership and original evidence;
new observations amend the approach within scope, while changed acceptance
still needs the caller.

## Behavior and naming

An example can be plain text; BDD does not require a `.feature` file or an
interview. For example, in a repository that calls queued work a **Job**:

> Given a Job has already completed, when the worker receives it again,
> then its completed result is returned and its side effect is not repeated.

Use the actual domain term instead of inventing a parallel label such as
"task item." Identify what the caller can observe and the smallest check that
distinguishes the desired behavior from the current failure. Keep the accepted
example available to Implement and Validate. Tests added after coding may
supplement it; they cannot redefine what was promised.

For uncertain designs, probe the assumption that could change the approach.
For product planning, distinguish demonstrated behavior from aspiration and
refine the existing product owner only within the request. A product document
is not required for an ordinary feature.

## Decision cost and stopping

Use real undo cost, affected users and existing authority when choosing who
must decide. Resolve reversible implementation details within accepted scope.
A material irreversible choice outside that authority needs the caller; prior
authorization remains valid. Reviewer agreement is evidence, not permission
to replace the caller's intent. Explain a consequential disagreement and its
support rather than silently changing acceptance.

A proposed process artifact earns its cost only with a concrete consumer,
subject or release decision, observed defect and retirement condition. If the
next action adds only ceremony or repeats settled evidence, omit it. Stop when
the implementer can act and the validator can judge, reserving capacity for
implementation, integration and repair.

Decision pointers and coarse future work adapt ideas from Matt Pocock's
[Wayfinder](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md);
complete slices and compatibility migrations adapt
[To Tickets](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-tickets/SKILL.md).
AgentOps keeps the caller's existing intent and native work authority.

## Identity and scope

Use runtime-derived source identity and digest. If conversation intent needs
an exact snapshot, existing `ao provenance snapshot-intent --source -
--evidence-root <explicit-root>` uses caller-selected protected external
non-Git storage. Missing routing permits neither workspace fallback nor a
second planning artifact. Preserve legacy proof.

Use normalized repository-relative scope patterns. An uncovered live consumer
needs a concise exact-file amendment to the caller; continue independent
in-scope work meanwhile. Generated companions already in scope need no extra
permission. [Boundaries](../rpi/references/boundaries.md) keep work/status in
the caller's tracker and delivery under repository policy.
