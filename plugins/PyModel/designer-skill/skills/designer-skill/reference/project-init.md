# Project Init

Optional project-context setup, only when requested or when the user authorizes documentation changes. Missing PRODUCT.md never blocks a bounded UI repair. Read-only audits and plans do not authorize implementation or context-file mutation.

## 1. Inspect existing evidence

Read existing PRODUCT.md, DESIGN.md, tokens, components, manifests and approved assets relevant to the requested setup. The loader searches the project root, `.agents/context/` and `docs/`; read each document independently. It does not rename legacy files or migrate them. If `.designer-skill.md` contains useful older context, read it and propose an explicit migration only when authorized.

Preserve existing files and concurrent work. If the user requests refresh, clarify which information should change rather than rewriting valid context. A discovered framework/component/icon system stays in place unless migration is part of the task.

## 2. Resolve material unknowns

Infer facts from the codebase and label uncertain hypotheses. Ask only what cannot be established and matters to this setup, using the host's discovered question tool or ordinary chat. Established users/purpose/identity need no redundant confirmation round.

Useful questions when evidence is absent:
- Is the primary surface brand-led marketing or a task-led product? Mixed products can record both per surface.
- Who uses it, in what context, and what outcome matters?
- What approved identity, voice, references and anti-references apply?
- Which accessibility requirements or known needs must be met?

A proposed brand is not an observed fact. When direction is unresolved, present a proposal and obtain the needed decision before recording it as approved. A user may explicitly delegate that choice.

## 3. Write only authorized context

PRODUCT.md records strategic evidence; DESIGN.md records observed visual contracts or clearly labeled proposals. Link canonical sources instead of maintaining independently editable copies of tokens.

Example PRODUCT.md outline (fill with real evidence, omit unknown sections or label them pending):

```markdown
# Product
## Register
product
## Users
## Product Purpose
## Brand Personality
## Design Principles
## Accessibility & Inclusion
```

For DESIGN.md use `refactor-and-redesign` §6. Include token/component source locations, behavior, supported environments and approved decisions. Do not claim an unrendered system was verified.

Context-file writes stay inside authorized scope. Setup does not authorize framework configuration, dependency installs, CSP changes or launching a server. This release uses ordinary source variants and the host's browser/native preview; it creates no live-helper config. Existing user-owned live config is left untouched.

## 4. Wrap up

Report files changed, established facts, pending decisions and verification gaps. Suggest one or two relevant canonical verbs from `scripts/command-metadata.json` or `list_commands`, not a separate command vocabulary. Optional follow-up documentation is a proposal, not a setup prerequisite for unrelated work.
