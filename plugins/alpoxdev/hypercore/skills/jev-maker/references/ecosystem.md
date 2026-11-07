# Ecosystem

Where this package sits, as of 2026-10-01. Three things are described below: the vendor's own agent
skill, the community skills that surround the same model, and what this package delivers.

The landscape is written from what is stored in this package: the vendor's page on its own skill, and
a search of public skill repositories done on 2026-10-01 whose results were not stored here. Community skills are named as leads,
never as requirements, and nothing here is a dependency.

Label for every community item: **community, not required, inspiration only**.

## Contents

- The official skill
- Community skills
- What this package delivers
- How to read this landscape
- Unverified items
- Sources

## The official skill

The vendor documents a TypeSafe skill in the `typesafe-ai` folder of the `typesafe-ai/skills`
repository, and the install command on the vendor's page is:

```bash
npx skills add typesafe-ai/skills --skill typesafe-ai
```

The installer asks which agent to target and installs project-local by default; a global install is a
flag away. A plugin path and a manual copy exist as alternates, and the page asks for exactly one
installation method so an agent does not end up with duplicate copies. A stale copy is named on that
page as a possible cause of an agent inventing request or response fields.

What it carries: the three question types, the architectural patterns for composing them, and guidance
on structuring evaluations. It is an orientation and design aid, and it asks the reader to open the live
documentation while working, which is the right instinct and also the reason it moves with the vendor's
site.

Two habits from that page are kept in this package: the questions and the thresholds belong in a single
file a person can review, and a first draft of a question set is expected to be edited rather than
accepted.

## Community skills

The 2026-10-01 search of public skill repositories whose results were not saved here returned a set of
community skills around the same model. They are grouped into six families below as an unverified
hypothesis, not as a confirmed taxonomy. Representative names are listed as they were recorded;
repository locations were not saved into this package, so none is asserted here.

| Family | Representative names | Repository | Status |
| --- | --- | --- | --- |
| Design guidance | `system-one`, `building-with-typesafe-jev` | not captured in this package | unverified |
| Question generation | `grill-jev` | not captured in this package | unverified |
| Classification templates | `jev-triage` | not captured in this package | unverified |
| Evaluation and audit | `jev-eval`, `jev-avaliar`, `jev-audit` | not captured in this package | unverified |
| Agent-harness connectors | no name captured | not captured in this package | unverified |
| Domain-specific | no name captured | not captured in this package | unverified |

What each family seems to do, as an unverified hypothesis from that search rather than a confirmed
description:

- **Design guidance** explains when the model is the right tool and how to split a feature between code
  and a judgment call.
- **Question generation** drafts question sets and criteria, which overlaps with the `questions` mode in
  this package.
- **Classification templates** show a worked classification, usually a routing or triage case, as an
  example to copy.
- **Evaluation and audit** covers measuring a question set and hunting for calls that could be replaced.
  It is methodology, not tooling.
- **Agent-harness connectors** attach the model to a coding agent or an agent framework, which is a
  different problem from producing request files.
- **Domain-specific** skills pick one industry or document type and write the questions for it.

None of the names above is required, endorsed, or checked for currency. They are listed so a request
that mentions one is recognized.

## What this package delivers

This package ships the artifacts a project needs to start:

- It writes files: a request JSON, a constants file, caller code for the chosen route and language, a
  fill-in template set, an evaluation case skeleton, and an audit table.
- It decides by artifact first. The mode is read from what the user wants to open, not from a keyword,
  and the fit gate runs before anything is generated, so a request that plain code answers is answered
  with plain code.
- It checks the request offline. The checker catches the shape errors that would otherwise come back as
  a rejected call, and it needs no key and no network.
- It keeps the volatile facts in one dated place. Prices, limits, endpoints, and aliases are held in
  [`./official/jev-platform.md`](./official/jev-platform.md) and [`./providers.md`](./providers.md)
  rather than scattered through the generated code.
- It is read-only where that is the right answer. The audit mode produces a ranked table and changes
  nothing in the audited tree.

The overlap with the design-guidance family is deliberate and shallow: this package links to the
snapshot for what the model can and cannot do instead of restating it, and spends its length on the
generated artifact.

## How to read this landscape

Names on this page are leads, not dependencies. A skill listed here may be unmaintained, may disagree
with the current vendor documentation, and may be written for a version of the model that no longer
exists. Read the vendor page before adopting anyone's advice about a request field.

Popularity numbers on a repository page, including star counts, are not used as a selection signal
here. What is used instead is whether a skill produces the artifact in hand and whether its advice
matches the vendor's current page.

Nothing on this page is a dependency of this package. This package runs on its own files.

## Unverified items

Recorded so they are not mistaken for confirmed facts later:

- **Community skill names and repositories.** The names above come from that search on 2026-10-01. No search result, page, or repository listing for them was saved into this package, so
  each row is marked unverified and no repository location is claimed.
- **Counts of community skills.** No count is quoted anywhere in this package. Any number seen elsewhere
  should be treated as a snapshot of one search on one day.
- **Popularity and maintenance claims.** Star counts, download counts, and "actively maintained"
  statements were not checked and are not relied on.
- **Client package versions.** The versions of the client packages that wrap the same model were not
  verified against a package registry. A calling project should pin whatever version it installs rather
  than trusting a number seen in a document.
- **Helper coverage in the client packages.** Which question types each client package offers a helper
  for was only partly confirmed by the pages saved here, so generated code should not assume that every
  question type has a helper.
- **Anything about a route that is not in [`./providers.md`](./providers.md).** A route without a
  verified row there gets no generated code, and no claim is made about it here.

## Sources

> Links checked 2026-10-01.

| Claim | Source |
| --- | --- |
| The official skill's location, its install commands, what it carries, the single-installation rule, the stale-copy failure, and the single-constants-file habit | <https://docs.typesafe.ai/agent-skill.md> |
| The question types and the architectural patterns the official skill covers | <https://docs.typesafe.ai/primitives> and <https://docs.typesafe.ai/concepts/how-to-build-with-system-one> |
| The community skill families and the representative names listed above | a public repository search on 2026-10-01; no source page saved |
| The delivery statement, the artifact list, and the audit scope | this package's own rules and procedures, [`../rules/modes-and-routing.md`](../rules/modes-and-routing.md) |
| The routes that carry a verified contract, and the rule that others get no generated code | [`./providers.md`](./providers.md) |

### Evidence grade

`VENDOR` for the official skill section: location, install commands, scope, and the two working habits
all come from the vendor page named above, captured on 2026-10-01.

`UNVERIFIED` for the community section, and only as a list of names. The families and the representative
skills came from that 2026-10-01 search, whose results were not saved into this package. No
repository was confirmed, nothing was read end to end, and no popularity or maintenance claim is made.
Every community row is marked unverified for exactly that reason.

`LOCAL` for the delivery statement, which describes what this package does.

Not evidenced here, and deliberately absent: prices, rate limits, context budgets, endpoint names, and
the model alias table. They belong to [`./official/jev-platform.md`](./official/jev-platform.md), behind
a review date.
