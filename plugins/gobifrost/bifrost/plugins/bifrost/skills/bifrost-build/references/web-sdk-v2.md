# Web SDK v2

The instance-served `bifrost` package is the runtime SDK for V2 Apps, both independent and Solution-owned. Use `../generated/web-sdk-surface.md` for the exact export/type surface. Read `apps-v2.md` for project structure and `app-quality.md` for UI completion.

## Keeping an existing app current

The CLI installs the selected instance's web SDK into local dependencies for development, and each server-side deploy builds with that instance's SDK. When a reported behavior is fixed in the web SDK, or an App predates the SDK behavior it now relies on, refresh it before rebuilding:

For a Solution App, run `bifrost solution sdk update [PATH] --app <app-slug>`. For an independent App, `bifrost app start` installs the selected instance's current SDK transiently; remove a stale `node_modules/bifrost` only when the CLI reports a contract mismatch, then start again.

Omit `--app` for a single-App Solution. The Solution command downloads the SDK from the connected Bifrost instance and reinstalls the vendored package; do not hand-edit generated SDK files. After updating, run the App's typecheck, tests, and production build, then redeploy it. API-only execution fixes and host-shell asset fixes do not require an App SDK update.

## Provider and context

Keep the scaffolded `BifrostProvider` wiring in `src/main.tsx`. The host supplies the API URL, viewer token, org scope, app ID, theme, logout handler, and mount basename.

`useBifrostContext()` exposes the scoped transport and host state, including `authedFetch`, logout, and theme controls.

## Signed-in user and roles

`useUser()` returns the signed-in user (`id`, `email`, `name`, `organizationId`, `isPlatformAdmin`, `roles`, `hasRole(name)`, `isLoading`, `error`), read once per provider from `/api/auth/me`. `<RequireRole role="..." fallback={...}>` renders its children only for a holder of that role and nothing while loading.

```tsx
import { RequireRole, useUser } from "bifrost";

const user = useUser();
<p>Signed in as {user.name}</p>
<RequireRole role="Approvers">
  <ApproveButton />
</RequireRole>
```

Showing or hiding a control is convenience, not security: the workflow (its access level and roles, its own checks on `context`) and table policies enforce. Never send these values to a workflow as input.

`supportsTheme` declares that the entire app responds to host light/dark state. Read the theme contract in `app-quality.md` before retaining it.

## Branding and organization selection

Use `useBranding()` for platform colors and logos. It reads public global branding,
resolves logo URLs against the provider's API URL, and applies the main client's
light/dark CSS variables by default. Style controls with `--primary`,
`--primary-foreground`, `--ring`, and `--bf-primary-hover`; the provider's `.dark`
class selects the dark palette. Keep the app's layout and CSS in its own source.

The hook exposes `squareLogoUrl`, `rectangleLogoUrl`, `applicationName`,
`primaryColor`, `palette` (both themes), and `colors` (the current theme).
Missing logos and an unset application name are null. For an app that owns its
color tokens, use `useBranding({ applyTheme: false })` and consume `colors`
directly. An unset primary color uses the platform's standard palette.

Use `useOrganizations({ enabled, includeInactive })` for organization lists and
pickers. Both options are optional; it loads active organizations by default.
The existing endpoint decides which organizations the caller can read. Defer
loading with `enabled: false` when the UI does not need the list, and request
disabled organizations with `includeInactive: true` when needed.

Both hooks expose nullable `data`, `loading`, `error`, and `refetch()`; render
loading and error states before consuming the response. Permission failures
remain errors. Selecting an organization is an app decision: listing
organizations does not change the provider scope or grant access to their data.

```tsx
import { useBranding, useOrganizations } from "bifrost";

const branding = useBranding();
const organizations = useOrganizations();

// After handling loading and error states:
{branding.rectangleLogoUrl && (
  <img src={branding.rectangleLogoUrl} alt="Platform logo" />
)}
<select aria-label="Organization">
  {organizations.data?.map((org) => (
    <option key={org.id} value={org.id}>{org.name}</option>
  ))}
</select>
```

Refresh the App's SDK against an instance containing these hooks before
importing them; see **Keeping an existing app current** above.

## Header

`BifrostHeader` provides optional Bifrost chrome and account/theme controls, plus the App's section links when given `nav`:

```tsx
import { NavLink } from "react-router-dom";
import { BifrostHeader } from "bifrost";

const NAV = [
  { to: "/", label: "Overview", end: true },
  { to: "/tickets", label: "Tickets" },
];

<BifrostHeader title="Operations" nav={{ items: NAV, link: NavLink }} />
```

`nav.link` is the router's link component; the SDK has no router of its own. On wide screens the links form a tab row under the title bar. Below 640px the header is one row: a menu button labelled "Open menu" on the left, then the truncated title. The button opens a panel with Back to Bifrost, the links, the `action` slot, the theme toggle and the account section. Without `nav`, phones still get the menu button for theme and account.

The platform does not insert it automatically. Compose it into the app's own layout and avoid adding a second competing top-level header.

## Workflow hooks

Use the direct SDK capability for platform reads and table/file operations:
`useUser`, `useBranding`, `useOrganizations`, `useTable`/`tables`, and
`useFiles`/`files`. These capabilities can be consumed without packaging a
wrapper workflow. Use workflows for integration calls, secret-bearing work,
and custom business logic that must execute on the server.

Prefer portable `path::function` locators such as `functions/orders.py::list_orders`.

| Need | API |
|---|---|
| Load/reload data on mount or parameter change | `useWorkflowQuery(ref, params)` |
| Run a submit/button action | `useWorkflowMutation(ref)` then `mutate(input)` |
| Fully imperative low-level control | `useWorkflow(ref)` then `run(input)` |

```tsx
import { useWorkflowMutation, useWorkflowQuery } from "bifrost";

const orders = useWorkflowQuery("functions/orders.py::list_orders", {
  status: "open",
});

const createOrder = useWorkflowMutation("functions/orders.py::create_order");
await createOrder.mutate({ customerId, lines });
```

Initial query data is nullable. Render loading and error states before accessing it. Keep query parameter objects stable so ordinary renders do not create accidental refetch loops. For mutations, expose progress, handle rejection, and prevent duplicate action where necessary.

Workflow hooks resolve within the current App context. Solution Apps prefer their install's workflows; independent Apps use live registered workflows in the selected organization. A UUID is environment-specific, so prefer a portable path/function ref.

## Tables

Use imperative `tables` for one-shot CRUD and `useTable`/`useInfiniteTable` for live React views.

```tsx
import { useTable } from "bifrost";

const { rows, total, loading, error } = useTable("tickets", {
  where: { status: "open" },
  page: 1,
  pageSize: 25,
});
```

Hook rows are flattened; imperative query documents keep custom fields under `.data`. Web `tables.delete()` deletes rows, while Python `tables.delete()` deletes the table. Read `tables.md` before implementing table mutations or filters.

## Managed files

Use imperative `files` for reads/writes/uploads/downloads and `useFiles` for a live location/prefix listing.

```tsx
import { files, useFiles } from "bifrost";

const reports = useFiles("reports/", {
  location: "documents",
  includeMetadata: true,
});

await files.write("reports/status.txt", "ready", { location: "documents" });
```

Solution locations must be declared. Independent Apps use live managed-file locations and policies. Render denied separately from empty, and use signed upload/download behavior for large binary data. Read `files.md`.

## Errors

The SDK exports typed table/file errors including access denied, not found, and invalid-policy/location cases. Distinguish failures when they lead to different user actions; otherwise show one actionable message and preserve diagnostic detail for logs.

Do not display raw workflow stack traces, decrypted integration errors, access tokens, or secret config values.

## App identity and scope

The scaffolded provider carries `appId` so deployed workflow/table/file requests resolve within the correct install. Do not construct `X-Bifrost-App`, auth, or Solution query headers manually.

The host also supplies org scope. Explicit scope overrides are privileged behavior and should not be used for ordinary app navigation. `allow_outbound_access` affects server-side fallback; it does not change the web SDK API or bypass policies.

## Verification

- Confirm every imported symbol exists in the generated surface.
- Exercise hooks through the scaffolded provider and real local proxy.
- Test loading, empty, denied, missing, error, success, and reconnect behavior as relevant.
- Verify app/workflow portable refs locally and after deploy.
- Check table/file policies with a realistic viewer.
- Apply the full rendered acceptance checklist in `app-quality.md`.
