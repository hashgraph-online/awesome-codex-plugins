# Inline v1 Apps

Use this reference only to maintain an existing `inline_v1` App. Build new Apps as V2 projects, either independently or inside a Solution according to ownership needs.

## Ownership

A v1 app has two live layers:

1. An app record containing its name, slug, `_repo` path, dependencies, organization, access level, and roles.
2. TSX/TypeScript/CSS source under `apps/<slug>/` in instance `_repo`.

Create the record before writing source. Read and write source with direct `bifrost files` commands; see `repository.md`. Source changes and metadata mutations affect the selected instance immediately.

## Runtime imports

The v1 runtime rewrites the special module name `bifrost` to an injected platform object. Import platform-provided names from that module:

```tsx
import {
  Button,
  Card,
  React,
  useState,
  useWorkflowQuery,
} from "bifrost";
```

Use `platform-api.md` as exact lookup for names that are actually exported. Do not assume a package available in v2 is injected into v1.

Other imports follow these rules:

- Import icons from `lucide-react`.
- Import router APIs from `react-router-dom`.
- Import another user file with a relative path such as `./components/ClientCard`.
- Import an app dependency with its bare package name only after declaring it on the app record with `bifrost apps set-deps`.
- Do not import host-client internal aliases such as `@/components/ui/button`; v1 user files cannot resolve the platform repository's private source tree.

## v1-only capabilities

`useAppState` belongs to the v1 injected surface and does not exist in the v2 SDK. `useUser` and `RequireRole` exist in both with the same shape (the v2 `useUser` adds `isLoading`, since it reads the user over the network); in v2, import them from `bifrost`.

Server-side workflows and policies remain the authorization boundary even when a v1 component hides UI by role.

## Editing and dependencies

Read current source before replacing it; `bifrost files write` is a full-text write. Preserve the app's existing route/component conventions unless the requested work includes a redesign.

Browser npm dependencies are stored on the app record, not inferred from imports:

```bash
bifrost apps set-deps <app-ref> --deps '{"recharts":"^2.12.0"}'
```

Changing dependencies can rebuild the live preview. Python worker requirements are separate.

## Preview and publish

Inspect draft source at `/apps/<slug>/preview` on the selected instance. The published app lives at `/apps/<slug>` and does not receive draft changes until publication.

After the user approves the preview, offer the explicit live publication step:

```bash
bifrost apps publish <app-ref>
```

Publication queues the production rebuild. Verify its result and the published route; do not treat a successful preview build as proof that publication occurred.

## Quality and migration

Apply `app-quality.md` to v1 changes as well. Use semantic platform tokens where the runtime supports them, verify the actual rendered preview, and test all affected states.

When converting to V2, choose ownership first. Use `bifrost app migrate <source-dir> <destination>` when the frontend should remain backed by live platform resources. Use `bifrost solution migrate-app <source-dir> <v2-slug>` when the App and selected backing definitions should become one installable package. Both commands stop before judgment-heavy route wiring, access review, theming, and visual QA; do not perform a mechanical import rewrite and call the migration complete.
