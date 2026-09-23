---
name: dev-design-context
description: 'Establish or update persistent product and visual design guidance in .design-context.md. Use for initial design setup, a deliberate design-direction reset, or explicit 设计上下文 requests. Discover existing users, components, tokens, assets, and constraints before asking about material gaps. Does not implement UI; ordinary UI work does not require repeating this setup.'
---

# Dev Design Context

Persist the project-specific design decisions future UI work needs. Read [references/dev-baseline.md](references/dev-baseline.md). This skill writes design guidance, not application code, mockups, or implementation reviews.

## Establish what is already known

Read existing `.design-context.md`, product/brand documentation, representative screens, reusable components, design tokens, and actual assets. Inspect relevant paths rather than cataloging every style declaration. Distinguish deliberate conventions from isolated inconsistencies or legacy accidents.

Capture the audience and their recurring tasks, product context, visual hierarchy, typography, color roles, layout density, component patterns, asset identity, supported devices, and interaction/accessibility constraints where evidenced. Reference source paths so future agents can find authoritative tokens and components rather than duplicating them.

An existing valid design context usually needs no update. An absent `.design-context.md` does not block implementation when existing instructions, code, or supplied designs already establish the direction.

## Resolve material gaps

Ask only what affects the design and cannot be inferred: a conflicting audience, undefined brand constraints, a major direction change, target device needs, or an explicit accessibility requirement. Use focused questions, not a fixed questionnaire or mandatory three-word personality exercise.

Choose reversible details from established conventions and record consequential assumptions. Do not invent a brand direction unsupported by the brief, and do not label accessibility compliance as achieved without evidence. References describe intent; copying arbitrary reference styling is not a substitute for understanding the product.

## Write the reusable context

Default output is `.design-context.md` in the project root. If it exists, update its `## Design Context` section in place, preserving unrelated content. Follow a user-specified destination or chat-only instruction instead when present.

Include only sections that guide actual decisions:

```markdown
## Design Context

### Users and tasks
<Audience, context of use, and recurring workflows>

### Product and brand
<Supported voice, identity, and visual constraints>

### Existing design system
<Authoritative tokens, components, assets, and relevant source paths>

### Design direction
<Hierarchy, density, typography, color roles, imagery, responsive and motion expectations>

### Design principles
<Concrete project-specific rules and the decisions they guide>

### Open assumptions
<Material unresolved assumptions only; omit if none>
```

Keep guidance concise and evidence-based; avoid universal design advice, invented requirements, task checklists, or duplicate token tables that will drift. Update another assistant configuration such as `.github/copilot-instructions.md` only when that destination is requested; do not add an unsolicited synchronization question.

Re-read the result to check consistency with the sources and the user's direction. Report the path and the principles that materially guide future work, plus remaining uncertainty. Do not claim UI parity, responsiveness, or accessibility from a documentation edit alone.

## Multi-Agent Profile

Recommended agent_type: explorer

When delegation is available and authorized, a bounded explorer can inspect components, tokens, assets, and representative screens and return facts with source paths. One agent owns user questions and the final context file. In the source repository, `docs/multi-agent-policy.md` is optional guidance, not a required standalone resource.
