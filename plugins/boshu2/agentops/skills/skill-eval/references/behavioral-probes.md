# Behavioral probes: preserve their existing meaning

`scripts/probe-skill.sh` remains the runner for small behavioral regression
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
`injected-prelude` establishes prelude-only evidence. Live runs use the selected
authorized native producer with equal scenario and repetitions. Effort levels
are a declared experimental choice, not a prerequisite for every question.

```bash
bash scripts/probe-skill.sh --probe <id> --replay
# Only within an already authorized live envelope:
bash scripts/probe-skill.sh --probe <id> --live --capture --reps 3 --output out.json
bash scripts/check-skill-probe-headroom.sh
```

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

Legacy behavioral ledger rows cite the headroom result, model, effort and
sample size. Append one row only under that ledger's existing admissibility
rules; preserve a valid INERT or losing result. Small samples remain
directional. If producer failure or truncation makes a rep `infra`
(discriminator exit 2), exclude it from the legacy **usable behavioral rate**
and report its count in the all-attempt accounting. Zero usable treatment reps
is UNMEASURED, never INERT. This rate convention does not authorize dropping
infrastructure attempts from coding-cohort accounting.

Use the legacy ledger and RUNBOOK only for their existing consumers:
[`LEDGER.md`](../../../evals/skill-probes/LEDGER.md),
[`RUNBOOK.md`](../../../evals/skill-probes/RUNBOOK.md) and
[`evals/skill-probes/README.md`](../../../evals/skill-probes/README.md).
