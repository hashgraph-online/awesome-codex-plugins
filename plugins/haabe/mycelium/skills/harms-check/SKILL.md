---
name: harms-check
description: "Use when building anything USER-FACING (or with persuasion/retention/cancellation/consent/pricing flows, or that touches vulnerable people) to surface design-level harm the security/privacy/compliance gates miss: dark/deceptive patterns and foreseeable misuse. Assumes the product works as designed and asks who it could harm and whether it is Happier-negative. NUDGE, not a block."
metadata:
  instruction_budget: "44"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Harms Check Skill

Design-time harm-to-users check — the safety-by-design lens the security/privacy/compliance gates structurally miss. Assumes the product works EXACTLY as designed. `/threat-model` (STRIDE) asks how an attacker breaks it; `/privacy-check` asks about personal data; neither asks: **who could this harm when it works as intended, and how could a legitimate feature be misused?**

This is the design-time front-end of the BVSSH **Happier** dimension: a manipulative or harmful design is Happier-negative by definition, and this gate catches it before `/bvssh-check` would only measure it post-hoc.

## When to run (JiT — conditional, NOT universal)

Fires only when the product-shape warrants it:
- **User-facing** product/feature (real people use it), OR
- has **persuasion / retention / conversion / cancellation / consent / pricing** flows (the dark-pattern surface), OR
- **touches vulnerable people** (children, patients, financially- or otherwise at-risk).

If none apply (internal dev tooling, a library, a build script), **SKIP — say so and move on.** This is a NUDGE, never a hard block.

**At release, the framework asks for it (v0.321.0).** When work that reaches real people has an exposure record on its diamond and no harms check recorded there, the release path says so in one advisory line: in the release gate's refusal, in `scale_locks.py --exposure-state`, and as context when a release is allowed. That line is the prompt to run this skill, or to record that it does not apply. It never refuses anything, and a Happier-negative verdict does not stop a release.

## Workflow

### 1. Dark / deceptive patterns (Brignull) — does the design manipulate the user?

Check the design against the recognised, regulated catalog (deceptive.design; FTC / EU Digital Fairness Act / GDPR-consent):
- [ ] **Obstruction / roach motel** — easy to get in, hard to cancel, leave, or delete
- [ ] **Sneaking** — hidden costs, drip pricing, sneak-into-basket, hidden subscription
- [ ] **Forced continuity / forced action** — silent auto-renew; forced account/consent to proceed
- [ ] **Confirmshaming** — guilt/shame wording to steer a choice ("No, I don't want to save money")
- [ ] **Nagging** — repeated interruption until the user relents
- [ ] **Misdirection / visual interference** — pre-ticked boxes, manipulative default, tricked hierarchy
- [ ] **Privacy zuckering** — coaxing users to share more than intended; consent dark patterns
- [ ] **Bait and switch / disguised ads** — the control does something other than advertised

Any hit = the design manipulates or coerces → Happier-NEGATIVE. Redesign for the honest default.

### 2. Consequence scanning (doteveryone) — intended AND unintended

- Intended consequences — which to amplify?
- **Unintended** consequences (assume it works as designed and scales) — which to **mitigate**?
- Who could this harm — including **vulnerable users AND non-users / third parties / society**?
- Who is **least able to absorb** the harm?

### 3. Foreseeable misuse (harms modeling) — weaponising a legitimate feature

- How could a bad actor use this feature-working-as-designed to harm someone (harassment, stalking, fraud, coercion)?
- What reasonably-foreseeable **"unsupported uses"** create harm?

## Output

```
## Harms Check: [Feature/Product]

Scope trigger: [user-facing | persuasion/retention flow | vulnerable users | N/A — skipped]

### Deceptive patterns
| Pattern | Present? | Honest redesign |
|---------|----------|-----------------|
| ... | yes/no | ... |

### Consequences & foreseeable misuse
| Harm | Who (incl. non-users / vulnerable) | Working-as-designed or misuse | Mitigation |
|------|------------------------------------|-------------------------------|-----------|
| ... | ... | ... | ... |

### Happier verdict
[net-positive for the user | Happier-NEGATIVE — redesign]

### Recommendations (NUDGE — advice, not a block)
1. ...
```

## Record the verdict on the exposure (v0.321.0)

When the diamond carrying this work has an exposure record (`exposures[]` in `.claude/diamonds/active.yml`), write the result on the record this check was run for:

```yaml
harms_check:
  'on': '2026-10-11'             # the date the check was run; quote both (a bare `on` is a YAML 1.1 boolean)
  verdict: net-positive          # net-positive | happier-negative | not-applicable
  note: "what was found, or why it does not apply"
```

- `not-applicable` is the SKIP above, written down: use it when none of the scope triggers apply, and put the reason in `note`.
- `happier-negative` is recorded as it is. It does not stop a release. The person decides whether the work goes out as designed, and the release path reminds them of the verdict when it does.
- It is not one of the exposure's `gates`, and nothing reads it to allow or refuse anything. Without it, the release path keeps saying that no harms check is recorded for that exposure.
- Use the Read tool on `.claude/diamonds/active.yml` before editing it, and change only this key.
- No exposure record yet (the work has not been put in front of anyone): the decision-log entry below is the whole record.

## Honest limits (scope guard)

This gate **educates** a builder who reached for a manipulative pattern without seeing the harm; it **cannot stop** a builder who deliberately wants to manipulate. It is a NUDGE keyed to product-shape — **not** a trust-&-safety / content-moderation apparatus. Online-content harms (CSAM, disinformation, hate speech) are out of scope and belong to specialised tooling, not Mycelium.

## Decision Log (MANDATORY per G-P4)

**APPEND** a `### Harms Check` entry to `.claude/harness/decision-log.md` with: the scope trigger, any deceptive patterns found, foreseeable-misuse / vulnerable-user harms, the Happier verdict, and mitigations accepted or waived.

## Theory Citations

- Brignull: Deceptive (Dark) Patterns
- doteveryone: Consequence Scanning
- Microsoft: Harms Modeling (foreseeable misuse; vulnerable- and non-user harm)
- Smart: BVSSH — the "Happier" dimension (this gate is its design-time front-end)
- eSafety / WEF: Safety by Design (anticipate harm before it occurs)
