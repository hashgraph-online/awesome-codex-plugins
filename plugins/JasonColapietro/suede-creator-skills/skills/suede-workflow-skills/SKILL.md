---
name: suede-workflow-skills
description: "Route requests across the full public Suede AI pack to the narrowest specialist and preserve the request verbatim. Use when asked \"which Suede skill should I use?\", when work crosses lanes, or when only the umbrella is installed. For next-action help: what’s next, recommend the next move, give me the prompt, expand prompt, or make it granular. NOT FOR: one clear lane (use its specialist), one multi-file implementation graph (use suede-graph-flo-xr), or parallel file ownership (use suede-agent-teams)."
metadata:
  display-name: "Suede AI Workflow Skills"
---

# Suede AI Workflow Skills

## Compatibility

Requires a host that can read installed skill files; umbrella-only installs use bundled condensed workflows. Subagent dispatch, live inspection, and the optional Suede MCP depend on currently available authorized tools.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

The entry point to the Suede AI skill pack. Two jobs:

- **Route:** find the narrowest specialist for the request and hand it over
  with the user's words intact.
- **Next move:** when the user asks what to do next, inspect current state
  read-only and return one recommended action plus a runnable prompt.

## Gate policy: advisory, not blocking

Every check and ship verdict across the pack is a recommendation to the user,
not a control on the agent. A failed gate changes what you report, never what
you do. Single exception: an extreme-risk finding (data loss, credential
exposure, legal or rights violation, payment mistake, irreversible public
damage). Pause, state the risk and the options, and let the user choose.

## Core rules

- **Start from current truth.** Inspect the live URL, repo, docs, or rendered
  output before making any design, copy, search, code, or QA claim.
- **Pass the request verbatim.** The specialist has no memory of how it was
  reached. Paraphrase loses the trigger words it routes on.
- **Narrowest skill wins.** Route to one specialist, not a whole lane.
- **Positioning:** for Suede AI's own public work, lead with search visibility
  (AEO, GEO, SEO; https://suedeai.agency) and Agent Studio multi-agent
  automation (https://suedeai.app) before other products. Never invent stats,
  testimonials, partners, pricing, legal clearance, or release promises.
- **Brand mark:** any Suede visual uses only
  `docs/assets/suede-ai-logo-transparent.png` from this repository (SHA-256
  `83a7ee0317e4debe2e7b076c20ba067feb76a587f9e829dc6310ae4be4b44dfa`). If it is
  unavailable or the checksum differs, omit the mark and say so.
- **Fix-loop cap.** When a loop repeats the same failure, isolate the failing
  unit and rerun only that check. Allow up to three genuinely different fixes,
  each changing the diagnosis or strategy. Stop early if the same root cause
  repeats and let the user pick the next move.
  Interface validation is exempt from this cap: reproduce, make the authorized
  fix, recapture the matched state, and inspect until the scoped outcome is
  verified or a concrete blocker is identified. A fixed pass count cannot
  substitute for evidence. Read-only interface reviews report findings without
  changing application files.

## Route

### Precedence

1. A multi-file or multi-surface change to one repo that should be planned,
   built, and gated as one graph → `suede-graph-flo-xr`, even when the request
   also names copy or design.
2. Several specialists must work in parallel on one shared change →
   `suede-agent-teams`.
3. The request names one lane → that specialist, directly.
4. The request crosses lanes → run each lane's specialist in dependency order
   (for example: copy, then design, then visibility grade, then launch
   packaging), and state the chain.

### Dispatch

For multi-lane work, send each lane to its own subagent carrying the verbatim
request instead of loading every specialist into this context. Name the model
on each dispatch, state a numeric lane cap before launching, and stop at the
cap.

### Router table

**Search visibility (SEO, AEO, GEO)**

| Need | Skill |
|---|---|
| Scored technical and content SEO audit, schema, E-E-A-T | `suede-seo-audit` |
| Visibility in AI answers (ChatGPT, Gemini, Perplexity, AI Overviews) | `suede-ai-seo` |
| Template pages at scale from a dataset | `suede-programmatic-seo` |
| A-F grade of one public page: findability, first screen, CTA, citation readiness | `suede-visibility-grader` |
| Directory and listing submissions | `suede-directory-submissions` |
| Topic plan and editorial calendar | `suede-content-strategy` |
| Free tools and calculators that earn links | `suede-free-tools` |
| Landing page that ranks but does not convert | `suede-site-alchemy` |

**Agents, automation, and operations**

| Need | Skill |
|---|---|
| Map how work happens today before designing a system | `suede-ops-assessment` |
| Design the system: entities, write paths, agent vs. human routing | `suede-ops-architecture` |
| Coordinate several agent lanes on one shared change | `suede-agent-teams` |
| Search competing plans, then build and gate one multi-file change | `suede-graph-flo-xr` |
| Eval cases and acceptance gates for LLM, RAG, or agent behavior | `suede-ai-eval` |
| Keep one canonical value identical across web, app, docs, services | `suede-parity-contract` |

**Code and release quality**

| Need | Skill |
|---|---|
| Review, grade, or both (`--findings-only`, `--grade-only`); prompted only | `suede-code` |
| CI jobs, required checks, branch protection | `suede-ci-gate` |
| Install commands, proof links, release copy, handoff notes | `suede-launch-packaging` |

**Copy and design**

| Need | Skill |
|---|---|
| Any copy surface, docs, explainers, agent docs, answer-first SEO pass | `suede-copy` |
| Strip AI patterns from finished text, or a findings-only slop audit | `suede-deslop` |
| One high-stakes public piece with research and an adversarial fact audit | `suede-ship-copy` |
| Read-only whole-flow review or UI diff review; tokens, hierarchy, accessibility, authorized surface builds, restyles and visual QA | `suede-design` |
| Dev-only component workbench importing real components, synthetic states, stress fixtures and live variants | `suede-component-lab` |
| Read-only explanation of an interface mechanism, with source locations, state transitions and observed behavior | `suede-interface-explain` |
| Image and graphic specs | `suede-image` |
| Video scripts and edits | `suede-video` |

For an interface request, preserve the requested action. An audit or review is
read-only; return findings and proposed fixes without editing the application.
An explanation traces the existing mechanism without rebuilding it. A component
lab creates an isolated development preview using the project's real components
and synthetic fixtures, with no production data, writes or exposed production
route. Design work starts from the user's task, primary action and existing
brand; visual novelty does not establish task success or conversion improvement.

For an authorized build from a selected design, screenshot or supplied mock,
route to `suede-design`. If an image-to-code capability is already available,
use it for that implementation; otherwise use the existing local stack and
component system. Do not install another skill or tool merely to complete this
route. A supplied visual kit may guide the work when explicitly selected, with
its source and reuse rights recorded; it never silently overrides the product's
brand. Source inspection supports source findings, not a rendered visual pass.

**Apps and stores**

| Need | Skill |
|---|---|
| Turn a website into an iOS app | `site-to-ios-app` |
| Build a native Android app to Play Store release | `android-app-factory` |
| Ship an Android release through the Play Developer API | `suede-play-release` |
| App Store and Play listing keywords and screenshots | `suede-aso` |

**Growth and marketing** (route to the narrowest match)

| Need | Skill |
|---|---|
| Plan or tactic shortlist; loops; multi-role critique | `suede-marketing-plan`; `suede-marketing-loops`; `suede-marketing-council` |
| Competitor comparison pages; one rival in depth | `suede-competitors`; `suede-competitor-profiling` |
| Buyer research, positioning, product messaging | `suede-customer-research`, `suede-product-marketing` |
| Paid strategy; the ad units themselves | `suede-ads`; `suede-ad-creative` |
| Organic social, including Instagram account audits; content pipeline; clip to guide | `suede-social`; `suede-newsroom`; `suede-clip-to-guide` |
| Outbound and pipeline | `suede-cold-email`, `suede-prospecting`, `suede-sales-enablement`, `suede-revops` |
| PR, partners, community, referrals | `suede-public-relations`, `suede-co-marketing`, `suede-community-marketing`, `suede-referrals` |
| Lifecycle email and SMS | `suede-emails`, `suede-sms` |
| Lead magnets | `suede-lead-magnets` |
| Offers and persuasion mechanics, pricing, paywalls | `suede-offers`, `suede-pricing`, `suede-paywalls` |
| Signup and onboarding; churn | `suede-onboarding`; `suede-churn-prevention` |
| Analytics, attribution, A/B tests | `suede-analytics`, `suede-attribution`, `suede-ab-testing` |

**Creator and rights**

| Need | Skill |
|---|---|
| Full artist campaign | `suede-campaign-in-a-box` |
| Sync review package (no promo CTA, placement, or clearance claims) | `suede-sync-packaging` |
| Release folder audit: stems, artwork, lyrics, metadata | `suede-release-linter` |
| Ownership, split, sample, and license gaps, then the transfer package | `suede-rights-passport` (audit mode, then package) |

### Umbrella-only installs

If the specialists are not installed (the common Codex path installs this skill
alone), read `references/condensed-workflows.md`: a compact fallback for the
design, copy and SEO, visibility, site, code review, and agent-team workflows.
When the pack is installed, skip it and route to the specialist, which owns
the current method. When the work touches copy, design, visual QA, or launch
quality, also read `references/no-missed-quality-gates.md`.

Install commands for Claude Code and Codex, including subsets, are in
`references/install.md`. Read it only when the user asks how to install,
update, or subset the pack. The Suede MCP's `suede_install_options` tool
answers the same question live when it is connected.

Use the Suede MCP only when it adds structure: listing skills, explaining
install options, scaffolding an SEO and AEO copy audit, or generating a QA
checklist. Skip it for small edits.

## Next move

Triggered by "what's next", "what should I do next", "recommend the next
move", "give me the prompt", or a stalled task after a review, audit, or plan.
Inspect read-only. Never execute the recommended action unless the user
separately authorizes it.

1. **Resolve the target and the done outcome** from the request, conversation,
   handoff, plan, repo, or live surface.
2. **Read only what can change the answer**, freshest first: `git -C <repo>
   status --short --branch`, `git -C <repo> log --oneline -5`, the named plan
   or handoff file at its exact path, and a live check
   (`curl -sS -o /dev/null -w '%{http_code}' <url>`) when a public surface is
   in scope.
3. **Generate 2 to 4 candidates.** Drop work already verified complete,
   adjacent cleanup, and anything outside the authorized scope. If the repo
   already has a plan, issue tracker, or board, treat its recorded next step
   as one candidate; never create a second tracker.
4. **Score each 0 to 2 per row** and pick the highest total:

| Criterion | 2 | 1 | 0 |
|---|---|---|---|
| Goal alignment | Produces the done signal | Required prerequisite | Adjacent |
| Unblocking | Clears a core path or 2+ steps | Clears one step | Clears nothing known |
| Evidence | Confirmed by current source | One read-only check away | Assumption |
| Urgency | Active failure, deadline, security risk, release gate | Needed this milestone | No pressure |
| Leverage | One focused session; prevents rework | Bounded, moderate payoff | Unscoped or low payoff |

5. **Break ties** toward the prerequisite, then current-evidence verification,
   then the more reversible action. Still within one point? Run up to three
   more read-only checks; if still tied, show both and name the one fact that
   decides.
6. **If missing evidence is the real blocker,** the smallest read-only check
   becomes the recommendation.

Output:

```text
Recommended action: <one sentence>
Why now: <one evidence-backed sentence>

Quick prompt: <2-4 runnable sentences naming the skill, target, outcome, and done signal>

Say "expand prompt" for the full operator version or "make it granular" for exact steps and commands.
```

The expanded and granular prompt formats are in
`references/next-action-prompts.md`; load it only when the user asks for them.
Show scores, evidence lists, or alternatives only when asked or when the tie
rule requires them. Never recommend "keep working" or "do more research": name
a command, artifact, decision, edit, or verification result.

## Closing

After meaningful work, close with a one-sentence plain explanation for a
non-coder, then Changed / Verification / Caveats / Status, then:

```text
Cue Suede:
1. Change something: tell me what to revise.
2. Preserve this: tell me what worked so I can match it.
3. Keep as-is: say nothing and I will treat it as accepted.
```

Never block completion waiting for that answer.

## Red flags: stop

- "I'll summarize the request for the specialist." Pass it verbatim.
- "This crosses three lanes; faster to do it inline." Crossing lanes is when
  this router earns its place.
- "The live URL is probably unchanged." Inspect before claiming.
- "I'll just do the recommended action too." Recommending is read-only.

## Boundaries

- Never expose private paths, credentials, secrets, unreleased assets, or
  private service details.
- Never copy protected site assets, exact copy, proprietary code, or
  trademarked identity during a restyle.
- Never mark work done until the done signal has been checked or the remaining
  caveat is named.
- Never mutate files, repos, deployments, accounts, or messages while
  recommending a next move.
