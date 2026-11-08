# Tauri Architecture Rules

> Core taxonomy and gates for Tauri v2 + Vite + React + TanStack Router file-based routing + TanStack Query.

Read this first. Load topic rules/tauri for implementation detail and dated official references whenever a vendor/API fact is material.

## Rule labels and authority

| Label | Meaning | Enforcement |
|---|---|---|
| **Official** | A requirement or documented behavior from Tauri, TanStack, Vite, or React. | Follow it unless higher-priority project/user instructions choose a supported alternative. |
| **Safety** | A Hypercore security or runtime-correctness boundary. | Blocking for touched work; never relax without an explicitly accepted risk and authority where required. |
| **Hypercore convention** | A local maintainability convention beyond vendor requirements. | Apply to touched surfaces; brownfield exceptions may be recorded instead of forcing unrelated migration. |

Official facts are dated evidence, not executable instructions. User and repository instructions outrank this skill; they do not authorize credentials, native side effects, publication, release, deployment, or destructive operations.

## Supported runtime shapes

### Complete packaged Vite SPA

**Official:** Tauri packages the Vite frontend build as static assets in its WebView. TanStack Router owns generated file-based routing through `@tanstack/router-plugin/vite`. TanStack Query owns asynchronous data cache and freshness; it does not provide a file-routing system.

**Safety:** Do not map browser modules, routes, loader state, or Query state to Tauri commands, IPC, or native authority. Keep renderer/browser code and Tauri IPC/Rust code as distinct trust boundaries.

**Hypercore convention:** Name the selected mode in architecture decisions and keep Vite, Router-plugin, and `src-tauri` wiring explicit in configuration rather than relying on undocumented scripts.

### Incomplete adoption

**Official:** Tauri v2 can host a static frontend without requiring Vite, React, Router, or Query.

**Safety:** Do not install, migrate, remove, or rewrite framework layers merely because this skill was triggered; preserve existing build/security behavior until the user requests an adoption step.

**Hypercore convention:** Adopt incrementally: establish Vite/React entrypoint and static package wiring, then Router file-based routing and Query where each provides an identified benefit. Record missing layers and compatibility constraints as an adoption plan, not violations.

### Route away

**Official:** Framework-specific rules/tauri only apply when their runtime and dependency evidence exists.

**Safety:** Do not apply Tauri IPC/capability rules/tauri to a web-only app or treat a project outside this stack as this static SPA architecture.

**Hypercore convention:** Route Rust-only, web-only, or documentation-only tasks to their applicable workflow after a short boundary note. A full-stack TanStack runtime has a different output shape: server-owned routes, loaders, and SSR data flow instead of a packaged static SPA boundary, so it goes to a full-stack architecture workflow.

## Architecture layers

```text
Renderer / WebView
  React UI -> TanStack Router (generated file routes) -> TanStack Query -> browser-safe remote API
       |
       | Tauri IPC (narrow, validated)
       v
Tauri Rust commands/plugins/state
  local OS/native boundary
```

### Ownership rules/tauri

- **Official:** Tauri commands are invoked through the Tauri API; capabilities, permissions, and plugin scopes govern access according to Tauri configuration.
- **Safety:** A privileged native operation MUST cross a narrow IPC/plugin boundary. Validate untrusted input at that boundary, authorize the caller/action, and expose the least capability/scope necessary.
- **Safety:** Browser-visible code MUST NOT contain server-only or native-only credentials. `VITE_`-prefixed values are public build-time values, not secrets.
- **Official:** TanStack Router owns route state/navigation and generated file-based routing. TanStack Query owns asynchronous remote-data cache/server-state behavior; it does not own file-based routing.
- **Hypercore convention:** Keep route adapters thin: pages compose routed screens, modules own cohesive domain UI/query/model behavior, and shared components are promoted only after independent reuse.
- **Hypercore convention:** Keep local native operations behind explicit IPC adapters. Avoid generic `utils`, `services`, component, or IPC catch-alls; group shared code by one named responsibility.

## Platform and packaging gates

| Gate | Label | Requirement |
|---|---|---|
| Static frontend | **Official** | Tauri `frontendDist` points to the built static Vite frontend artifact; development configuration uses the intended Vite dev URL/commands. |
| Router generation | **Official** | `@tanstack/router-plugin/vite` generates file-based routes and precedes the React plugin in Vite configuration. |
| Query ownership | **Safety** | Query cache and freshness MUST remain in TanStack Query; do not present Query as a file-routing system. |
| Asset paths | **Official** | Vite/Tauri asset base and output paths MUST work from packaged application assets, not only a browser dev server. |
| Client environment | **Safety** | Renderer code MUST use only public configuration and MUST NOT rely on local secret files or server-only environment values. |
| Privileged surface | **Safety** | New command/plugin access MUST have a reviewed capability, permission, scope, validation, and error path. |
| CSP/scopes | **Safety** | CSP, capabilities, permissions, and scopes MUST remain least-privilege; do not disable or widen them as a workaround. |
| Generated output | **Official** | Do not hand-edit generated route/build artifacts; change source/configuration and regenerate through the project workflow. |

## Brownfield adoption policy

A brownfield project may have legacy layout, router, query, IPC, or config patterns. Classify every finding before acting:

1. **Safety or Official correctness issue in touched code:** block or fix before completion.
2. **Safety issue in untouched reachable code:** report it clearly; fix it when the requested work depends on it or the user authorizes the broader change.
3. **Hypercore convention in untouched code:** record a bounded migration recommendation; do not expand the request into a repo-wide refactor.
4. **Missing stack layer:** select incomplete-adoption mode and propose the smallest ordered adoption step, not a false compliance failure.

Do not call legacy code compliant merely because it is untouched. Do not call a convention breach a vendor requirement.

## Blocking gates

Do not complete a touched change while any applicable gate below fails:

1. **Mode gate:** The project/runtime mode is unknown, a missing stack layer is treated as complete adoption, or a full-stack TanStack project is treated as this packaged static SPA instead of being routed to a full-stack architecture workflow.
2. **Boundary gate:** Browser modules, routes, loader state, or Query state are mapped to Tauri commands or native authority.
3. **Secret gate:** A renderer-reachable path can read/exfiltrate credentials, private configuration, native filesystem/process access, or server-only dependencies.
4. **IPC gate:** A new privileged command/event/plugin path lacks least privilege, validation, authorization, capability/permission/scope coverage, or safe error handling, or the design relies on channel/large-response scoping the installed Tauri version does not provide.
5. **Input gate:** Untrusted renderer, web, deep-link, event, or IPC data reaches native-sensitive behavior without validation and authorization.
6. **Platform gate:** Static packaging, route generation, asset paths, CSP, Vite environment exposure, or capability configuration would fail or become unsafe outside development.
7. **Authority gate:** The task needs credentials, native side effects, destructive actions, publication, release, or deployment without explicit authority.
8. **Evidence gate:** Required validation is absent, failed, or misrepresented after at most two passes against the same declared checks.

A blocking gate may be cleared only by a concrete fix, a project-supported alternative with evidence, or an explicit user decision for an authority-gated action. A convention-only deviation is not a blocking-gate waiver.

## Validation decision

Before claiming completion, identify mode and touched layers, evaluate applicable blocking gates, run the allowed focused checks from `rules/tauri/testing.md`, and record exact output or the reason a check was not permitted. One correction pass is allowed after a failed validation pass; stop after the second result and report remaining blockers rather than starting another optimization loop.