# Evergreen Technical Book Knowledge

Core concepts for keeping technical nonfiction useful as tools and platforms change.

## Overview

Technical books often need concrete details, but too many temporary details can make a book stale before word of mouth has time to compound. The durable version of a technical book teaches principles, tradeoffs, mental models, and reusable workflows while placing fast-changing walkthroughs in resources that can be updated.

This skill uses transformed guidance from practical nonfiction product-design methods. Do not copy source-book prose into user outputs.

## Key Concepts

### Content Half-Life

**Definition**: How long a piece of content is likely to remain accurate and useful.

Long half-life content belongs in the book. Short half-life content needs careful framing, updateable placement, or an edition plan.

### Durable Core

**Definition**: The concepts, decisions, patterns, and practices that support the book's promise even as tools change.

For a self-hosting book, this might include threat modeling, backup thinking, network mental models, ownership tradeoffs, and maintenance habits.

### Volatile Detail

**Definition**: A tool-specific, vendor-specific, version-specific, UI-specific, policy-specific, or price-specific detail likely to drift.

Volatile details can be useful, but should be short, clearly dated, or moved to companion resources.

### Companion Resource

**Definition**: An updateable artifact outside the stable manuscript.

Examples include scripts, checklists, templates, config repositories, videos, living setup guides, issue trackers, and versioned walkthroughs.

### Edition Strategy

**Definition**: The plan for when and how the book itself will be revised.

Some technical books should be evergreen with companion updates. Others should be explicit edition-based manuals.

### Stable Reference

**Definition**: A book reference to external material that remains understandable even if the target changes.

Stable references describe the resource purpose and path, not only a brittle deep link.

## Terminology

| Term | Definition |
|------|------------|
| Evergreen | Designed to remain useful for years. |
| Drift | Loss of accuracy caused by changing tools, vendors, interfaces, or norms. |
| Companion site | Updateable web home for volatile resources. |
| Last reviewed | Date or version marker showing when a resource was checked. |
| Update trigger | Condition that prompts a companion or edition update. |
| Durable example | Concrete example that illustrates a lasting pattern. |

## How It Relates To

- **Book TOC Lab**: Scope decisions determine which volatile details are excluded or moved.
- **Technical Book Lab Design**: Labs need enough concrete detail, but may delegate volatile variants.
- **Technical Manuscript Verification**: Verification finds current-info dependencies and drift.
- **Book Sales Optimization**: Companion resources can support lead capture or upsells, but must not make the book incomplete.

## Common Misconceptions

- **Myth**: Evergreen technical books should avoid tools.
  **Reality**: They should use tools as examples while teaching durable patterns.

- **Myth**: Moving details online means the book can be incomplete.
  **Reality**: The book must still deliver its core promise. Companion resources should update or extend value.

- **Myth**: A current screenshot is harmless.
  **Reality**: UI screenshots date quickly and can make otherwise durable advice look abandoned.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| Half-life | Estimate how fast content will age. |
| Durable core | Keep lasting concepts and decisions in the book. |
| Volatile detail | Move, date, or minimize fragile specifics. |
| Companion resource | Put updateable support outside the manuscript. |
| Edition strategy | Decide when the book itself changes. |
| Stable reference | Link by purpose, not brittle mechanics. |
