# Intake and Questions

Use this rule before the first question. It owns the platform and size judgment, the explore-first order, the question budget and format, and the defaults that are never worth asking about.

## 1. Decide the platform first

Target platforms are `web`, `ios`, `android`, `desktop`. More than one is normal. Decide from the request and the evidence, not from a template default.

| Signal | Platform |
|---|---|
| Browser, URL, responsive layout, SEO, session in a tab | `web` |
| App Store, TestFlight, an iPhone or iPad build | `ios` |
| Play Store, an APK or AAB, an Android tablet build | `android` |
| An installed application, tray icon, installer, auto-update, notarization, code signing | `desktop` |

Record the decision in the meta block with a one-line reason, for example `platforms: web, ios - the request names a browser product and an App Store release`. When the request is genuinely ambiguous between two platforms and the answer changes the scope materially, that is one question, not a guess buried in the document.

A platform decision is not a checklist. The platform block in `prd.md` records the decided platform and its open obligations; a platform checklist fills that block when one exists.

## 2. Decide the size

| Size | Use when | Effect on the document |
|---|---|---|
| `S` | One feature or one behavior change inside an existing product; one user-visible outcome; no new surface | One goal, one or two stories, a short requirement list, no P2/P3 sections unless they carry real scope |
| `M` | A new product surface or a multi-step flow; several stories that can ship in sequence | Full section set, P1/P2/P3 stories, several requirements, platform blocks for each decided platform |
| `L` | A new product, several platforms, or a change that alters the product model | Full section set plus explicit risks, dependencies, and the must-not-change behavior |

Record the size with a one-line reason: `size: S - one settings screen changes an existing flow`. When two sizes fit, take the smaller one. An oversized document is a defect: the failure mode this skill exists to avoid is a workflow that treats every idea like a product launch.

## 3. Explore before asking

Read, in this order, until the question would be answered:

1. the repository: existing product docs, README, configuration that names platforms or constraints
2. existing documents under `.hyper/prd/` for the same product, to avoid contradicting a decided PRD
3. the context the user pasted, including links, screenshots described in text, and prior conversation

Never ask what these sources answer. If a source answers part of a question, ask only the remainder. If two sources disagree, that disagreement is a finding for the document's open questions, not a question to the user unless it blocks scope.

## 4. Question budget and format

| Size | Questions |
|---|---|
| `S` | `S 1` |
| `M` | `M 3` |
| `L` | `L 5` |

Rules for every question:

- One question at a time. Never a numbered list of questions in one message.
- Two to five options, each concrete enough to choose without a follow-up.
- Exactly one option marked as recommended, with a one-sentence reason.
- Ask only what the user alone can decide: business priority, target audience, pricing intent, legal posture, launch scope, a tradeoff between two acceptable outcomes.
- Do not ask what the document can state as an assumption. If the answer is derivable from convention, take the convention and mark it.
- Silence, "알아서", "적당히", or an answer that does not pick an option means: take the recommended option, record it as `[가정: …]`, and continue. Do not re-ask. The marker sits in the sentence that uses the value: a value chosen by silence is never written as fact, even in a section far from the question.
- A question left unanswered and blocking (the document cannot be scoped without it) keeps `status: draft` and appears in the open questions section with the answerer named.

## 5. Defaults that are not worth asking

Take these unless the request contradicts them, and record the choice as an assumption only when it changes scope:

- language of the document body: the user's language, otherwise Korean
- slug: kebab-case from the product or feature name
- file location: `.hyper/prd/<slug>/prd.md`
- section order: the template order
- status: `draft` until the checklist passes with no blocking question
- priority scale: `P0` for a requirement without which the goal fails, `P1` for the first shippable scope, `P2` for a later requirement
- metric measurement time: the first measurement window the product can realistically observe, stated explicitly rather than left blank
- platform checklist content: recorded as an open obligation, never invented

## 6. Report the intake

Before writing sections, state in one short block: platforms with reason, size with reason, how many questions the budget allows, and which sources were read. This block goes into the meta area of `prd.md`, not into a separate file.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| A bounded question count instead of an open interview | [snarktank/ai-dev-tasks create-prd](https://raw.githubusercontent.com/snarktank/ai-dev-tasks/main/create-prd.md) - "Limit questions to 3-5 critical gaps in understanding." |
| One question at a time and a session-wide cap | [spec-kit clarify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/clarify.md) - "Maximum of 5 total questions across the whole session." / "Present EXACTLY ONE question at a time." |
| A list of reasonable defaults that should not be asked about | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "Examples of reasonable defaults (don't ask about these)" |
| Discover facts instead of asking for them | [OpenAI Codex plan template](https://raw.githubusercontent.com/openai/codex/main/codex-rs/collaboration-mode-templates/templates/plan.md) - "Eliminate unknowns in the prompt by discovering facts, not by asking the user." |
| Ask only what changes the architecture or the decision | [Citadel prd](https://github.com/SethGammon/Citadel) - "Ask up to 3 questions — only those that would change the architecture." |
| Platform-specific obligations belong in the PRD from the start | [strvcom flutter-template prd](https://github.com/strvcom/flutter-template) |
| A document proportional to the problem | [Martin Fowler, SDD tool comparison](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) - "it quickly became clear that the workflow was like using a sledgehammer to crack a nut" |

### Evidence grade

`LOCAL` - the platform table, the size table, and the defaults list are this package's design. The `S 1, M 3, L 5` budget is a chosen value assembled from the cited caps, not a measured optimum.
