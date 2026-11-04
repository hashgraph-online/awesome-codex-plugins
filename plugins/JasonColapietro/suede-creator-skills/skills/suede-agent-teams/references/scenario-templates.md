# Scenario Templates and Feature Flag Practice

Pre-built rosters, lane maps, and rollout mechanics for common high-risk work.
Read the scenario that matches the objective before opening lanes; adjust only the
named target. Every roster, gate, and status word used here is defined in the
`suede-agent-teams` SKILL.md: these are instantiations, not new machinery.

## Contents

- [(a) Auth Rewrite](#a-auth-rewrite)
- [(b) Payment Integration](#b-payment-integration)
- [(c) Public Launch Review](#c-public-launch-review)
- [(d) Data Migration](#d-data-migration)
- [(e) Performance Audit](#e-performance-audit)
- [(f) Recovery / Incident Response](#f-recovery--incident-response)
- [Feature Flag Strategy](#feature-flag-strategy)

## (a) Auth Rewrite

Roster: Scout, Planner, Builder (auth lane only), Code Grader, Code Reviewer, Release Verifier, Handoff Writer
RFC required: yes. Shared session/token contract must be accepted before Builder opens.
Flag required: yes. Default off in production; ramp by internal → 1% → full.

Lane map:
- Scout: map current auth flow, session storage, token shape, and all routes that read session
- Planner: list every file that must change and every route that must be regression-tested
- Builder: auth files only. No touching unrelated routes.
- Code Grader: grade security lane with zero tolerance for C or below on the security dimension
- Code Reviewer: focus on token lifecycle, expiry, rotation, and session fixation
- Release Verifier: confirm auth works in production before any other lane ships
- Handoff Writer: include session contract diff and regression test evidence

Done signal: login, logout, token refresh, and session expiry all pass in production

## (b) Payment Integration

Roster: Scout, Planner, Builder (payment lane only), Code Grader, Code Reviewer, Release Verifier, Handoff Writer
RFC required: yes. Payment data shape and provider contract must be accepted.
Flag required: yes. Never ramp payment paths without a staged rollout.

Lane map:
- Scout: map current billing models, Stripe/provider SDK version, webhook endpoints, and idempotency handling
- Builder: payment files and webhook handlers only
- Code Grader: flag any missing idempotency key, error retry, or PCI-sensitive data log as a blocker
- Code Reviewer: confirm error handling covers card decline, webhook replay, partial capture, refund edge cases
- Release Verifier: test with Stripe test mode, then confirm webhook signature validation in production
- Handoff Writer: include provider dashboard link and webhook log evidence

Done signal: charge, refund, and webhook replay all pass in production with idempotency confirmed

## (c) Public Launch Review

Roster: Scout, Design Reviewer, Visibility Grader, Code Reviewer, Release Verifier, Handoff Writer
RFC required: no (review-only, no builder lane)

Lane map:
- Scout: enumerate every public-facing URL, meta tag, og:image, CTA, and claims sentence
- Design Reviewer: check above-fold load, mobile rendering, accessibility, and state coverage
- Visibility Grader: score first-screen clarity, CTA pull, proof, AI readability, and structured data
- Code Reviewer: check for console errors, broken links, unresolved env vars, and exposed secrets
- Release Verifier: confirm live URL, DNS, SSL, and all published statements match approved copy
- Handoff Writer: include Lighthouse score, screenshot evidence, and any unresolved published statement

Done signal: all public URLs verified live, no console errors, Lighthouse performance ≥ 80

## (d) Data Migration

Roster: Scout, Planner, Builder (migration lane only), Code Grader, Release Verifier, Handoff Writer
RFC required: yes. Data shape before/after and rollback strategy must be accepted.
Flag required: migration itself cannot be flagged; gate behind a manual trigger or migration script run

Lane map:
- Scout: map current schema, row counts, FK constraints, indexes, and any running jobs that read the affected tables
- Planner: write migration script, define rollback script (reverse migration or restore point), and identify zero-downtime vs. maintenance-window requirement
- Builder: migration files only. Schema changes separated from data backfill into two sequential sub-lanes.
- Code Grader: grade data/state dimension with zero tolerance for D or below; flag missing rollback script as a blocker
- Release Verifier: run migration against a staging DB clone, confirm row counts before/after, confirm app boots with new schema, then promote to production
- Handoff Writer: include before/after row counts, migration command with timing, and rollback script location

Done signal: production DB row counts match expected delta, app health check passes, rollback script tested in staging

## (e) Performance Audit

Roster: Scout, Planner, Builder (perf lane only), Code Grader, Release Verifier, Handoff Writer
RFC required: no, unless audit reveals a structural change (e.g. query rewrite, CDN switch).

Lane map:
- Scout: run Lighthouse, measure Core Web Vitals (LCP, INP, CLS), identify top 3 bundle contributors, map slow DB queries (EXPLAIN ANALYZE), and list current caching headers
- Planner: rank findings by impact × effort, list the three highest-ROI fixes
- Builder: implement only ranked fixes. No opportunistic refactors.
- Code Grader: confirm each fix does not regress correctness or introduce a race condition
- Release Verifier: compare Lighthouse before/after with screenshots; confirm no regression on primary user paths
- Handoff Writer: include before/after Lighthouse scores, Core Web Vitals deltas, and any deferred findings

Done signal: LCP < 2.5s or measurable improvement documented; no regression on primary paths

## (f) Recovery / Incident Response

Roster: Scout, Builder (fix lane only), Release Verifier, Handoff Writer
RFC required: no (incident is already in progress; run the Rollback Decision Tree, not an RFC)
Flag required: n/a: this scenario reacts to an existing deploy, it does not introduce one

Lane map:
- Scout: identify what shipped, when, and what changed; walk the Rollback Decision Tree (data loss/corruption, security exposure, primary path broken, degraded-but-functional, or cosmetic) and name which branch applies
- Scout: if the branch is "ROLLBACK IMMEDIATELY" (data loss/corruption or security exposure), say so and stop: do not investigate further before rollback, per the Rollback Decision Tree
- Builder: executes the rollback, or the <15-minute fix, or the hot-fix-forward, per the branch Scout named. No opportunistic changes outside the incident scope.
- Builder: after rollback, write the immediate summary (what rolled back, what was affected, who was notified) and open a follow-up issue, per the Rollback Decision Tree's post-rollback steps
- Release Verifier: confirm the primary path is restored in production before any other lane closes
- Handoff Writer: run the post-mortem for any P0 or P1 incident (required) or P2 (optional but encouraged); skip for P3. Populate Timeline, Impact, Root Cause, Contributing Factors, What Went Well, and Action Items with owners and due dates.

Done signal: primary path verified restored in production; for P0/P1, a completed post-mortem with status `open` and every action item assigned an owner

## Feature Flag Strategy

The trigger list, when to flag, stays in SKILL.md. This is the mechanics once a
lane is flagged.

**Flag lifecycle:**
1. **Introduce**: create the flag, default off in production. Ship the code behind the flag.
2. **Ramp**: enable for internal users, then 1%, 10%, 50%, 100% of production traffic. Monitor at each ramp.
3. **Remove**: once 100% and stable for ≥2 weeks, delete the flag and all conditional branches. Flag removal is a P3 code review finding if overdue. Set the removal date at creation, not after ramp.

**When NOT to flag:**
- Bug fixes with no behavioral change (ship directly)
- Internal tooling with no external API contract
- Refactors that don't change behavior (ship with a focused review)

**Flag hygiene rules:**
- Every flag gets a removal date at creation. Stale flags are a debt item (P3 code review finding).
- Flag names describe the feature, not the state: `new_billing_flow` not `enable_billing`.
- Never nest flags inside flags without a design review.
