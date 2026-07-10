# Guardrail Value-Proof Methodology (pre-registered)

`age-workflow-guardrail-hooks-j39.2` · BC6-Orchestration · cc-hooks family

This document is the **pre-registered methodology** that lets a workflow-guardrail
hook earn the "lease on life" ADR-0002 demands. It is written and committed
*before* the measurement is run, so the success criterion and the null-tolerance
cannot be retrofitted to whatever the data happens to say.

> **Status at landing (no overclaim):** this ENABLES the ADR-0002 proof — it does
> not yet PROVIDE it. The guard ships INERT (opt-in installer); the telemetry
> channel collects **zero** data until it is installed AND N≥30 real fires
> accrue. So ADR-0002 l.58 is *not cleared at landing* — it becomes clearable once
> the data exists. (Recorded by the 2026-06-17 recent-commits review.)

## Why this exists (the whole point)

AgentOps went hookless (#511) on the finding that hooks "couldn't be proven to
have value" — the 2.x A/B eval showed injected context made no difference
(`aggregate_delta = 0`). ADR-0002
(`docs/adr/ADR-0002-agentops-3-hookless-cdlc-rearchitecture.md`, l.58) therefore
requires, for any hook to survive: **"test or eval evidence showing positive
value."** Without that evidence, the installed-skill-edit keystone guard is just
another unproven hook awaiting the next teardown. This methodology + the per-fire
telemetry it consumes *is* that evidence pipeline.

## The sensor: gate-blind per-fire telemetry

The keystone guard (`skills/cc-hooks/hooks/installed-skill-edit-guard.sh`) emits
**exactly one JSONL line per FIRE** to
`${AGENTOPS_HOME:-~/.agentops}/guardrail-telemetry.jsonl`
(override with `AGENTOPS_GUARDRAIL_TELEMETRY`):

```json
{"ts":"2026-06-16T18:30:00Z","session":"<session_id>","token_class":"installed-skill-edit","path_sha256":"<64-hex>"}
```

- `ts` — UTC ISO-8601, second resolution.
- `session` — the Claude `session_id` (the unit the attempt-rate is computed per).
- `token_class` — which mistake-token / guard fired (`installed-skill-edit`).
- `path_sha256` — **a SHA-256 hash of the edited path, never the raw path.**

**Privacy invariant:** the raw command/path is NEVER persisted — only the hash.
The hash is one-way; it lets us count *distinct* edited targets and detect
repeats without ever logging what the agent was editing. Asserted in
`tests/scripts/installed-skill-edit-telemetry.bats`.

**Inert by default:** the emission code only runs when the guard fires, and the
guard ships INERT (AgentOps 3.0 hookless default; opt-in installer only). On a
machine where the guard is not installed, zero lines are ever written. On a
machine where it IS installed, the happy path (any non-installed-skill edit)
writes nothing.

**Gate-blind:** the sensor records the *attempt*, not the outcome of the
redirect. It cannot see whether the agent subsequently "did the right thing" — by
design (see the Goodhart note below).

## The metric: fire-ATTEMPT rate over time

Define, per session `s`:

- `fires(s)` = count of telemetry lines with `token_class = installed-skill-edit`
  emitted during session `s`.

The success signal is a **declining fire-attempt rate across sessions** —
i.e. a downward trend in `fires(s)` (or `fires(s)` normalized by session
length / edit volume) as `s` advances in time. The interpretation: once a guard
reliably interrupts a mistake-token, the agent (and the operator tuning prompts/
skills around it) stops *attempting* the mistake. That is a learning signal that
the gate's own redirect **cannot fabricate** — the redirect fires *after* the
attempt is already counted; lowering the count requires the attempt itself to
stop happening, which the hook cannot do by counting.

### Why NOT the hand-roll / "did they comply" rate (the Goodhart trap)

The original design measured the hand-roll rate with the guard on vs off. That
was **rejected** (pre-mortem finding #3) as circular / Goodhart:

- The gate's redirect lowers the post-redirect hand-roll rate *by construction* —
  the guard exists to do exactly that, so "the rate went down" proves nothing.
- The counterfactual ("would the agent have complied without the guard?") is
  unobservable in a single timeline.
- `N=1` with the guard always-on is the same regime that produced the repo's
  `delta=0` / `-0.37` corpus-A/B nulls.

The attempt rate over time sidesteps all three: it is measured on the *input*
side of the redirect, so the redirect cannot move it; the trend is across the
agent's *own* history, needing no off-arm counterfactual.

## Pre-registered decision rule

Fixed **before** any data is collected:

- **Minimum N:** at least **30 sessions** with the guard installed before any
  trend claim is made. Below N, report raw counts only — no verdict.
- **Noise floor:** fire counts are low-rate and bursty (one footgun cluster can
  spike a single session). A declining trend counts only if it survives a
  per-session-median (or 5-session moving-average) smoothing — a single quiet
  session is not a trend.
- **Earns its keep (KEEP):** at N ≥ 30, the smoothed fire-attempt rate shows a
  **monotone-ish downward trend** (later windows strictly below earlier windows)
  AND the guard demonstrably caused at least one redirect (≥1 fire) without ever
  firing on the happy path (zero false-positive telemetry lines). This is
  positive behavior-change evidence per ADR-0002 l.58.
- **NULL is ACCEPTABLE (KEEP-on-no-harm):** if at N ≥ 30 the rate is flat or the
  trend is inconclusive, that is an **expected, acceptable outcome — not a project
  failure.** The repo's measured A/B base rate for context interventions is
  null/negative; a flat attempt-rate paired with **zero context tax** (silent on
  every happy path, asserted by the keystone bats) and **zero false positives**
  satisfies the ADR-0002 l.58 "lease on life" as *no harm + a measurable signal
  channel that exists and runs*. A guard that is provably silent and provably
  fires only on the real mistake-token has earned its keep even with a flat
  trend, because the failure mode it replaces (unproven, noisy, always-injecting
  hooks) is strictly worse.
- **CUT:** the guard is cut if, at N ≥ 30, telemetry shows it fired on the **happy
  path** (any false-positive line — a path that was not an installed-skill edit),
  OR the emission imposed a measurable context/latency tax, OR the fire-attempt
  rate **rises** with no operator explanation. Any of these means it costs more
  than it proves.

## Falsifiability summary

| Outcome at N ≥ 30 | Verdict | Rationale |
|---|---|---|
| Smoothed attempt-rate declines, ≥1 true fire, 0 false fires | KEEP | positive behavior-change evidence (ADR-0002 l.58) |
| Attempt-rate flat/inconclusive, 0 false fires, 0 tax | KEEP (null = acceptable) | no harm + live signal channel; beats unproven always-on hooks |
| Any false-positive fire, OR measurable tax, OR rising rate | CUT | costs more than it proves |

## Reproducing the read (when N is reached)

```bash
# Fires per session, oldest→newest:
jq -r 'select(.token_class=="installed-skill-edit") | .session' \
  "${AGENTOPS_GUARDRAIL_TELEMETRY:-$HOME/.agentops/guardrail-telemetry.jsonl}" \
  | sort | uniq -c

# Distinct targets touched (hashes), to spot repeated footguns:
jq -r 'select(.token_class=="installed-skill-edit") | .path_sha256' \
  "${AGENTOPS_GUARDRAIL_TELEMETRY:-$HOME/.agentops/guardrail-telemetry.jsonl}" \
  | sort | uniq -c | sort -rn
```

No raw path is ever available in the ledger — only hashes — so the read is
privacy-preserving by construction.
