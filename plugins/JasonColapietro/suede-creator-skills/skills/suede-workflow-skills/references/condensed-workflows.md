# Condensed Workflows: umbrella-only fallback

Read this file **only when the individual Suede skills named in SKILL.md are
not installed**, for example the Codex install path that installs
`suede-workflow-skills` alone. When the pack is installed (Claude Code
`/plugin install suede-skills@suede`, `install.sh`, or the per-skill Codex
install), route to the named specialist instead: it owns the current version of
every method below and this file is a frozen, lossy summary of it.

Each section is the minimum viable version of one specialist's workflow.

## Contents

| Workflow | Owning skill when installed |
|---|---|
| [Suedify Workflow](#suedify-workflow) | `suede-design` (Restyle mode) |
| [Design Workflow](#design-workflow) | `suede-design` |
| [Component Lab Workflow](#component-lab-workflow) | `suede-component-lab` |
| [Interface Explanation Workflow](#interface-explanation-workflow) | `suede-interface-explain` |
| [Copy And SEO Workflow](#copy-and-seo-workflow) | `suede-copy`, `suede-seo-audit` |
| [Visibility Grading Workflow](#visibility-grading-workflow) | `suede-visibility-grader` |
| [Site Alchemy Workflow](#site-alchemy-workflow) | `suede-site-alchemy` |
| [Code Review Workflow](#code-review-workflow) | `suede-code` |
| [Agent Team Workflow](#agent-team-workflow) | `suede-agent-teams` |

The Gate policy, Core Rule and Boundaries in SKILL.md govern everything here.
Its general fix-loop cap applies to the other workflows. Interface validation
uses its stated exception: reproduce, make the authorized fix, recapture the
matched state, and inspect until the scoped outcome is verified or a concrete
blocker is identified. A fixed pass count cannot substitute for evidence.
Read-only interface reviews report findings without changing application files.

## Suedify Workflow

Use this when the user provides or implies:

```text
reference_url -> target_url
```

1. Capture the reference site's layout, hierarchy, spacing, typography, color
   roles, imagery, navigation, motion, proof structure, and mobile behavior.
2. Capture the target site's current approved content, brand assets, claims,
   routes, copy constraints and mobile behavior.
3. Map reference signals to target-safe equivalents. Do not copy proprietary
   code, logos, exact copy, private assets, fake proof, or unsupported claims.
4. Implement inside the target's existing framework, components, tokens, and
   routing patterns when possible. Preserve existing approved copy and claims;
   a restyle request does not authorize rewriting them. Change words only when
   the user has authorized that copy scope, following the approved-copy rules.
5. Verify desktop and mobile render, text fit, links, accessibility basics,
   build/test commands, and live route before calling the restyle done.

Output:

```text
Reference URL:
Target URL:
Fidelity level:
Changed:
Verification:
Unmatched reference signals:
Legal/brand caveats:
Status: ship | ship-with-caveats | hold
```

## Design Workflow

For design or frontend work:

1. Preserve the requested mode: a whole-flow review or UI diff review is
   read-only; an authorized build or fix may edit the agreed surface.
2. Identify the exact surface: repo/folder, route, live URL, branch, dirty
   files, and relevant local docs.
3. Decide the register: brand page, product UI, dashboard, campaign page,
   docs surface, or app workflow.
4. Name the user-visible job and primary action. Prioritize task completion,
   clarity and conversion hypotheses while preserving the current brand.
5. Check layout, typography, color, spacing, imagery, state coverage,
   responsiveness, accessibility basics, and copy fit.
6. Inspect available renders. For edits, compare before and after; for a
   review, inspect the current state without changing application source.
7. For major visual work, compare source visual truth and rendered
   implementation together, with matched viewport, state, theme, content, and
   auth conditions.

For a UI diff, resolve the requested base and head to exact available refs or
commit IDs. Record the comparison command, selected files and working-tree
inventory: staged, unstaged and untracked changes, plus any excluded paths.
Inspect both sides and the shared components and affected consumers before
attributing a finding. Classify each finding as introduced, regression,
pre-existing or attribution unknown. If a ref or comparison side is unavailable,
mark attribution unknown and state what could actually be inspected. Never
invent a ref or commit, silently substitute another base, or present a
working-tree-only observation as proof of a regression.

Major design work needs a compact contract:

```text
Objective:
Surface:
Done signal:
Constraints:
Lanes:
```

Source inspection alone never establishes a rendered visual pass. If the
browser or render is unavailable, report source-backed findings and mark the
visual checks as not observed. Treat predicted conversion effects as hypotheses
until a valid measurement supports them.

For a selected design or screenshot build, use an already available image-to-code
capability, or implement with the existing local stack and components. Do not
install a dependency or skill just to satisfy this routing fallback. An optional,
explicitly selected visual kit supplies references with recorded reuse rights;
preserve the target product's brand and approved assets.

For design-system work, capture at least the token map, component inventory,
state matrix, screenshot contract or preview board, asset register, migration
notes, and a scored quality audit when the scope is broad enough.

## Component Lab Workflow

Use for a dev-only component workbench, stress fixtures or live variants:

1. Inspect the existing component imports, providers, tokens and preview tooling.
2. Reuse that tooling; if it is unavailable, provide a local fixture plan and
   identify the missing runtime without installing dependencies automatically.
3. Before importing components or starting the preview server, inspect transitive
   imports, import-time module initializers, server-side actions, bootstrap hooks,
   storage and analytics clients. Establish isolation at those execution points
   with synthetic data, inert callbacks and existing safe substitutes. Exclude
   production credentials and records; disable payment, booking, lead submission,
   persistence and other outbound effects. Browser request-blocking alone is
   insufficient: effects can occur during import or server execution.
4. If any effect or required isolation remains unresolved, stop execution and
   report the exact blocker with a non-executing fixture plan. Only after
   verifying isolation, import the real components and start the preview in that
   isolated runtime. Never copy production logic into a substitute component to
   make a state appear covered.
5. Exercise supported empty, loading, error, long-content, disabled, narrow-screen
   and keyboard states. Keep design variants separate from behavior fixtures.
6. Keep the preview out of production routes and output. Verify that isolation
   from actual build configuration before describing it as development-only.
7. Report actual rendered observations, state coverage, untouched production
   behavior and remaining checks. A proposed fixture is not executed evidence.

## Interface Explanation Workflow

Use for a read-only explanation of how an existing interface works:

1. Identify the user's specific question and trace the relevant source files.
2. Map input, event handling, state changes, layout, rendering and outputs.
3. Cite concrete file locations for each mechanism claim and distinguish an
   inference from a source fact or a browser observation.
4. Inspect current behavior when available without changing application source,
   sending real transactions or creating a replacement implementation.
5. Return a concise causal explanation and any uncertainty. Use a diagram only
   if it clarifies the mechanism. Route requests for review to `suede-design`
   and requests for a state workbench to `suede-component-lab`.

## Copy And SEO Workflow

For public copy, docs, README, landing pages, skill pages, plugin listings, and
SEO passes, including AEO and AI EO:

1. Identify reader, page type, primary action, proof, and evidence boundaries.
2. Write the clearest outcome first.
3. Use concrete artifacts, commands, links, screenshots, files, or examples as
   proof.
4. Keep titles under 60 characters when practical and meta descriptions under
   160 characters when practical.
5. Check H1, headings, internal links, schema/JSON-LD, CTA clarity, FAQ fit,
   search intent, answer intent, and sourceable proof.
6. Remove generic AI phrasing, filler, vague claims, and unsupported promises.
7. Run the no-missed copy gate: cut formulaic structure, fake intensity,
   rhetorical setup, inanimate false agency, quote-bait lines, and detached
   business jargon while preserving true Suede specificity.

Full audit output:

```text
[HIGH|MEDIUM|LOW] Finding
Location:
Issue:
Fix:
Suggested copy:
Verification:

SEO title:
Meta description:
H1:
Subhead:
Primary CTA:
Internal links:
Schema changes:
Answer-ready summary:
Evidence boundaries:
Ship gate: ship | ship-with-caveats | hold
```

## Visibility Grading Workflow

For public pages, GitHub Pages sites, docs, campaign pages, launch pages, and
creator pages, use `suede-visibility-grader` when the question is whether the
right person or agent can find the page, understand it, trust it, cite it, and
take the next action.

Grade:

```text
Findability: A-F
First-screen clarity: A-F
CTA pull: A-F
Proof and trust: A-F
AI readability: A-F
Design signal: A-F
Overall: A-F
```

Treat the grade as an execution guide, not an audited traffic metric. Inspect
the live URL or source before grading and name anything that was not checked.
For public surfaces, visual evidence matters. Missing live/render inspection
caps promotion readiness, and broken CTA, false claim, inaccessible primary
action, or unresolved major design-signal failure can hold the page even when
metadata looks acceptable.

## Site Alchemy Workflow

For landing pages, campaign pages, product microsites, public repo pages, or
conversion surfaces:

1. Name one buyer, one offer, one proof stack, and one action.
2. Rewrite the hero before touching decorative details.
3. Build a CTA ladder: primary action, proof/docs action, and next-step action.
4. Improve section rhythm, mobile composition, text fit, and link clarity.
5. Run a link sweep and verify the live or local rendered page before shipping.

Use these named moves as notes, not shell commands:

- `/vibe-scan`
- `/hero-voltage`
- `/offer-spine`
- `/proof-stack`
- `/cta-magnet`
- `/mobile-seduction`
- `/ship-polish`

## Code Review Workflow

For code, docs, plugin, MCP, or public-site changes:

1. Build a context graph: changed files, callers, routes, data flow, configs,
   docs, tests, generated files, and runtime surfaces.
2. Review for production behavior, security, published-statement accuracy, regression
   risk, missing tests, broken install paths, stale docs, and deploy gaps.
3. Lead with findings ordered by severity.

Finding format:

```text
P0/P1/P2/P3 - Title
File/route:
Evidence:
Impact:
Fix:
Verification:
Confidence:
```

Ship gate:

- `ship`: required verification passed and no known blocker remains.
- `ship-with-caveats`: no blocker remains, but caveats are named.
- `hold`: blocker or high-risk unknown remains.

For important work, include a Suede A-F code grade:

```text
Code grade:
Correctness: A-F
Security and permissions: A-F
Data and state: A-F
Suede truth: A-F
UX and release behavior: A-F
Tests and verification: A-F
Deploy readiness: A-F
Overall: A-F
```

When the user asks for a grade more than a full findings report, route to
`suede-code --grade-only` and include the explanation for why the grade landed there.

## Agent Team Workflow

Use team lanes for large, risky, cross-surface, public, design-heavy, or
release-bound work. Use the max-agent loop when the user asks for it or the
task needs continuous quality gates, evals, recovery controls, and release
truth.

When the user explicitly asks for max effort, max agents, max agent teams,
spare no compute, or to fix everything, freeze authority before spawning
anything: one controller lane owns the plan and the progress store, every
other lane subordinates to it, and no lane creates a competing team protocol
or promises access to a hidden token counter.

Define:

```text
Objective:
Target:
Constraints:
Lane Map:
Dependency Order:
Done Signal:
Ship Gate:
```

Useful grouping loops:

- Linear delivery loop: scout, plan, build, verify, review, ship.
- Continuous PR loop: branch/PR/CI/review/release control for public or risky
  work.
- RFC/DAG loop: decompose broad work into ordered decisions and atomic tasks
  before implementation.
- Exploratory parallel loop: run independent approaches or audits in parallel
  only when file ownership does not collide.
- Parallel surface loop: split lanes only when file ownership does not collide.
- Scout and constraints loop: map docs, WIP, risky files, live routes, owners,
  and no-touch boundaries before edits.
- Adversarial review loop: one lane tries to break the work from production,
  user, release, published-statement, and abuse angles before release.
- Consensus review loop: two review lenses merge blockers, caveats, and fixes.
- Design and visibility loop: rendered QA plus A-F page visibility grading.
- Code grade loop: A-F code grade plus fix briefs for weak lanes.
- WIP protection loop: claim allowed files and sequence lanes that collide.
- Release lock loop: build, deploy, live/API readback, claim truth, handoff.
- Recovery loop: isolate a failed check, patch the gap, rerun the failed check.
- Evidence handoff loop: gather screenshots, commands, URLs, caveats, and next
  action for the next agent.
