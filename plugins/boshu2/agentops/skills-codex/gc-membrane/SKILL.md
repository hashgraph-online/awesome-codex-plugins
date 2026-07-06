---
name: gc-membrane
description: Reference for the agentops-membrane Gas City
---
# gc-membrane — the AgentOps close door for Gas City

Canonical pack source: **`packs/agentops-membrane/`** in the AgentOps repo (git-tracked). Imported into a city via `pack.toml` (pinned tree-URL, or local
path while iterating). Operator loop that drives it:
[`using-gc`](../using-gc/SKILL.md).

## Why it exists (the one structural gap)

Stock gc orchestrates superbly but has **no fail-closed close**: its
`mol-review-quorum` formula fans review out cross-family and even ships a
deterministic Go finalizer (`reviewquorum.Finalize`) — which has **zero
production callers**. The quorum verdict is whatever the synthesis *agent*
writes; an agent can synthesize "pass" over two failing lanes. That is
self-grading — exactly what AgentOps exists to prevent (**no verdict = not
done**). The pack replaces agent-written synthesis with a deterministic,
evidence-bound verdict computed by scripts the *control dispatcher* runs.

## What the pack ships

| Piece | Purpose |
|---|---|
| `formulas/membrane-quest.toml` | v2 workflow: worktree build with `[steps.check]` → `close-gate.sh`, `max_attempts = 3` |
| `membrane/close-gate.sh` | the close door (run by the dispatcher, never an agent) |
| `membrane/finalize.jq` + `finalize.sh` | deterministic verdict — the `reviewquorum.Finalize` rollup ported to jq, hardened |
| `membrane/scaffold-quest.sh` + `quests/_template/` | move-1 intake: default-FAIL `CONTRACT.md`, red `test.sh` |
| `agents/{planner,builder,verifier,agy-verifier}` | trinity + third family, RBAC via harness config |
| `doctor/law0-print-args`, `doctor/membrane-health` | blocking doctor checks |
| `orders/membrane-canary.toml` | scheduled structural smoke via `scripts/e2e.sh` |
| `tests/{finalize,intake}.bats` | pins the rollup parity + scaffold contract (bash+jq only) |
| `RESIDUAL-GAPS.md` | the two honest zero-nudge gaps + mitigations |

## The close-door flow, end to end

1. **Intake:** `scaffold-quest.sh <slug>` writes `CONTRACT.md` (default-FAIL
   acceptance ruler) + `test.sh` (executable red harness) on the quest repo's
   `main`. The gate later reads the contract from `main` ONLY
   (`git show main:CONTRACT.md`); **the builder never reads CONTRACT.md** —
   it reads `test.sh`.
2. **Build:** the builder (claude family, own worktree, keeps write) makes
   `test.sh` green on a branch.
3. **Check step fires** (control dispatcher, `[steps.check]`):
   `close-gate.sh` runs deterministic pre-gates (branch exists, non-empty
   diff vs main, contract present) → mints a per-round **nonce** → routes
   ONLY the diff + contract to **≥2 cross-family reviewer lanes** via
   `gc session submit` (the only verb that reliably drains an idle pane) →
   collects `review-quorum.lane.v1` JSONs → hands to the finalizer.
4. **Finalize** (`finalize.jq`) computes the verdict. **Precedence:
   hard > transient > findings > pass**, hardened beyond the upstream rollup:
   - **Nonce anti-replay:** a lane verdict without the exact round nonce is
     rejected as stale.
   - **Cross-family floor:** < 2 distinct provider families can NEVER
     CONFIRM (`fewer_than_two_families`).
   - **Degradation-aware:** transient lane loss (provider unavailable,
     timeout) ⇒ DEGRADED — retried WITHOUT consuming an attempt; never a
     false REFUTE.
5. **Outcome:** exit 0 CONFIRMED → quest bead closes with an evidence-bound
   record; exit 2 REFUTED (hard finding) → builder respawned, one of
   `max_attempts` (3) consumed; exit 3 DEGRADED → lane retry. Exhausted
   attempts leave the quest bead **OPEN** — never a spurious close.
   **The membrane never merges or pushes; a human merges the branch.**

## RBAC — author ≠ judge, enforced as config

Builder = claude family (opus), write access, only in its worktree.
Verifiers = codex/gpt (`LANE1`) and antigravity/gemini via agy (`LANE2`),
`permission_mode = "plan"` (read-only), fresh-context, receive only
diff + contract. Never same-family self-grade: quorum is builder-family vs
two other families. City wiring makes both lanes always-on `[[named_session]]`
entries so submit-delivery is deterministic.

## pawl-verdict.v1 — reading a verdict

Artifacts land at `<city>/membrane/<quest>/`:
`pawl-verdict-round-N.json` (+ latest copied to `pawl-verdict.json`),
`lane-<family>-round-N.json`, `nonce-round-N.txt`.

```json
{
  "schema_version": "pawl-verdict.v1",
  "disposition": "CONFIRMED | REFUTED | DEGRADED",
  "failure_class": "hard | transient | null",
  "refuters": [
    {"family": "gpt",    "verdict": "pass|fail", "nonce_echo": "…", "findings_count": 0},
    {"family": "gemini", "verdict": "pass|fail", "nonce_echo": "…", "findings_count": 0}
  ]
}
```

Checks when reading: `disposition`; ≥2 distinct `refuters[].family` on any
CONFIRMED; every `nonce_echo` matches the round nonce file; on REFUTED read
the lane JSON's findings (a placement/path finding may be a **diff-frame
mismatch** — a contract bug, not a build bug; fix the contract frame instead
of burning redo attempts).

## Self-verification

- `doctor/membrane-health` (blocking): door present + executable, formula
  resolves, trinity present, **≥2 provider families** configured.
- `doctor/law0-print-args` (blocking): every claude/antigravity provider
  carries an explicit empty `print_args` (the builtin defaults are headless
  print sinks — LAW 0).
- `orders/membrane-canary`: native cooldown order running `scripts/e2e.sh`
  (both doctor checks green + `gc lint`) — structural smoke, surfaced through
  `gc events`/dashboard.

## Residual gaps (honest, not papered over)

Two session/provider-boundary stalls stand between "installed" and
zero-touch — the idle-pane drain (only `gc session submit` recovers; a
keepalive order re-submits on cooldown) and the codex/agy first-run trust
modal (pre-trust via city-scoped `CODEX_HOME` / one interactive run). Both
documented with mitigations in the pack's `RESIDUAL-GAPS.md` and as
first-class moves in the troubleshooting ladder of
[`using-gc`](../using-gc/SKILL.md).
The durable fixes are upstream (headless verifier lane / submit-consume
guarantee) — the pack does not fake a root fix.

## Non-goals

No auto-merge/auto-push. No wrapping of gc's native surface. No new
stall-detection framework. No gating on `gc costs`. No `runtime=gc`
re-coupling and no gc subcommand under the `ao` CLI — the pack is gc-native
content that lives BESIDE `ao`/NTM.

## Scenarios

```gherkin
Scenario: Fail-closed verdict on a hard finding
  Given a quest round where one reviewer lane returns a hard finding with a valid nonce echo
  When finalize.sh computes the verdict
  Then the disposition is REFUTED with exit 2 and the quest bead stays open

Scenario: Transient lane loss never false-refutes
  Given a quest round where one reviewer lane is provider_unavailable
  When finalize.sh computes the verdict
  Then the disposition is DEGRADED with exit 3 and no redo attempt is consumed

Scenario: One family can never confirm
  Given a quest round where all lane verdicts come from a single provider family
  When finalize.sh computes the verdict
  Then the result is fewer_than_two_families and the disposition is not CONFIRMED
```

## Proof it works (live evidence, 2026-07-05)

Three real quests through the door on the native reference city:
REFUTED→redo→**CONFIRMED** (hello); **DEGRADED** on transient agy-lane loss
without a false refute (csv-stats); cross-family **hard REFUTE** where the
gpt lane caught 3 real blocking gaps the gemini lane passed
(install-gc-city) — the quest correctly stayed open. Artifacts:
`<city>/membrane/{hello,csv-stats,install-gc-city}/pawl-verdict*.json`.
