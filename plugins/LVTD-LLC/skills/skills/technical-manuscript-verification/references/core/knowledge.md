# Technical Manuscript Verification Knowledge

Core concepts for verifying technical nonfiction before readers depend on it.

## Overview

Technical manuscripts fail when hidden assumptions meet real reader environments. Verification turns instructions, claims, configs, screenshots, and examples into checkable artifacts so the author can fix blockers before beta readers or buyers encounter them.

This skill uses transformed guidance from practical nonfiction product-design methods. Do not copy source-book prose into user outputs.

## Key Concepts

### Verification Item

**Definition**: Any manuscript element that can be checked for technical correctness.

Examples include commands, code snippets, config blocks, file paths, ports, URLs, screenshots, diagrams, version claims, package names, and security advice.

### Evidence Standard

**Definition**: The level of proof required before saying an item works.

Standards range from "ran successfully in a clean environment" to "needs primary-source confirmation." Higher-risk items require stronger evidence.

### Environment Matrix

**Definition**: The supported combinations of operating system, architecture, tool versions, hosting provider, package manager, hardware, or network conditions.

The matrix can be small, but it must be explicit.

### Reproducibility Gap

**Definition**: A place where readers cannot reproduce the author's result from the manuscript alone.

Gaps often come from missing prerequisites, implicit local state, secrets, version drift, or skipped verification output.

### Safety-Critical Step

**Definition**: A step that can expose data, weaken security, break a system, spend money, delete state, change permissions, or create maintenance obligations.

Safety-critical steps require warnings, rollback, and strong verification.

### Current-Info Dependency

**Definition**: A claim or instruction likely to change as tools, vendors, pricing, interfaces, policies, or APIs change.

These items should be checked against current primary sources and often moved to companion resources.

## Terminology

| Term | Definition |
|------|------------|
| Clean run | Verification from a fresh environment, not the author's already-configured machine. |
| Expected output | What the reader should see after a command or action. |
| Primary source | Official documentation, repository, API docs, or vendor page. |
| Untested | Not checked in the current pass. |
| Known-good | Verified under named conditions. |
| Drift | Difference caused by changes in software, services, docs, UI, or policies. |

## How It Relates To

- **Technical Book Lab Design**: Lab design creates checkpoints; verification tests them.
- **Evergreen Technical Book**: Volatile verified details may belong in companion resources.
- **Beta Reader Feedback**: Verification reduces avoidable failures so beta readers can reveal reader-experience problems.
- **Self-Publishing Production**: Final production should preserve verified code blocks, screenshots, links, and diagrams.

## Common Misconceptions

- **Myth**: Expert review is enough.
  **Reality**: Experts catch conceptual errors, but runnable instructions still need execution or artifact checks.

- **Myth**: A command is safe because it is common.
  **Reality**: Common commands can be dangerous in the wrong directory, user, host, or network context.

- **Myth**: Screenshots prove the text is accurate.
  **Reality**: Screenshots can drift from tool UIs and must match the surrounding instructions.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| Verification item | Anything technical that can be checked. |
| Evidence standard | Proof required before claiming it works. |
| Environment matrix | The conditions under which instructions are supported. |
| Reproducibility gap | Missing state that blocks real readers. |
| Safety-critical step | Higher-risk action needing warning and rollback. |
| Current-info dependency | Detail likely to drift and needing current sources. |
