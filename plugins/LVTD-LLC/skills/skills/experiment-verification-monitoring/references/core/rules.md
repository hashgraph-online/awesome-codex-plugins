# Experiment Verification Monitoring Rules

Use these rules when designing quality gates for experiments and platforms.

## Core Rules

### 1. Verify The Experiment Before Launch

Every experiment needs setup checks before broad user exposure.

- Confirm eligibility and targeting.
- Confirm assignment and variant consistency.
- Confirm exposure logging.
- Confirm primary and guardrail metric availability.
- Confirm treatment and control experiences.

### 2. Build Tools For Repeated Failure Modes

Manual checklists are not enough when errors repeat.

- Build QA tooling for spot-checking user experiences.
- Automate checks that are deterministic.
- Keep manual review for judgment-heavy UX or product questions.

### 3. Use Canaries To Catch Early Launch Issues

Canaries reduce blast radius.

- Start with limited exposure or a health-check window when appropriate.
- Check assignment balance, exposure volume, metric freshness, and obvious
  treatment errors.
- Define pause or rollback criteria before launch.

### 4. Run A/A Tests For Platform Health

A/A tests validate infrastructure, not product hypotheses.

- Use them periodically when platform trust matters.
- Monitor false positives, assignment balance, and metric pipeline behavior.
- Investigate surprising differences instead of dismissing them.

### 5. Monitor Active Experiments

Do not wait until final readout to find obvious failures.

- Alert on missing exposure, metric drops, assignment imbalance, and guardrail
  breaches.
- Monitor leakage, interference, and cross-test conflicts.
- Assign an owner for each alert category.

## Guidelines

Less strict recommendations:

- Track experiment quality metrics as platform KPIs.
- Add verification and monitoring steps to the experimentation playbook.
- Use dashboards that show both experiment health and business outcomes.

## Exceptions

- **Tiny internal experiments**: Manual verification may be enough when user risk
  and decision risk are low.
- **Emergency mitigations**: Launch safeguards may be abbreviated, but document
  the reason and add post-launch monitoring.

## Quick Reference

| Rule | Summary |
|------|---------|
| Prelaunch verify | Check setup before broad exposure |
| Tool repeated checks | Automate recurring failure modes |
| Canary early | Reduce blast radius and catch launch issues |
| A/A health | Test the platform itself |
| Monitor active | Alert before final readout |
