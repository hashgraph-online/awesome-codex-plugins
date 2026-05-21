---
name: staff-engineer-mode
description: "Use when making engineering decisions across ideation, design, development, testing, release, operations, or maintenance"
---

# Staff Engineer Mode

## Iron Law

```
ONE PRIMARY SPECIALIST BY DEFAULT; INFER ROUTING CONTEXT BEFORE WITHHOLDING
```

Loading many plausible specialists is a routing failure.

## Precedence Over Generic Process Packs

When the request touches an engineering surface -- architecture, reliability, resilience, operations, security, delivery, data, platform, client, AI/ML, accessibility, cost, production-readiness, rollout, migration, incident response, control records, API design, service contracts, or design of any engineering system -- **Staff Engineer Mode runs first**.

Do not invoke `superpowers:brainstorming`, `superpowers:writing-plans`, or any other broad process / design skill as the first response to an engineering-system prompt. Route through Staff Engineer Mode and load the selected specialist via the Load Contract below. A process skill may be used only after the specialist is loaded, and only for sub-decisions inside that specialist's workflow.

Phrasings such as "build X", "design X", "make X reliable", "add HA to X", "plan a rollout", "review this service", "prep for launch", or "investigate this incident" -- where X is an engineering system -- ARE engineering-system prompts. Route them through Staff Engineer Mode, not through generic brainstorming. The user prompt does not need to name lifecycle phases or specialist slugs.

## Load Contract

To load a specialist, **Read** the file at `<specialist-root>/<slug>.md`. Resolve `<specialist-root>` in this order:

1. If a `SPECIALIST_ROOT=` line is present in this session's additional context (Claude Code, Cursor, OpenCode), use that absolute path.
2. Otherwise use the platform default:
   - Codex: `~/.codex/staff-engineer-mode/specialists`
   - Gemini: the `specialists` directory next to the loaded `GEMINI.md`
   - Any other host: the `specialists/` directory at the router skill's install root.

Three rules, all mandatory:

- **Use the Read tool. Do not use the Skill tool.** Specialists are not registered skills on any supported platform. `Skill staff-engineer-mode:<slug>` returns `Unknown skill` and is a routing failure.
- **Complete the Read before producing engineering guidance for routed work.** Do not answer routed engineering prompts from priors.
- **A confidently-routed answer without a matching Read in the same turn is a routing failure even when the slug is correct.**

## Overview

Users are not expected to know specialist names. Classify by artifact, phase, surface, and risk, then quietly select the specialist whose outputs fit the next useful artifact.

## When To Use

- The request asks for engineering decisions or guidance for design, delivery, operations, reliability, security, architecture, API, data, platform, or client work.
- The user asks to guide ideation, design, development, testing, release, or maintenance decisions.
- The user asks to plan implementation, guide development, de-risk an idea, compare engineering options, or shape a design before code exists.
- The prompt gives enough context to infer the artifact, surface, risk, or next decision even when it does not name a lifecycle phase.
- The request is broad, vague, or spans multiple engineering surfaces.
- No single specialist clearly dominates from the prompt.
- The user asks for staff-engineer-level architecture, reliability, security, operations, delivery, data, platform, client, or cost guidance.
- The user asks to troubleshoot an unclear network, deployment, reliability, performance, security, data, or operations issue.

## When Not To Use

- A focused specialist has already been selected and loaded for the current request.
- The request is product discovery, marketing, staffing, compensation, procurement, legal/auditor liaison, broad compliance program management, or business strategy.
- The request is routine editorial or mechanical single-file documentation cleanup with no source-of-truth, freshness, operational, or lifecycle decision.
- The work is outside system delivery, operations, security, reliability, or maintainability.

## Inputs To Infer

Infer these from the prompt, repo, files, branch context, and conversation. Do not ask the user to supply them as intake fields.

- **Artifact:** decision, design, plan, readiness check, rollout, investigation, runbook, migration, eval, control pack, or diff review.
- **Phase:** ideation, design, development, testing, before merge, release, migration, active incident, post-incident, regression, readiness, or maintenance.
- **Surface:** architecture, contract, reliability target, topology, dependency, performance, observability, delivery, data, platform, security, client, AI, accessibility, cost, or operator load.
- **Risk/scope:** availability, latency, durability, correctness, privacy/security, compatibility, release safety, tenant/customer impact, public edge, internal traffic, multi-service, or multi-location.

## Bundled Specialist Slugs

Pick `primary` and `secondary` only from this exact list. Never invent, shorten, or paraphrase a slug.

```
accessibility-gates, agent-pr-review, ai-coding-governance, api-design-and-compatibility,
architecture-decisions, backup-and-recovery, caching-and-derived-data,
code-readability-for-agents, configuration-and-automation-safety,
cost-aware-reliability, cryptography-and-key-lifecycle, database-operations, data-contracts,
data-pipeline-reliability, dependency-and-code-hygiene, dependency-resilience,
dev-environment-parity, distributed-data-and-consistency, documentation-lifecycle,
edge-traffic-and-ddos-defense, engineering-control-evidence, event-workflows,
experimentation-and-metric-guardrails, feature-flag-lifecycle, fleet-upgrades,
high-availability-design, identity-and-secrets, incident-response-and-postmortems,
infrastructure-and-policy-as-code, internal-service-networking, llm-application-security,
llm-evaluation, llm-serving-cost-and-latency, migration-and-deprecation,
ml-reliability-and-evaluation, mobile-release-engineering, observability-and-alerting,
oncall-health, performance-and-capacity, platform-golden-paths, privacy-and-data-lifecycle,
production-readiness-review, progressive-delivery, release-build-reproducibility,
resilience-experiments, secure-sdlc-and-threat-modeling, slo-and-error-budgets,
software-supply-chain-security, state-machine-correctness, tenant-isolation,
test-data-engineering, testing-and-quality-gates, vulnerability-management,
web-release-gates
```

## Workflow

1. Infer the requested artifact and phase from prompt, repo, files, branch context, and conversation before naming any skill.
2. If the work is in ideation, design, development, testing, release, or maintenance and has an engineering surface, route by the decision or artifact the specialist should guide; concrete files, diffs, and repo artifacts improve the answer, and are required only for explicitly diff-specific review.
3. Treat phase labels as signals, not hard requirements; infer applicability from context, artifact, surface, risk, and the next decision.
4. Translate named tools into capabilities; routing outputs must use capability language, not repeat tool, vendor, framework, protocol, database, or command names from the prompt.
5. Pick `primary` (and any `secondary`) verbatim from the Bundled Specialist Slugs list above; if no listed slug fits, withhold routing instead of inventing or paraphrasing one.
6. Choose the narrowest primary whose required outputs match the next artifact.
7. Add one secondary only when the user explicitly asks for a separate artifact covered by another skill.
8. Load the chosen specialist per the Load Contract above before producing detailed guidance.
9. If confidence is low, infer the safest narrow in-scope route from available context; withhold routing only when no engineering lifecycle/control frame is present.
10. Keep single-surface verification details with the matching specialist; use `engineering-control-evidence` only for cross-surface mappings, scorecards, exceptions, or control packs.
11. Reframe out-of-scope work as an engineering-control question only when that is plausible.

## Synthesized Default

Select one primary when the prompt has enough context. Recommend at most one secondary follow-up. Broad requests become a short sequence, not a pile of loaded specialists.

## Exceptions

- For explicit launch/readiness decisions or broad release readiness checks, use `production-readiness-review` as primary.
- For active incidents, use `incident-response-and-postmortems` first even if root cause appears to belong elsewhere.
- For vague prompts such as "make this better" or "troubleshoot a network issue", infer from repo and conversation context before withholding routing.
- For out-of-scope business or ceremony prompts, do not select a skill unless context already supplies an engineering lifecycle/control framing.

## Review Routing

Treat "review" as a verb until the artifact proves otherwise.

- Concrete PR, branch, patch, last commit, or diff review before merge routes to `agent-pr-review`.
- Changed files alone do not make a diff review; route static-analysis or maintenance backlog prioritization to `dependency-and-code-hygiene`.
- Generic review-system design, reviewer routing, ownership, change size, review latency, or DORA workflow has no routed specialist unless a concrete engineering surface is present.
- Launch readiness, go/no-go, tier upgrade, or broad release readiness routes to `production-readiness-review`.
- Design review, architecture review, security review, API review, data review, rollout review, or test review without a concrete diff routes by the engineering surface, not by the word "review".
- A surface-specific change before merge still routes to the narrow surface specialist when the requested artifact is compatibility, deprecation, migration, safety, rollout, security, accessibility, data, or test results rather than a general diff verdict.

## Required Outputs

- For confident routing: primary specialist slug; optional secondary only when necessary; confidence of high or medium.
- Inferred intent: requested artifact, dominant surface, work phase, and one-sentence rationale.
- For explicit eval-harness runs only: include a fenced `routing` block only for confident in-scope routing; never emit a routing block for low-confidence, ambiguous, or out-of-scope prompts. The block contains a JSON object with `primary`, `secondary`, `confidence`, `artifact`, `surface`, `phase`, and `rationale`; JSON text fields must not repeat tool, vendor, framework, protocol, database, or command names from the prompt.
- For low-confidence routing: infer a best-effort route when in scope; otherwise withhold routing without intake questions, candidate lists, confidence labels, routing drafts, or specialist names.
- Out-of-scope reframe when applicable, without specialist names or candidate routes.

## Checks Before Moving On

- `single_primary`: output has exactly one primary specialist unless routing is withheld.
- `secondary_cap`: output has no more than one secondary specialist.
- `capability_translation`: tool, vendor, or framework names are translated into capability language before routing and not repeated in routing block fields.
- `scope_check`: out-of-scope requests are reframed or declined without specialist names.
- `ambiguity_check`: ambiguous prompts infer from available context when possible; withheld routes expose no specialist names, candidate routes, confidence labels, drafts, or intake questions.
- `intent_inference`: rationale identifies the requested artifact and phase before naming a skill.

## Routing Tiebreakers

Use this section for common routing precedence. Load `references/routing-matrix.md` for exact-slug guardrails, eval runs, exact-slug uncertainty, or adjacent surfaces.

- Explicit launch, major traffic shift, tier upgrade, or readiness decision routes to `production-readiness-review`; active user-impacting incidents route to `incident-response-and-postmortems` before root-cause specialty work.
- Prefer newer narrow routes over broad neighbors. Concrete PR, branch, patch, or diff review routes to `agent-pr-review` even when test results are mentioned; otherwise route the engineering decision to the narrow surface specialist.
- Reliability policy, telemetry construction, on-call load, fault-domain topology/static failover capacity, restore capability, failure experiments, overload controls, and state invariants are separate surfaces.
- API compatibility, data contracts, migrations, hygiene, fleet upgrades, event replay/DLQ, database backfills, cross-service database/storage correctness, cache freshness, and pipeline freshness stay distinct.
- Database migration execution is `database-operations`; if the same prompt separately asks for future blocking checks, add `testing-and-quality-gates` as secondary.
- Build/release artifacts, production exposure, rollback plans, config or automation mutation, and feature-flag lifecycle are separate delivery artifacts.
- Desired-state capture, drift detection, reconciliation, or emergency exception rules after manual infrastructure changes route to `infrastructure-and-policy-as-code`.
- Deprecation PRs/no-new-usage checks stay with `migration-and-deprecation`; ML promotion/eval/skew/drift/rollback stays with `ml-reliability-and-evaluation`.
- Security routes by artifact: threat model, identity/secrets, cryptography, supply-chain trust, deployed vulnerability, tenant boundary, privacy lifecycle, or LLM app risk.
- Public edge defense, service identity/discovery/locality, dependency retry/timeout/circuit-breaker policy, backend capacity, browser field/lab release signals, accessibility, cost tradeoffs, LLM eval/serving/security, AI coding controls, and code readability stay separate.
- Single-surface verification details stay with the matching specialist; cross-surface control mappings, scorecards, exception records, and control packs route to `engineering-control-evidence`.

## Red Flags - Stop And Rework

- More than two specialists are selected automatically.
- The router chooses from a phrase match without identifying artifact and phase.
- A tool or vendor name drives routing without capability translation, or appears in routing block text.
- `production-readiness-review` is used for any broad prompt without a readiness event.
- Compliance, staffing, compensation, procurement, or marketing work is routed as engineering work.
- A low-confidence or out-of-scope answer names candidate specialists, prints a routing draft, or exposes the internal shortlist.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Keyword matching | Infer artifact, phase, surface, and risk. |
| Loading every related specialist | Choose one primary and list at most one follow-up. |
| Treating tools as domains | Translate tools to capabilities. |
| Dumping candidate specialists | Infer the narrowest route, or withhold only when no in-scope frame exists. |
| Asking intake questions too soon | Infer from prompt, repo, files, branch context, and conversation first. |
