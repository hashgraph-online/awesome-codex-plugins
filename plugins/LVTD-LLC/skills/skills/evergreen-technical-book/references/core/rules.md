# Evergreen Technical Book Rules

Use these rules when scoping or revising technical nonfiction for durability.

## Core Rules

### 1. Protect The Durable Promise

The book should solve a reader problem that remains valuable beyond a tool cycle.

- Frame the promise around reader capability, not one vendor UI.
- Teach why decisions matter, not only which button to click.
- Keep examples concrete enough to act on.

### 2. Classify By Content Half-Life

For each section, ask how quickly it can become wrong.

- Durable: principles, tradeoffs, patterns, checklists, failure modes.
- Semi-durable: workflows, examples, config shapes, architecture patterns.
- Volatile: UI steps, prices, package versions, cloud limits, vendor policies, screenshots.

### 3. Move Volatile Detail Deliberately

Do not leave fragile detail in the book by accident.

- Keep volatile detail only when it is essential, brief, and valuable now.
- Move tool walkthroughs, setup screens, and version-specific variants to companion resources.
- Mark last-reviewed dates or version targets where appropriate.

### 4. Keep The Book Complete

Companion resources should not withhold the core promise.

- The book must explain the model, path, decisions, and safety boundaries.
- Companion resources can provide scripts, templates, updated screenshots, checklists, videos, and variants.
- Do not turn the book into a teaser for the companion site.

### 5. Design Stable References

External references should survive change.

- Prefer a stable resource page or repository over many fragile deep links.
- Explain what the reader will find there.
- Include search terms or navigation hints when direct URLs may change.

### 6. Create An Update Policy

Durability needs maintenance.

- Define review cadence.
- Define update triggers.
- Define who owns updates.
- Track last-reviewed dates.
- Accept that some books need new editions.

## Guidelines

- Use one canonical companion home for the book.
- Keep volatile links in one list when possible.
- Use versioned sample configs.
- Prefer diagrams of concepts over screenshots of changing UIs.
- Keep reader safety warnings in the book, even when commands live elsewhere.
- Preserve cut volatile content as marketing or companion material.

## Exceptions

- **Edition-based manuals**: A book may intentionally target a specific version. Put that in the title, subtitle, or introduction.
- **Compliance or legal books**: Current details may be the value. Plan frequent editions or subscription updates.
- **Beginner books**: Some screenshots may be worth the drift risk if they reduce fear, but keep them sparse.

## Quick Reference

| Rule | Summary |
|------|---------|
| Durable promise | Sell lasting reader capability. |
| Half-life | Classify how fast content ages. |
| Volatile moves | Put fragile steps where they can update. |
| Complete book | Do not hide the core promise online. |
| Stable references | Link to durable homes and explain purpose. |
| Update policy | Define review cadence and triggers. |
