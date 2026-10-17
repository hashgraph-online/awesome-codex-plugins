---
name: wakewire-inspect
description: Triage wakewire delivery problems — events not arriving, failed or held deliveries, duplicates, rate-limit digests. Use when the user asks why an expected event didn't show up in a thread, or wakewire tools report failures.
---

You are debugging wakewire deliveries. Work the pipeline in order: source → route → queue → sink.

## 1. Daemon and sources

`wakewire_status` shows queue depth, adapter reachability, and per-source counters (`received`, `rejected`, `connected`, `lastEventAt`, `lastError`).

- Source `rejected` climbing → webhook signature failures. The secret in GitHub and the one stored at setup time don't match; re-run `wakewire_source_setup_github`.
- Gmail `connected: false` with `lastError` → OAuth expired or label missing; re-run `wakewire auth gmail`, check the label exists.
- `adapter.codexReachable: false` → the daemon can't spawn/reach codex; deliveries will sit in `held` and retry automatically.

## 2. Deliveries

`wakewire_deliveries` (filter with `{status: "failed"}`, `{routeId: ...}`, `{limit: ...}`). Status meanings:

- `queued` / `delivering` — in progress.
- `delivered` — done; `threadId`/`turnId` say where it went.
- `held` — retrying with backoff (Codex app closed, thread busy, network). `error` has the reason, `nextAttemptAt` the next try. This self-heals; nothing to fix unless it persists.
- `failed` — permanent (bad template field, deleted thread/route, or max retries). Read `error`.
- `skipped-duplicate` — same source delivery id seen before (webhook redelivery). Expected, not a bug.
- `coalesced` — folded into a digest turn because the route exceeded its rate limit; `coalescedInto` points at the digest delivery.

The `renderedPrompt` field shows exactly what was (or would be) injected — use it to debug template issues.

## 3. Common causes of "event never arrived"

1. Event didn't match the route: check `match` in `wakewire_route_list` against the delivery log — repo must be `owner/repo`, branch filters only apply to pushes, gmail labels must match exactly.
2. Route disabled — `wakewire_route_toggle`.
3. No delivery row at all → the source never received it: webhook not firing (check GitHub's recent-deliveries page), smee channel disconnected, or Gmail label not applied.
4. Duplicate id → `skipped-duplicate` (see above).

## 4. Fix and replay

After fixing a template or route, `wakewire_replay` with the failed delivery id re-renders against the current config and enqueues it again — no need to wait for a new event. Replays bypass duplicate detection by design.
