---
name: sealos-app-builder
description: Build, adapt, and document apps that run inside Sealos Desktop using the Sealos app SDK. Use when creating a new Sealos app, integrating an existing web app into Sealos Desktop, wiring Sealos session data into business features, preparing local iframe-based debugging, or producing beginner-friendly Sealos app tutorials and starter implementations. Also triggers on "/sealos-app-builder".
---

# Sealos App Builder

## Overview

Use this skill to turn a generic web app into a Sealos app that runs inside Sealos Desktop, or to scaffold a new Sealos app from scratch. Focus on the repeatable parts: SDK initialization, session access, language sync, business-data integration, local debugging through a Desktop test app, and publish readiness.

Prefer a simple, teachable implementation that a beginner can understand and extend.

## Core Workflow

### 1. Identify the starting point

Classify the request into one of these paths:

1. Create a new Sealos app from scratch.
2. Adapt an existing web app to run inside Sealos Desktop.
3. Add Sealos identity and business-data integration to an app that already renders.
4. Produce documentation or a tutorial instead of code changes.

If the repository already contains Sealos-related code, inspect local sources first. In particular:

1. Look for `packages/client-sdk` or equivalent SDK sources.
2. Look for existing provider apps under `providers/` or similar directories.
3. Reuse the repository's established framework and routing patterns when they are already in place.

If the repository does not contain local Sealos sources, use the bundled references in this skill as the baseline.

### 2. Integrate the Sealos app SDK

Treat Sealos Desktop integration as a root-level concern.

Before using any starter template, install the SDK first:

```bash
pnpm add @labring/sealos-desktop-sdk
```

Use `npm install @labring/sealos-desktop-sdk` or `yarn add @labring/sealos-desktop-sdk` when the project uses a different package manager.

1. Initialize the SDK once in a client-only root component.
2. Fetch `getSession()` and `getLanguage()` early.
3. Store session, language, loading state, and desktop availability in a shared context or store.
4. Listen for language changes through `EVENT_NAME.CHANGE_I18N` when the app needs runtime language sync.
5. Add a graceful fallback when the app is opened outside Sealos Desktop.

Read [references/minimal-app-template.md](references/minimal-app-template.md) before implementing the root integration.
If the app uses Next.js App Router, also read [references/nextjs-app-router.md](references/nextjs-app-router.md).

Use one of these starter templates:

1. [assets/templates/react/sealos-provider.tsx](assets/templates/react/sealos-provider.tsx) for React.
2. [assets/templates/vue/use-sealos.ts](assets/templates/vue/use-sealos.ts) for Vue.

### 3. Connect Sealos identity to business data

For most apps, the key integration is not the iframe itself but the user mapping.

1. Use `session.user.id` as the stable app-level user identifier.
2. Persist display-friendly fields such as `name`, `avatar`, `k8sUsername`, and `nsid` when useful.
3. Keep business data in the app's own database and API routes.
4. Model Sealos user identity as input to your business logic, not as your entire backend.

Read [references/data-integration-patterns.md](references/data-integration-patterns.md) when you need schema or API guidance.

### 4. Prepare local debugging in the real runtime

Do not assume a successful browser render means Sealos integration works.

The app usually needs to be opened by Sealos Desktop in an iframe for SDK calls like `getSession()` to succeed. When local debugging is part of the task, read [references/local-debug-and-test-app.md](references/local-debug-and-test-app.md).

Use these rules:

1. Explain clearly when a page is outside Sealos Desktop.
2. Prefer a test app inside Sealos Desktop for end-to-end verification.
3. Avoid server-side SDK calls.

### 5. Prepare for publishing

When the user wants deployment or launch readiness:

1. Verify environment variables.
2. Verify database connectivity and migrations.
3. Confirm the app works when launched from Sealos Desktop.
4. Confirm any cross-app navigation or event usage is valid.
5. Summarize the remaining manual registration or platform configuration steps.

Use [references/publish-checklist.md](references/publish-checklist.md) as the release checklist.

## Implementation Rules

### Keep the integration simple

Default to the smallest viable Sealos integration:

1. One root provider or store.
2. One business identity mapping pattern.
3. One fallback path for non-Desktop access.

Avoid spreading SDK initialization across multiple pages or components.

### Prefer the repository's real SDK surface

If the current workspace contains actual Sealos SDK sources or existing Sealos apps:

1. Inspect those sources.
2. Follow the real exported APIs and types.
3. Call out repository-specific differences from generic examples.

### Use the official SDK package name

Use `@labring/sealos-desktop-sdk` in generated examples and starter code by default.

Only deviate from that if the target repository already has an established local workspace alias and the user explicitly wants to preserve it.

## Decision Guide

### If the user asks for "How do I build a Sealos app?"

Provide:

1. A short explanation of the runtime model.
2. A minimal SDK integration example.
3. A business-data mapping example.
4. Local debugging guidance through a Sealos Desktop test app.

### If the user asks to modify an existing app

Do this order:

1. Inspect the current app entry point.
2. Add or refactor a single root Sealos provider.
3. Wire business APIs to `session.user.id`.
4. Verify fallback behavior outside Desktop.

### If the user asks for documentation or a tutorial

Structure the output around:

1. What a Sealos app is.
2. How to initialize the SDK.
3. How to obtain and use the session.
4. How to integrate business data.
5. How to debug through a Desktop test app.
6. How to publish and verify.

## References

Read only the files needed for the task:

1. [references/sdk-capabilities.md](references/sdk-capabilities.md) for available SDK APIs and runtime behavior.
2. [references/minimal-app-template.md](references/minimal-app-template.md) for the recommended root integration pattern.
3. [references/nextjs-app-router.md](references/nextjs-app-router.md) for a concrete Next.js App Router placement example.
4. [references/data-integration-patterns.md](references/data-integration-patterns.md) for user mapping, database schemas, and API shapes.
5. [references/local-debug-and-test-app.md](references/local-debug-and-test-app.md) for iframe-based debugging and Desktop test app setup.
6. [references/publish-checklist.md](references/publish-checklist.md) for launch-readiness steps.
