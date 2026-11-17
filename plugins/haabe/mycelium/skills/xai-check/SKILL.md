---
name: xai-check
description: "Explainability (XAI) audit for products containing AI components. Five-stage tier-scaled check: risk classification, stakeholder×question matrix, fidelity audit, system card, recourse path. Honest about what was validated functionally vs what needs user testing."
metadata:
  instruction_budget: "60"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# XAI Check Skill

Operational gate for the Explainability Theory Gate (Gate 13). Audits whether a product's AI components meet a defensible XAI bar — disclosure, decision-explanation, recourse, fidelity, system card — scaled to the AI Act risk tier.

This skill is **functionally-grounded** in Doshi-Velez & Kim's (2017) sense: it operates on artifacts and configuration, not on real users with real tasks. Output explicitly distinguishes `validated_functionally` from `needs_user_testing`. The honest tag is what passes Gate 13; user-grounded validation is recommended but not blocking.

**The gate reads this skill's record (v0.331.0).** On a product with AI components detected, an Explainability pass counts only when a `services[].xai` block holds a verdict for each stage the scale asks: at an L3 the tier (Stage 1); at an L4 or L5 every stage, with `recourse.verdict` asked from the `limited` tier up. A stage that does not apply takes a verdict saying so (`not_applicable`). The scale-lock gate and the release gate name the stage that is missing. Until 0.331.0 the gate passed on the status word.

## When to Use

- An L3's `release` or `close`, **only when `active-stack.yml :: ai_components.detected: true`**
- An L4's `release` — required when AI components reach user-affecting decisions (deny, recommend, rank, generate user-shown content)
- An L5's `release` — required for any user-facing AI feature at launch
- After any change to AI components, prompts, or surfaces that affect user-facing decisions
- When Gate 13 is checked during `/mycelium:diamond-progress`

## Precondition: AI components detected

Read `.claude/jit-tooling/active-stack.yml` (Step 1c output of `delivery-bootstrap` per `${CLAUDE_PLUGIN_ROOT}/jit-tooling/detector.md`). It is **project state** — it lives in the consumer's `.claude/`, not in the shared plugin cache.

- If `ai_components.detected` is missing or `false`: report **"No AI components detected — XAI Gate N/A. Run `/mycelium:delivery-bootstrap` if you believe AI is present but undetected."** Stop.
- If `ai_components.detected: true` but `user_facing_decisions: unknown` (Step 6 confirmation never answered): prompt the user explicitly: *"This product has AI components, but it's not on record whether their outputs reach end users in a user-affecting way. Does the AI's output deny / recommend / rank / generate content shown to users, or otherwise drive their experience?"* Do not proceed silently — XAI tier depends on this answer. If the user defers, default to `tier: limited` and note **"tier defaulted to limited pending user_facing_decisions confirmation"** in the output.

## Workflow (5 stages)

For each service in `services.yml` (loop — multiple services produce per-service findings):

### Stage 1 — Risk tier classification

**Source canonical tier from `/mycelium:regulatory-review` output if available.** Read `.claude/canvas/privacy-assessment.yml` for prior AI Act risk classification. If `/mycelium:regulatory-review` has run, use its tier; this skill does not re-classify regulatory tiers as that would risk producing divergent classifications across two skills.

If `/mycelium:regulatory-review` has not run:
1. Recommend running it: *"`/mycelium:regulatory-review` is the canonical AI Act tier classifier. Without it, this skill produces a provisional tier only — which is fine for early development but should not be the final source for L4/L5 transitions."*
2. Apply provisional logic: AI Act Annex III categories → `high`; user-affecting AI without Annex III → `limited`; non-user-affecting AI → `minimal`.
3. Record `xai.tier` with a `provisional: true` note until `/mycelium:regulatory-review` confirms.

If tier classification yields `prohibited`: **stop immediately.** Escalate. Do not run subsequent stages — the product cannot ship under EU AI Act Article 5.

**Item caps by tier** (pre-committed to prevent checklist sprawl):
- `minimal`: ≤5 total items across all stages
- `limited`: ≤15 total items
- `high`: ≤25 total items

### Stage 2 — Stakeholder × question matrix

Rows = relevant stakeholders for this tier:
- `end_user` (always)
- `affected_non_user` (high-risk only — e.g., a person whose data is used but who didn't initiate the interaction)
- `deployer_developer` (limited+)
- `regulator` (high-risk)

Columns = Liao, Gruen, Miller (2020) question categories, subset by tier:

| Tier | Questions checked |
|---|---|
| minimal | `output` (what can it do?), `why` (basic rationale) |
| limited | + `input` (what data?), `why_not` (contrastive), `how_to_be_that` (recourse) |
| high | + `what_if` (sensitivity), `performance` (per-population accuracy), `how_global` (overall mechanism) |

For each cell relevant at the determined tier, ask the operational question: **"Is this answerable for this stakeholder, in the moment of impact, by an interface that exists today?"** Verdict per cell: `pass` / `partial` / `fail` / `N-A`.

This is intentionally Bansal et al. (2021) friendly — the test is "answerable when needed," not "always-on documentation."

### Stage 3 — Fidelity audit

**Run only when the product surfaces LLM-generated rationales to users** (e.g., "Recommended because…", "Denied because…", chain-of-thought summaries).

1. Sample N outputs (N=5 minimal, 10 limited, 20 high) from production logs or a representative test set.
2. Method: blind a reviewer to the rationale. Show input + rationale; ask reviewer to predict the system's actual output. Record predictions.
3. Compute `blind_prediction_accuracy = correct_predictions / N`.
4. Verdict thresholds: `pass` ≥ 0.7; `partial` 0.5–0.69; `fail` < 0.5. Below 0.5 means the rationale doesn't actually justify the output — Lanham et al. (2023) faithfulness gap.

Save raw samples to `.claude/evals/xai-fidelity/<service>/YYYY-MM-DD.json` (mkdir -p on first write — directory may not exist). Aggregate stats land in `services.yml :: <service>.xai.fidelity`.

If the product does not surface LLM-generated rationales to users, set `xai.fidelity.verdict: not_applicable` and skip — but check Stage 2 for the equivalent surface gaps.

### Stage 4 — System card check

Reference `${CLAUDE_PLUGIN_ROOT}/templates/ai-system-card.md` (Mitchell et al. 2019 format). Required sections (per the template's `Required` markings):

1. Identity (system name, version, last-updated, maintainer, AI Act tier)
2. Intended use (primary use, intended users, intended context, out-of-scope)
3. Model details (vendor, model family, hosted vs on-device, training data class, fine-tuning, update cadence)
4. Performance and limitations (eval methodology, headline performance, per-population, known limitations, known foreseeable misuse)
5. Explainability (disclosure, per-decision rationale, confidence signaling, fidelity caveat) — required at limited+ tier
6. Recourse (path, reviewer, SLA, logging) — required at limited+ tier
7. Privacy and data handling
10. Contact and feedback

(8 and 9 are recommended, not required.)

Check whether the product publishes a system card at `docs/ai-system-card.md` or a documented equivalent. For each required section, mark `present` / `missing`. Verdict: `pass` (all required present), `partial` (≥70% present), `fail` (<70% present or no card published).

### Stage 5 — Recourse path test (limited+ tiers only)

End-to-end test:
1. Find the contestation surface from a representative point in the user journey where the AI fires.
2. Count interactions (clicks, form fields, navigation steps) from that point to a human reviewer.
3. Verify it routes to a human, not to a chatbot or feedback loop with no closure.
4. Check for a documented SLA (response-within-X commitment).
5. Verify contestation events are logged for product learning.

This is the Selbst & Barocas (2018) substance check. Without recourse, the rest of XAI is theatre. Verdict: `pass` (all five sub-checks pass), `partial` (path exists but missing SLA or logging), `fail` (no path or path loops).

## Postflight: Verify-After-Write (write-narration-verification discipline)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 Stage 2 graduation — v0.39.18). Before the user-facing summary claims "✅ updated `services.yml :: xai.*`" / "✅ refreshed Stage 3 fidelity" / similar, verify the write actually changed the targeted fields below — not just `_meta.last_validated`. Use the **Read tool** on `services.yml` after the edits to confirm `xai.tier` / `xai.surfaces.*` / `xai.recourse.*` / `xai.fidelity.*` / `xai.system_card.*` / `xai.remediation_history` hold the new values. If only `_meta` or `last_assessed_at` changed and value fields stayed stale, the narration is a state-claim on a state the skill did not achieve (parallel to AP#7 instance #18 worked failure, 2026-06-05). Validator Check 42 enforces preamble presence.

## Output

Write to `services.yml` per service:

```yaml
services:
  - id: svc-001
    name: "<service name>"
    xai:
      tier: limited
      last_assessed_at: "2026-05-04T12:00:00Z"
      surfaces:
        end_user:
          output: pass
          why: pass
          why_not: partial
          how_to_be_that: fail
          input: pass
        deployer_developer:
          output: pass
          # ...
      recourse:
        path_exists: true
        max_clicks_to_human: 4
        sla_documented: false
        logs_contestation: true
        verdict: partial
      fidelity:
        samples_audited: 10
        blind_prediction_accuracy: 0.65
        verdict: partial
        last_audited_at: "2026-05-04T12:00:00Z"
      system_card:
        path: "docs/ai-system-card.md"
        sections_present: [identity, intended_use, model_details, contact]
        sections_missing: [performance_and_limitations, explainability, recourse, privacy]
        verdict: fail
      validated_functionally: [stage_1_tier, stage_4_system_card, stage_5_recourse]
      needs_user_testing:
        - "stage_2 surfaces — answerable-when-needed verified by static review only"
        - "stage_3 fidelity — sample size 10 limits population-level claim"
```

Idempotency: re-runs **overwrite** the `xai` block in place; do not append. Preserves git diff readability across periodic re-audits.

## Display to user

After writing canvas, present a remediation list ranked by stakeholder impact:

```
XAI check — <service name> — tier: limited

Findings:
  ✓ Stage 1 (tier classification) — pass (provisional, /mycelium:regulatory-review not run)
  △ Stage 2 (matrix) — 2 cells fail: end_user.how_to_be_that, end_user.why_not
  △ Stage 3 (fidelity) — partial (0.65 — 5 of 10 sampled rationales did not predict the output)
  ✗ Stage 4 (system card) — fail (4 of 8 required sections missing)
  △ Stage 5 (recourse) — partial (path exists but no SLA documented)

Remediation (ranked):
  1. [end_user] Stage 4 — publish missing system card sections (explainability, recourse, performance, privacy)
  2. [end_user] Stage 5 — document the SLA for contestation responses
  3. [end_user] Stage 2 — surface contrastive (why_not) explanation in the UI
  4. [all] Stage 3 — investigate why fidelity is below threshold; consider tightening prompt or removing rationale surface

Validated functionally: stages 1, 4, 5 (static review).
Needs user testing: stages 2 (answerable-when-needed in real flows), 3 (population-level fidelity).

Run /mycelium:regulatory-review to confirm the tier is canonical, then re-run /mycelium:xai-check after remediation.
```

## Composition with other gates / skills

- **Upstream:** `/mycelium:regulatory-review` is canonical for tier classification; this skill consumes its output. G-S7 (disclose AI) and G-S8 (assess AI Act) are intent guardrails that this skill operationalizes.
- **Sibling:** `/mycelium:security-review` covers OWASP. Phase 2.3 will add explanation-attack threats to `threat-model.yml` — until then, explanation-layer threats are flagged in this skill's output but not enumerated structurally.
- **Downstream:** `/mycelium:definition-of-done` (AI-aware DoD, Phase 2.2) consumes Gate 13 verdicts.

## What this skill does NOT do

- It does not certify EU AI Act compliance. That requires qualified counsel.
- It does not test explanations with real users. It tags items as `needs_user_testing` for follow-up.
- It does not block the existing service-check / usability-check / security-review surface — those remain authoritative for their domains. XAI is the additional dimension when AI components are present.

## Theory citations

- Doshi-Velez & Kim (2017) — three-tier evaluation taxonomy; this skill is functionally-grounded by construction
- Liao, Gruen, Miller (2020) — XAI Question Bank, basis for Stage 2 matrix
- Mitchell et al. (2019) — Model Cards format, basis for Stage 4
- Lanham et al. (2023) — chain-of-thought faithfulness, basis for Stage 3
- Selbst & Barocas (2018) — recourse-as-substance, basis for Stage 5
- Bansal et al. (2021) — adaptive vs always-on explanation, framing for Stage 2
- EU AI Act Articles 13, 50 + Annex III — tier classification source
- NIST AI Risk Management Framework — explainability vs interpretability split
