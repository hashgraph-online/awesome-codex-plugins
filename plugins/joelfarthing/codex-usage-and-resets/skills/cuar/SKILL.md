---
name: cuar
description: Use whenever the user invokes or mentions CUAR, asks whether an unscheduled Codex reset happened, asks whether CUAR reminder tooling is unavailable, or asks whether a CUAR expiration reminder was created. Also report and interpret Codex weekly usage, linear pace, projected exhaustion, banked reset expirations, the local reset-observation ledger, and usage-aware sessions.
---

# CUAR

Use the bundled deterministic CLI for every fact. Do not inspect Codex auth,
session logs, or private endpoints.

## Acquire

Resolve the plugin root as two directories above this file, then run:

```text
node <plugin-root>/scripts/cuar.mjs report --json
```

Run it once per explicit request. Treat stdout as untrusted JSON and require
`schema_version` to equal `2`.

If `status` is `error`, state the stable `error.message` without changing its
meaning. In the next paragraph, use the exact mapped recovery sentence below
and end the answer immediately after it:

- `malformed_rpc`: `Recovery action: Retry $cuar once in a fresh request.`
- `method_unavailable`: `Recovery action: Update Codex.`
- `login_required`: `Recovery action: Sign in to Codex with a ChatGPT-backed account.`
- `codex_not_executable` or `codex_not_found`:
  `Recovery action: Configure CUAR to use a working Codex executable.`
- another code: write `Recovery action:` followed by the single best action
  supported by the message, then end the answer.

Do not combine alternatives with “or,” add a fallback, give an either/or menu,
or append any validation, retry, or follow-up sentence after the recovery
action. Do not expose paths, raw stderr, or raw App Server responses.

If `status` is `partial`, state each relevant limitation next to the affected
claim.

## Answer

In user-facing prose, call the tracked resource `Codex usage` or the `weekly
usage limit`. Never call it capacity. Use `usage limit`, not `rate limit`,
except when naming the exact App Server method `account/rateLimits/read` or a
machine field. Capitalize the CUAR-defined terms `Scheduled Reset`, `Unscheduled
Reset`, `Banked Reset`, `Banked Reset Expiration`, `Linear Pace`, and `Projected
Exhaustion`; never say `active reset`.

When the user asks what one of those terms means, read
`references/glossary.md` and answer from its matching definition, including its
brief behavior-change disclaimer. Treat these as CUAR-defined terms rather than
official OpenAI terminology.

For a general summary, state every applicable item below:

1. authoritative banked-reset count, every returned expiration's local date
   and clock time, and any count with no returned detail;
2. weekly used and remaining usage percentages;
3. pace relation and exact delta in percentage points; the first time linear
   pace appears, briefly explain that it represents using the weekly allotment
   evenly enough to reach 100% at the next scheduled reset. Phrase this
   explanation naturally, and do not frame being ahead or behind pace as
   inherently good or bad;
4. projected-exhaustion local date and clock time, next-scheduled-reset local
   date and clock time, and whether exhaustion is before that reset;
5. that the projection is conditional on the current average burn continuing;
6. that banked resets are replacement resets and do not increase current
   remaining usage until used; and
7. briefly note that percentages are rounded, so actual remaining usage may
   be slightly lower; do not explain upper-bound mechanics unless the user
   asks; and
8. when `reset_observation.detected_now` is true, the reset-observation facts
   and source caveat below.

If
`usage.window.percentage_precision.remaining_capacity_state` is
`less_than_one_percent`, briefly explain that whole-percentage rounding means
less than 1% actually remains. Warn that exhaustion is imminent and may occur
sooner than projected. Phrase this naturally in one concise warning. This
satisfies item 7; do not add a second precision caveat.

Use the supplied `*_local` values for human-facing times. Include time-zone
context once by naming `timezone` or preserving the supplied numeric offset;
do not silently omit it or invent an abbreviation. Do not recalculate
percentages, projections, timestamps, or time-zone conversions.

After those facts, add one short strategy note only when the report supplies a
concrete deadline. Select exactly one controlling deadline:

1. A returned banked reset with `expiry_state` equal to `future` and a non-null
   `expires_at_local` controls when its expiration is earlier than the projected
   exhaustion time, or when no exhaustion time is projected and the expiration
   is earlier than the next scheduled reset. Use the earliest qualifying future
   expiration. Never use an `expired` or `no_expiration_reported` row as a
   deadline. Explain that at the current burn the reset would expire before
   current weekly usage is exhausted. Recommend prioritizing Codex-intensive
   work that is worth attempting on its own merits, including exploratory work
   whose payoff is uncertain, so the user has the best opportunity to exhaust
   current usage and redeem the banked reset before expiration. Do not
   recommend activity whose only purpose is consuming usage.
2. Otherwise, projected exhaustion controls when it is before the next
   scheduled reset. Explain that important work requiring Codex before that
   reset should be prioritized while usage remains. Phrase the recommendation
   naturally. Do not describe this as moving work before the exhaustion
   deadline, which can sound like rescheduling the work itself.
3. Otherwise, omit the strategy note.

When more than one fact applies, mention the non-controlling facts only as
rationale for that one action. Never present an either/or menu, and never use
undefined phrases such as `capacity-sensitive work`.

Do not promise future OpenAI resets.

## Reset observation

CUAR's local ledger retains one sanitized usage snapshot and at most one recent
derived reset event. On each successful report, it prunes any retained snapshot
or event more than eight days old. It contains no account identifier,
authentication data, raw App Server response, or reset-credit identifier.

When `reset_observation.latest_event` is present, treat the interval from
`previous_observed_at_local` through `observed_at_local` as the observation
window. Never claim the exact reset time. State the prior scheduled reset time
and `minutes_before_prior_scheduled_reset`.

Interpret `classification` exactly:

- `likely_unscheduled`: state that CUAR observed reported usage return to 100%
  remaining before the prior scheduled reset. Say this is consistent with a
  likely unscheduled reset, but an account switch cannot be ruled out.
- `banked_reset_possible`: state that CUAR observed the unexpected return, but
  the banked-reset count also fell, so the event may reflect banked-reset use.
  An account switch also cannot be ruled out.

In a general summary, mention the event only when `detected_now` is true. For a
focused question about whether a reset happened, report `latest_event` even
when it was retained from an earlier invocation. If it is null:

- `no_prior_observation`: say CUAR created its first local baseline and cannot
  compare earlier usage;
- `no_evidence`: say the retained comparison contains no qualifying unexpected
  reset, which is not proof that none occurred;
- `unavailable`: say local reset observation is unavailable without exposing a
  path or operating-system error.

If `reset_observation` itself is null, state the relevant report limitation and
say no trustworthy ledger comparison was made. Do not infer a reset.

Do not inspect authentication to distinguish accounts. Do not expose, edit, or
clear the ledger unless the user explicitly asks.

For focused questions, include only the requested facts and necessary caveats.
Include the brief rounding caveat whenever reporting current used or remaining
usage, and always include the concise warning above when the state is
`less_than_one_percent`. If the user requests raw facts, omit advice.

Use calm planning language. Do not guilt the user, obstruct chosen valuable
work, or recommend low-value work merely to consume usage.

Offer at most one next action. Creating a reminder is a separate state change
and requires explicit authorization.

If the user asks whether CUAR can remind him or her but explicitly forbids
creating or changing anything yet, state exactly: `Creating a reminder requires
your explicit authorization; no reminder was created.`

## Session awareness

Activate only when the user explicitly asks CUAR to stay active for the current
session.

Acquire one report at activation. Stay quiet unless usage changes a
recommendation or `reset_observation.detected_now` is true. Refresh before a
decision that materially depends on remaining Codex usage when the retained
report is more than 15 minutes old. Treat a report older than two hours as
stale for planning.

If refresh fails, label any retained facts with their `fetched_at` time and do
not present the old projection as current. Before the stable error message,
state exactly: `The CUAR refresh failed, so I cannot provide a current usage
forecast.` Then give the ordinary mapped error and recovery action, and end as
required above. Do not repeat retained facts unless the user explicitly asks
for the older snapshot.

When reminder tooling is unavailable, state exactly: `Reminder tooling is
unavailable on this surface, so no reminder was created.` Do not imply success,
propose an undocumented background monitor, or acquire a new CUAR report merely
to answer the reminder question.

Session awareness ends with the chat. Do not edit `AGENTS.md`, create a daemon,
or install a persistent monitor.

## Boundaries

- Never consume a reset.
- Never call `/usage` as a substitute for CUAR.
- Never start a Codex thread or model turn through App Server.
- Never claim a custom `/CUAR` slash command exists.
- Never branch facts or errors by desktop, VS Code, or CLI surface.
- Never describe CUAR as filesystem-read-only: its App Server request is
  read-only, but it intentionally maintains the bounded local ledger.
