---
name: status
description: Report observable AgentOps evidence without
---
# Status

A status snapshot is trustworthy exactly when every line traces to an artifact
that exists on disk right now; the first inferred line turns the report into a
guess wearing a report's clothes.

Report only observable local facts: available intent, subject-manifest, and
verdict artifacts; their counts, digests, and timestamps; deterministic check
results; and unavailable or corrupt sources. The canonical durable stores are
`.agents/ao/intents/sha256` and `.agents/ao/verdicts/sha256`; subject manifests
remain caller-supplied unless the caller names their location. When `.agents/ao`
evidence exists, report which stored artifact kind is newest and label that
conclusion as evidence recency, not runtime phase or process activity.

Always disclose `checked` and `not_checked`. Runtime phase, execution elapsed
time, tool-call activity, and remaining work are `not_checked` unless a caller
provides a separate authoritative source for them.

`ao status` is the evidence-store view. It validates content-addressed artifact
names and content before counting them, reports corrupt and unavailable entries,
and shows only intent/verdict counts plus evidence recency. Legacy session
indexes, provenance summaries, flywheel health, and quality signals belong to
their own read surfaces and are not aggregated into this command.

Status does not inspect work queues, assign priority, claim work, infer a next
action, repair records, govern retries, or change any state. Optional Git or
tracker metadata may be displayed only when the caller supplies it; absence
cannot change the report interpretation.

Named failure mode — **recency-as-activity**: reading "newest artifact is a
verdict" as "validation is running", which invents a runtime phase from a
timestamp.

Anti-pattern: filling `not_checked` gaps with plausible narrative so the
snapshot feels complete. Corrective: report the gap as a gap; an honest hole
outranks a smooth story.

Return the snapshot and stop.
