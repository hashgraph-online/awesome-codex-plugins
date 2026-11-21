---
name: build
description: Build or modify Bifrost apps, workflows, forms, agents, tables, managed files, configs, integrations, events, and related platform resources. Use for independent or Solution-owned V2 Apps, loose instance _repo/v1 content, local preview and testing, deployment planning, or MCP-only Bifrost work. Covers instance and install targeting, source ownership, access controls, testing, app design and theming, visual QA, and deployment handoff.
---

# Bifrost Build

## Overview

Bifrost is an open-source platform for building apps, workflows, forms, and agents, with foundational features such as managed tables and files. Use this skill to plan, build, test, preview, and deploy work on the Bifrost platform.

Follow the process below for every task. Load only the references routed for the current artifact.

## Prerequisites

These App and Solution workflows require Bifrost CLI 1.2.3 or newer. The selected
instance may enforce a newer minimum through `/api/version`; when the CLI gate
blocks, install the CLI served by that instance before continuing.

Confirm the CLI exists and inspect the connection from the directory where commands will run:

```bash
command -v bifrost
bifrost auth default
```

If the CLI or authentication is not configured, route the user to `bifrost:setup`.

A sandbox may be unable to read the host credential store. If authentication appears absent, repeat the read-only `bifrost auth default` check with host access before asking the user to log in again.

## Required process

### 1. Choose the working model and target

First choose which of four working models owns the change. `Workspace` here means the selected instance's loose `_repo` source and live loose entities; it does not mean global entity scope.

| Working model | Use it when | Authoring and lifecycle | Read next |
|---|---|---|---|
| **Workspace** | Maintaining a v1 app, building a loose workflow/entity, or intentionally creating source/resources shared at the instance level | Edit `_repo` source with `bifrost files`; create and mutate its scoped entity records directly with dedicated CLI commands. Commands target the selected instance directly; v1 app source remains draft until published. | `references/repository.md` |
| **App** | Building one normal Vite/React App in its own git repository while workflows, tables, files, configs, and integrations remain live platform resources | Create or bind with `bifrost app create` / `app bind`; develop with `bifrost app start`; deliver only the App bundle with `bifrost app deploy`. Source stays local and never enters `_repo` or a manifest. | `references/apps-independent.md` |
| **Solution** | Building a cohesive, portable, versioned app or automation package that should own and deploy its definitions together | Edit local source and `.bifrost` manifests; preview with `bifrost solution start`; deliver with `bifrost solution deploy`. Keep `allow_outbound_access: false`. | `references/solutions.md` |
| **Solution supported by the Workspace** | A Solution intentionally depends on eligible shared `_repo` modules, registered loose workflows, tables, or files | Author and deploy Solution-owned definitions locally, but manage each shared Workspace dependency separately through its own CLI/file path. Set `allow_outbound_access: true`; this adds runtime fallback, not ownership or permission. | `references/solutions.md` and `references/solution-resource-access.md` |

Use `bifrost.solution.yaml` at the project root as the Solution ownership marker. If it exists, inspect `allow_outbound_access` and `allow_inbound_access` to distinguish the two Solution models. Without it, a project-level `.env` containing `BIFROST_APP_ID` identifies an independent App; an ordinary loose checkout without either marker uses the Workspace model. If starting inside a nested folder, locate the root with ordinary file discovery; do not use a custom shell loop.

For net-new work, confirm the model with the user before scaffolding. Use an App when one independently deployed frontend should consume live platform resources. Prefer a Solution when the frontend and its workflows, tables, configs, or other definitions must travel and reconcile as one installable package. Use the Workspace for deliberately loose, shared, or existing v1 content. Enable Workspace support for a Solution only when the shared dependencies are intentional and understood, never as a default convenience.

Then establish the exact instance and, for either Solution model, the install that the CLI resolves. Read `.env` in the intended CLI invocation directory, normally the project or Solution root. Parent-directory `.env` files are not selected implicitly. Inspect these optional fields when present:

- `BIFROST_API_URL`
- `BIFROST_APP_ID`
- `BIFROST_SOLUTION_ID`
- `BIFROST_SOLUTION_SLUG`
- `BIFROST_SOLUTION_ORG_ID`
- `BIFROST_SOLUTION_SCOPE`

Treat `.env` as local instance/App/install selection, not portable source. Do not commit it. A normal Bifrost project `.env` should not contain access or refresh tokens; report only the selector and binding fields above. An App clone uses `bifrost app bind` to recreate `BIFROST_API_URL` and `BIFROST_APP_ID`. Without an explicit install binding, Solution commands resolve a unique install by portable slug and print `--solution <id>` choices when several are available. If Solution deploy finds no install, it requires `--org <ref>` or `--global` before creating one.

Compare `Current connection` and `Default connection` from `bifrost auth default`:

- If `.env` selects a non-default instance, tell the user which instance and install are selected and offer the saved default before material work.
- Removing `BIFROST_API_URL` from `.env` returns that directory to the saved default connection. Use `--url` for a one-command override; use `app bind` or `solution bind` only when intentionally remembering a target.
- Never change the user's saved default merely to target one project.

### 2. Understand and plan the change

If this is an App, state its local project, selected instance, bound App, and intended runtime organizations. If this is a Solution, state its name/slug, selected instance, resolved install, and install scope. Then confirm the requested outcome and intended users.

For every material change, present a concise plan and get confirmation before editing. A small, well-bounded bug fix does not need ceremony. The plan must identify:

- user outcome and acceptance criteria;
- source files and platform entities involved;
- organization, access level, roles, and policies;
- integrations, configs, tables, and managed file locations;
- live-instance or deployment effects;
- for apps: information hierarchy, primary interactions, visual direction, theme behavior, responsive behavior, and non-happy-path states.

Keep the access tuple `(organization, access_level, role_ids)` compatible across an app and every workflow, form, or agent it calls, unless a specific entity intentionally requires different access than the rest. Record that exception and verify that every intended caller can still traverse the dependency chain. Runtime access never bypasses organization, role, policy, or external-user checks.

### 3. Build in the correct ownership model

Load the artifact references routed below and follow the working model selected in step 1. Use curated references for the method and generated appendices or `--help` for exact syntax; never infer a familiar command or flag.

Before writing code, read `best-practices/security.md` and `best-practices/workspace.md`, plus the `best-practices/` file for each area touched (`workflows.md`, `integrations.md`, `data.md`, `apps.md`; index in `best-practices/README.md`). References teach the surface; best practices are the rules that keep it from leaking data across users and organizations. Do not mix authoring paths: Workspace entities mutate live; independent App source changes locally and only its compiled artifact deploys; Solution-owned definitions change through local source and deploy. If an App or a Solution supported by the Workspace needs changes on both sides, track them as separate change sets with separate ownership, access, verification, and delivery effects.

Use test-driven development for behavior: define the acceptance result, write a focused failing test when useful, implement the change, and make it pass. Do not create contrived tests for visual-only acceptance; verify the rendered result instead.

Before adding workflow logic, search for an existing module that already owns the domain or integration behavior. Keep workflows as thin orchestration; put reusable business and integration logic in modules.

Treat `app start` and `solution start` as connected development, not data sandboxes. Table, managed-file, config, and integration writes can affect the selected instance.

### 4. Verify the complete experience

Run the relevant automated tests, type checks, builds, and end-to-end behavior. Exercise the primary path and important failures.

For user-facing apps, inspect the rendered result. Verify:

- every changed route and core interaction;
- light and dark modes when theme support is declared;
- loading, empty, error, validation, disabled, and success states;
- narrow and wide layouts, overflow, keyboard use, focus visibility, and contrast;
- spacing, typography, hierarchy, and component consistency.

Give the user the exact local preview command or URL when possible. Fix material polish problems before calling the work complete.

### 5. Ship or hand off intentionally

Summarize what changed and what was verified. Separate source changes from live platform mutations and undeployed work. Call out production-sensitive effects, then offer the appropriate deploy, publish, commit, or push step when the user is ready. Never imply that deployment or publication occurred when it did not.

## How the boundaries fit together

Keep these layers distinct:

- **Working model and source ownership** determine where definitions are edited: instance `_repo`/live records, one local App repository, or local Solution source.
- **Lifecycle ownership** determines how definitions reach the platform: immediate Workspace mutation, App artifact deploy, or Solution full-replace deploy.
- **Dependency resolution** determines where running code may look after its own resources miss. `allow_outbound_access` changes this layer only.
- **Authorization** determines whether a resolved entity or row/file operation is allowed. Organization, access level, roles, policies, and external-user rules always apply.
- **Environment data** such as table rows, runtime files, config values, and integration mappings can be live even while Solution source is running locally.

Therefore, a Solution supported by the Workspace may call an eligible loose workflow without owning it; that workflow keeps its own registration and access controls. A globally scoped Solution entity is still deploy-managed. Shared fallback can make a table or file readable without making it writable or Solution-owned.

These relationships produce the following hard boundaries:

- Solution-owned apps, workflows, forms, agents, tables, configs, claims, and file-location declarations change through local source plus `bifrost solution deploy`; do not live-mutate their managed records.
- Independent App source changes only in its local repository. `bifrost app deploy` builds and activates the App artifact; it does not capture, copy, or own the live workflows, tables, files, configs, or integrations the App calls.
- Instance `_repo` source changes through direct `bifrost files` commands. Writing source does not replace entity creation or workflow registration.
- `.bifrost/*.yaml` is Solution source inside a Solution. Outside a Solution, discover and mutate live entities with their CLI commands rather than treating an exported manifest as live state.
- `allow_outbound_access` is a runtime fallback gate, not install scope, global entity permission, or an authorization bypass.
- `allow_inbound_access` gates outside callers targeting this install per-call with `solution=`; it is not install scope or an authorization bypass, and a targeted call is not a delegated user identity.
- Prefer dedicated entity commands. Before using `bifrost api`, confirm the endpoint in `generated/openapi-digest.md`; it addresses the Bifrost platform API only, never a third-party integration API.
- Keep integration credentials and decrypted config values behind Python workflows; do not expose them to browser code.

## Reference routing

| Need | Load for the task |
|---|---|
| Any change that touches identity, access, integrations, tables/files/configs, or App UI | `best-practices/security.md` always; then `best-practices/workflows.md`, `integrations.md`, `data.md`, or `apps.md` per area (`best-practices/README.md` routes them) |
| Create, bind, start, deploy, or migrate an independent App | `references/apps-independent.md`, `references/apps-v2.md`, `references/app-quality.md`, and `references/web-sdk-v2.md` |
| Create, bind, start, capture, deploy, export, or install a Solution | `references/solutions.md` |
| Read or write instance `_repo` source; maintain loose modules, workflows, or v1 apps | `references/repository.md` |
| Author, register, execute, rename, or expose a Python workflow | `references/workflows.md` and the relevant section of `references/python-sdk.md` |
| Build or modify a V2 App inside a Solution | `references/apps-v2.md`, `references/app-quality.md`, and `references/web-sdk-v2.md` |
| Maintain an existing inline v1 app | Read `references/apps-v1.md` and `references/app-quality.md`; search `references/platform-api.md` only for the exact v1 export being used |
| Create or change forms, agents, configs, integrations, events, orgs, roles, or claims | `references/entities.md` |
| Define a table, write policies, or use table data | `references/tables.md` |
| Store, list, upload, download, or permission managed runtime/user files | `references/files.md` |
| Use resources outside a Solution install | `references/solution-resource-access.md` |
| Work with Bifrost through MCP without the CLI or local source | `references/mcp-mode.md` |
| Need an exact command or flag | `generated/cli-reference.md` |
| Need an exact Python or web SDK signature/export | the matching file under `generated/` |
| Need to confirm a platform endpoint | `generated/openapi-digest.md` |
