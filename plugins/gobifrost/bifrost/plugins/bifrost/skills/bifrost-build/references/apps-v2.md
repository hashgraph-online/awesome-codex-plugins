# V2 Apps

A V2 App is a normal React/TypeScript/Vite project. It can be independently deployed from its own repository or owned and deployed as part of a Solution. Choose the ownership model before scaffolding; read `apps-independent.md` for independent App lifecycle and `solutions.md` for Solution lifecycle.

Read `app-quality.md` before designing user-visible UI and `web-sdk-v2.md` when using Bifrost data or workflows.

## Scaffold first

From a Solution root:

```bash
bifrost solution scaffold-app operations
```

For an independent App repository:

```bash
bifrost app create operations --name "Operations"
```

Both commands create the same App project structure; a Solution nests it under `apps/<slug>/` and adds its descriptor/manifests:

```text
operations/                    # independent repo root, or apps/operations in a Solution
├── package.json
├── vite.config.ts
├── tsconfig.json
├── components.json
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── components/
    ├── lib/
    └── pages/

# Solution ownership adds these outside the App directory:
functions/
.bifrost/apps.yaml
bifrost.solution.yaml
```

Keep the scaffold's `index.html` and reusable `mount()` lifecycle in `src/main.tsx`. It registers the app module, receives per-mount URL/token/org/app/theme bootstrap data, wraps the app in `BifrostProvider`, and mounts the router at the host-provided basename. Hand-written legacy entrypoints often work locally and fail when the platform mounts the app more than once.

The Solution scaffold creates an App manifest entry; its metadata and source deploy with the Solution. The independent scaffold creates and binds the remote App record but stores no manifest or remote source. Do not cross these ownership models.

## Import boundaries

The `bifrost` package contains only the v2 runtime SDK:

```tsx
import {
  BifrostHeader,
  useTable,
  useWorkflowMutation,
  useWorkflowQuery,
} from "bifrost";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { useMemo } from "react";
import { Link } from "react-router-dom";
```

- Import React APIs from `react`.
- Import routing from `react-router-dom`.
- Import icons from `lucide-react`.
- Import shadcn components from the app's `@/components/ui/*` files.
- Import user components by local path.
- Never copy v1 examples that import React, router, icons, or UI components from `bifrost`.

Use `../generated/web-sdk-surface.md` to confirm SDK exports. Do not guess an export.

## App-to-workflow contract

Choose the direct SDK capabilities in `web-sdk-v2.md` before adding a workflow
for a platform read or table/file operation. Branding, organization lists,
viewer identity, documents, and managed files already have SDK APIs. Keep
integration credentials and server-side business logic in workflows.

Reference workflows with portable path/function locators:

```tsx
const query = useWorkflowQuery("functions/list_clients.py::run", { status: "active" });
const save = useWorkflowMutation("functions/save_client.py::run");
```

Prefer `useWorkflowQuery` for reads that run on mount and `useWorkflowMutation` for explicit actions. Guard nullable initial data, render the hook's error, and prevent duplicate mutations while loading.

Solution Apps resolve their own deployed workflows first. Independent Apps resolve live registered workflows in the selected organization. Enforce authorization and integration access in the workflow. Client-side hiding is a convenience, not a security boundary. Keep config secrets and OAuth tokens out of browser code.

## Dependencies and components

Use the app's normal package manifest for browser dependencies. Install shadcn components into the app and import their local source; the platform does not inject the host client's private component tree into v2 apps.

The scaffold intentionally omits an instance-specific `bifrost` dependency. `bifrost app start` and `bifrost solution start` install the selected instance's SDK transiently without changing `package.json`; deployed builds inject the SDK shipped by the serving instance.

Prefer dependencies that are actively maintained, browser-safe, and compatible with the app's React version. Do not introduce a library for behavior that the platform or browser already provides simply because an old example used it.

## Local development

Run the lifecycle's connected development server:

```bash
bifrost solution start operations
# or, from an independent App root:
bifrost app start
```

Open the proxy origin printed by the command, not Vite's internal port. App and workflow code hot-reload behind the same origin.

Both paths use live instance data. A Solution start can run local Solution workflows; an independent App start never runs local workflows and proxies workflow calls to the live platform. Reads and writes to tables, managed files, configs, integrations, and shared resources use real instance state. Seed disposable data or obtain permission before exercising production-sensitive mutations.

## Completion checks

Before offering deploy:

- run the app's tests, type check, and production build;
- exercise workflow calls through the App; for an independent App those calls must hit the live platform rather than local Python;
- inspect every changed route and important state using `app-quality.md`;
- verify `supportsTheme` only after both themes pass;
- confirm the app and supporting entities share compatible organization/access/roles;
- verify portable workflow refs and no environment-specific UUIDs leaked into source;
- ask the user to preview the printed local origin.
