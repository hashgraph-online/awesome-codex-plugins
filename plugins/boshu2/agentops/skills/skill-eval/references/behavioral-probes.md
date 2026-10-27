# Behavioral probes: preserve their existing meaning

The AgentOps source checkout's `scripts/probe-skill.sh` remains the runner for
small behavioral regression
probes and immutable replay. It exposes an empty workspace and one injected
SKILL.md, not a complete installed-package coding trial. Its verdict measures
**behavior change**, never quality uplift or productive engineering completion.
Existing ledger entries retain that meaning and their recorded limitations.

| Probe form | Use when | Discriminator |
|---|---|---|
| Tier 1 — quiz | A decision rule is the caller's behavioral question | The answer/action on the scenario |
| Tier 2 — seeded task | Applying a discipline in work is the question | Whether the agent acted on a realistic planted defect |

Either form may be the starting point. Use [seeding](seeding.md) for seeded
tasks. Grade the act, never vocabulary copied from the treatment. A floor probe
detects at least one act; a multi-defect band needs both lower and upper bounds
to catch omission and finding spray. Calibrate against a transcript performing
the act without the prelude's wording and one repeating the wording without the
act.

The declared `treatment_source` remains the only arm variable: `canonical-skill`
uses exact SKILL.md bytes and is the mode the coverage gate counts;
`injected-prelude` establishes prelude-only evidence. The live runner uses the
Codex adapter; run it only when that adapter is available and caller-authorized,
with equal scenario and repetitions. An unavailable or unauthorized route is
UNMEASURED, not permission to substitute another runtime. Effort levels are a
declared experimental choice, not a prerequisite for every question.

Take the replay and live commands from the
[skill-probes README](https://github.com/boshu2/agentops/blob/main/evals/skill-probes/README.md#running)
(AgentOps source checkout only). Three
facts decide whether one runs and what it shows (checked 2026-10-25):

- **Replay needs a dated set.** Pass `--replay --fixtures <set>` naming a
  directory that holds `fixture-set.json`; no probe has a usable default
  `fixtures/` set, and `premortem-self-validation` (LEGACY-UNVERIFIED) has no
  replayable set at all.
- **Exit 0 is not reproduction.** A replay reproduces a stored result only when
  its scorecard reports `evaluator_matches_capture: true`. Every committed set
  replays with `false`, which the coverage gate labels `evaluator-stale`, so
  treat the committed sets as historical.
- **Live reps and names are bound.** A live capture, only inside an authorized
  envelope, takes `--reps` equal to `probe.json` `reps` (2 on every committed
  probe) or omits it, plus a new `--fixtures` name and `--output` path each
  time; the runner refuses another rep count, an existing fixture set or an
  existing scorecard before dispatch.

AgentOps source checkout only: from the repository root,
`bash scripts/check-skill-probe-headroom.sh` reports the classes below.
Authoring a probe means supplying the package the runner reads (`probe.json`,
`question.md`, `discriminator.sh`, a prelude only in `injected-prelude` mode)
and its replay result.

## Headroom classifications

The existing `skill.probe-headroom` gate in `cli/internal/probeheadroom` owns
classification and thresholds. Its multi-effort saturation rule remains the
legacy gate contract; do not fabricate enough runs to satisfy it or rederive
the rule in a new report. Read and report the actual answer:

- **SATURATED:** the probe cannot distinguish the targeted act. Preserve the
  observation as a scenario limitation in the RUNBOOK; do not append a skill
  verdict to the legacy ledger. Do not infer skill value or lack of value.
- **FLOOR:** treatment did not act. Check the discriminator on a known passing
  transcript. The result alone does not prove the skill cannot help elsewhere.
- **UNMEASURED:** no usable measurement, not INERT.
- **SEPARATED:** the gate found usable headroom. This classification itself does
  not establish positive treatment benefit; retain the actual probe verdict.

## Legacy ledger

[`LEDGER.md`](https://github.com/boshu2/agentops/blob/main/evals/skill-probes/LEDGER.md) and
[`RUNBOOK.md`](https://github.com/boshu2/agentops/blob/main/evals/skill-probes/RUNBOOK.md)
(AgentOps source checkout only) keep the historical
verdicts under their own admissibility rules; keep a valid INERT or losing
result. A rep scored `infra` (discriminator exit 2) leaves the usable
behavioral rate but stays in the all-attempt count; zero usable treatment reps
is UNMEASURED, never INERT.
