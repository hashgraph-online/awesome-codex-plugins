# Elicitation Contract — Bounded User Interview

Plugin runtime asset. Loaded by every command skill (`init`, `plan`, `document`,
`review`) before any gate that may question the user. Normative for every command
and every track gate (`sdd`, `requirements-cascade`, `decision`, `describe`,
`actualize`, `experience`). This contract defines when to ask, how many questions,
in what form, and where answers persist. It does not define which questions a gate
asks — see Ownership.

## When to interview

Consider an interview only when at least one trigger signal is present:

- the command arguments are absent or vague;
- a coverage scan returns `Missing` on a material category;
- two or more viable alternatives exist on one decision;
- the code and a document conflict.

Apply the materiality filter to every candidate question: keep it only when it
concerns architecture, data model, task decomposition, tests, UX behavior,
operations, or compliance. Drop every candidate that fails the filter. The
coverage scan behind the `Missing` trigger uses the categories in
`skills/_shared/coverage-taxonomy.md`; the materiality filter is this
seven-area list, not that taxonomy.

If no candidate passes the filter, skip the interview and state that no material
ambiguity was found.

## Ground first

Before asking any question — on every host, at every gate — attempt to answer it
yourself from:

- `.archcore/` search (`search_documents`, `list_documents`);
- the codebase;
- git history;
- clarifications already recorded in this invocation or the draft artifact.

Ask only what grounding could not resolve.

## Question form

Compose every question with these parts, in this order:

1. one interrogative sentence;
2. a one-line "why it matters";
3. a recommended option, stated first;
4. 2–4 options, plus a free-answer choice, plus "you decide".

You MUST NOT ask a question without a stated recommendation.

## Budget

- Auto mode: hard ceiling of 5 questions per invocation, drawn down across all
  gates of that invocation. You MUST NOT exceed the ceiling regardless of how
  many gates run.
- Expert invocation: per-gate budgets rise up to the maximum the track file
  declares.
- A re-asked disambiguation (see Failure handling) does not count against the
  budget.
- When candidate questions exceed the remaining budget, rank them by
  impact × uncertainty and ask only the top ones within budget.

## Delivery — widget versus prose

The widget-versus-prose switch lives only in this contract; a skill file
MUST NOT contain host-conditional text.

- If the host offers no question widget, present exactly one question per message.
- If the host offers a question widget, you MAY batch up to 4 related questions
  in one call.

## Who may ask

- A subagent MUST NOT conduct an interview.
- A hook MUST NOT ask the user a question. A hook MAY inject a notice of
  unresolved assumptions.

## Delegation

- If the user answers "you decide" or "I don't know", adopt the recommended
  answer and mark it `[assumption]` in the artifact.
- If the user delegates twice in a row, end the interview and finish the work on
  recorded assumptions.

## Write-back

- If the draft artifact does not exist, create it with `create_document` before
  writing clarifications.
- When a gate closes, write the accepted answers under `## Clarifications` in
  the draft artifact, within the single `update_document` call required by
  `skills/_shared/gate-contract.md`.
- When the budget is exhausted while material questions remain, record the
  remaining questions in the `deferred` field of the track state block with a
  one-line reason each.
- Update the track state block per `skills/_shared/gate-contract.md`.

## Failure handling

- If the user interrupts the interview, proceed on the answers recorded so far
  and mark unresolved material items `[assumption]`.
- If the user rejects the recommended answer without giving an alternative,
  re-ask once with the option list. This re-ask is the re-asked disambiguation
  exempt from the budget.

## Ownership

- Per-gate question lists: the track file `skills/_shared/tracks/<track-id>.md`,
  with gate records per `skills/_shared/gate-contract.md`.
- Coverage categories behind the coverage-scan trigger:
  `skills/_shared/coverage-taxonomy.md`.

Read the owning file; do not restate its content here or in a skill file.
