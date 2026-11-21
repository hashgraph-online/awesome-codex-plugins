# Suede AI Marketing Loop Skills: Worked Contract

This is a synthetic application scenario, not a client result or a required output filename. Adapt the values to the supplied evidence. The skill's existing output format and authority boundaries apply.

## Input

A team wants a weekly ranking review for ten owned pages. Search data is supplied as dated exports, the marketing owner reviews proposed changes, and scheduling has not been authorized.

## Expected output

Return the nine anatomy fields: Check cadence (weekly); Acts when (a page crosses the agreed ranking-change condition); Purpose (protect relevant visibility); Skills used (the audit or content skill needed for the draft); Loop body (read the dated export, compare, draft, and stage for review); Self-check (fresh export and sufficient observations); State / idempotency (page/date/condition dedupe key and durable state path); Stop / bail-out (missing data, repeated error, or manual disable); Output (a reviewable draft with a named human checkpoint). Supply a copyable manual cadence and say nothing was scheduled.

## Missing input and recovery

If this week's export is missing, record a skipped review and the missing date; do not infer a ranking change. If a scheduler is unavailable, retain the loop body and manual cadence. A later scheduling request must produce the scheduler's confirmation rather than an invented job id.

## Validation

Replay the same export twice: only one draft action should exist for the same page/date/condition. Test the kill switch and insufficient-data case. Compare any created schedule with its confirmed next run time and the user's timezone.

## Detailed scope and routing

Suede AI recurring marketing workflow design: turns repeatable work into agent-ready loops with a check cadence, action condition, self-check, durable state and dedupe, human checkpoint, stop condition, and output, drawn from a 46-loop catalog across SEO and AI-search visibility, paid, earned, activation, retention, revenue, referral, and ops. Returns a complete loop spec plus scheduling proof or a manual cadence. Use when the user wants repeatable ad-fatigue, content-refresh, ranking-drop, AI-citation watch, churn-watch, or weekly-review loops, or wants agents to run marketing operations on a schedule. NOT FOR: one-off tactics or plans (use suede-marketing-plan), experiment design (use suede-ab-testing), or creating a live automation without explicit scheduling authority.
