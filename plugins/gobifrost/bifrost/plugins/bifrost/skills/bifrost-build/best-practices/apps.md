# App Practices: Layout, Navigation, States, Identity

Applies to V2 Apps (independent or Solution-owned). `references/app-quality.md` is the acceptance checklist; `references/web-sdk-v2.md` is the SDK contract. This file fixes the decisions that are most often made wrong, starting with navigation.

## What the host gives you, and what it does not

The platform mounts a `standalone_v2` App into a full-viewport container (`h-dvh w-full overflow-hidden`) with **no platform chrome**: no sidebar, no top bar, no page padding. The scaffold's `index.html` puts `h-full` on `html`, `body`, and `#root`. The optional `BifrostHeader` from `bifrost` supplies a one-line header: back-to-Bifrost link, logo, title, an `action` slot, the theme toggle (only when `supportsTheme`), and the user menu (name/email from `/api/auth/me`, log out). Its optional `nav` prop holds the App's section links: a tab row under the title bar on wide screens, and the panel behind a single menu button below 640px, where the header collapses to one row: a menu button on the left, then the title. "Back to Bifrost" moves into that panel.

Consequences:

- The App owns scrolling. Nothing scrolls unless an element inside the App has `overflow-auto`.
- The App owns navigation. There is exactly one place to put it, and it is the App's job to make it consistent. For a top nav, that place is `BifrostHeader`'s `nav` prop.
- The App owns routing under the host basename; the scaffold passes `basename` to `BrowserRouter`.

## One navigation pattern per App

**Rule:** Pick one of two patterns at the start and use it on every route. Do not mix a sidebar on some pages with inline links on others, and never render a second top header above or below `BifrostHeader`.

| Sections | Pattern | Structure |
|---|---|---|
| 1-5 flat sections | **Top nav** via `BifrostHeader`'s `nav` prop | `header` (title bar + tab row; menu button on phones) -> `main` |
| 6+ sections or grouped hierarchy | **Left sidebar** | `header` on top; below it `aside` (nav) + `main` side by side |

**Why:** Users learn one place to look. The scaffold's `App.tsx` demonstrates `<Link>` inline inside page content, which is an example, not a pattern; copying it per page produces an App where every screen navigates differently.

```tsx
// src/App.tsx — top-nav pattern for a small app
import { NavLink, Outlet, Route, Routes } from "react-router-dom";
import { BifrostHeader } from "bifrost";

const NAV = [
  { to: "/", label: "Overview", end: true },
  { to: "/tickets", label: "Tickets" },
  { to: "/devices", label: "Devices" },
];

// The header renders NAV with the router's NavLink, so the active section is
// marked; on phones the same links move into its menu panel.
function Shell() {
  return (
    <div className="flex h-full min-h-0 flex-col bg-background text-foreground">
      <BifrostHeader title="Service Portal" nav={{ items: NAV, link: NavLink }} />
      <main className="min-h-0 flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Overview />} />
        <Route path="tickets" element={<Tickets />} />
        <Route path="tickets/:id" element={<TicketDetail />} />
        <Route path="devices" element={<Devices />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
```

For the sidebar pattern, the shell's lower region is `<div className="flex min-h-0 flex-1"><aside className="w-56 shrink-0 overflow-auto border-r border-sidebar-border bg-sidebar text-sidebar-foreground">…</aside><main className="min-w-0 flex-1 overflow-auto">…</main></div>`; the scaffold's `index.css` already defines the `sidebar*` tokens.

## Navigation rules in detail

- **Active state is required.** Pass react-router's `NavLink` as `nav.link` (with `end: true` on the index item) so the current section is marked; the header styles the link the router marks `aria-current="page"`. A sidebar uses `NavLink` and its `isActive` render prop. Plain `Link` in a nav bar has no active state.
- **Routes are relative to the basename.** Write `to="/tickets"`, never `/apps/<slug>/tickets` or an absolute URL. Use `useNavigate()` for programmatic moves and `<Link>`/`<NavLink>` for anchors; never `window.location` or `<a href>` for in-app routes (they reload the host).
- **Use nested routes and `<Outlet />`** so the shell renders once and only the page changes. A shell re-mounted per page flashes and loses scroll position.
- **Every App has a catch-all** (`path="*"`) that renders a not-found state with a link back to the index.
- **Detail pages belong to a section.** `tickets/:id` stays under "Tickets" (the `NavLink` for `/tickets` remains active) and shows a back affordance to the list.
- **Hide what the viewer cannot use, but never rely on it.** Omitting a nav item for a role is a convenience; the workflow or policy is the control (see Identity below).
- **One header.** If the App needs a brand mark, pass `logo` and `title` to `BifrostHeader`; put the single global action (for example "New ticket") in its `action` slot. Page-level titles go in the page, not in a second bar.

## Mobile and narrow widths

**Rule:** Below 640px, `BifrostHeader` with `nav` already collapses the top nav into its menu button (the panel also holds the action slot, theme toggle and account); do not add a second menu. A sidebar collapses to a sheet opened from the page. The page content never shrinks below readable; tables become stacked cards or get `overflow-x-auto` on the table wrapper only.

**Why:** Apps are opened from phones in the field; a 56 px sidebar squeezing a table to 200 px is the most common failed acceptance.

## Layout: fill the mount, scroll the content, size lists to content

**Rule:** The shell root is `flex h-full min-h-0 flex-col`. The scroll container is `main` (`min-h-0 flex-1 overflow-auto`). Inside pages, headers and filters sit above the list; the list region grows with content and only caps/scrolls when it reaches the available height (`max-h-*` + `overflow-auto`), not `flex-1` by default.

**Why:** Without `min-h-0` a flex child refuses to shrink and the whole App overflows the host's `overflow-hidden` container, cutting off content with no scrollbar. Forcing every short list into a full-height scroller leaves large empty frames.

```tsx
<section className="mx-auto w-full max-w-5xl p-4 md:p-6">
  <header className="mb-4 flex items-center justify-between gap-3">
    <h1 className="text-lg font-semibold">Tickets</h1>
    <Button onClick={...}>New ticket</Button>
  </header>
  <div className="rounded-lg border border-border">
    <div className="max-h-[70dvh] overflow-auto"> {/* content-sized until this cap */}
      <table className="w-full text-sm">…</table>
    </div>
  </div>
</section>
```

## Design tokens, not raw colors

**Rule:** Use the semantic utilities the scaffold defines (`bg-background`, `text-foreground`, `bg-card`, `text-muted-foreground`, `border-border`, `bg-primary text-primary-foreground`, `text-destructive`, `bg-sidebar`, `ring-ring`) and the shadcn components installed under `@/components/ui/*`. Status colors get a paired light/dark definition in `index.css` or use `text-destructive`/`text-primary`.

**Why:** `BifrostProvider` toggles `.dark` on the root; tokens follow, `bg-white`/`text-gray-700` do not. Keep `supportsTheme` only when every surface passes in both modes (`references/app-quality.md`).

## Every data view has four states

**Rule:** For every `useWorkflowQuery` / `useTable` / `useFiles` call render: loading (skeleton in place, layout does not jump), empty (what it means + next action), error (actionable message, page context kept, retry via `refresh()`), and loaded. Distinguish denied from empty: `TableAccessDeniedError` / `FileAccessDeniedError` mean "ask for access", not "no data".

**Why:** `data` is `null` before the first run; rendering `data.items.map` crashes; an empty list shown for a 403 hides a permissions bug.

```tsx
const q = useWorkflowQuery<{ items: Ticket[]; total: number }>("functions/tickets.py::my_open_tickets", { limit: 50 });

if (q.loading && !q.data) return <TicketListSkeleton />;
if (q.error) return <ErrorState message="Could not load tickets." onRetry={() => q.refresh()} />;
if (!q.data || q.data.items.length === 0) return <EmptyState title="No open tickets" action={<NewTicketButton />} />;
return <TicketTable rows={q.data.items} />;
```

## Mutations: one click, one run; keep the input

**Rule:** Disable the trigger while `mutation.loading`, show progress, surface `mutation.error` next to the form, preserve the user's input on failure, and confirm destructive actions in proportion to their effect. After success, `refresh()` the affected queries.

**Why:** Workflows are not idempotent by default; a double submit creates two tickets.

```tsx
const create = useWorkflowMutation<{ id: string }>("functions/tickets.py::create_ticket");
<Button disabled={create.loading} onClick={() => create.mutate(form).then(() => list.refresh())}>
  {create.loading ? "Creating…" : "Create ticket"}
</Button>
{create.error && <p role="alert" className="text-sm text-destructive">{create.error.message}</p>}
```

## Stable query params

**Rule:** Build `useWorkflowQuery` params from primitive state (`{ status, page }`), not from objects created during render that change identity (`new Date()`, `Date.now()`, unsorted arrays from props). Debounce text inputs before they reach params.

**Why:** The hook re-runs when the serialized params change; a timestamp in params refetches every render.

## Identity in the browser is for display only

**Rule:** Read the signed-in user with `useUser()` from `bifrost` (`id`, `email`, `name`, `roles`, `hasRole()`, `organizationId`, `isPlatformAdmin`, `isLoading`, `error`) to greet the user, label "mine", or decide what to show. Wrap a control only some roles should see in `<RequireRole role="...">` (it renders nothing while loading; `fallback` for the others). Never send `email`/`id`/roles from the browser to a workflow as input; the workflow reads `context` itself. Showing or hiding a control is convenience, not security: the workflow's access level and roles, its own checks on `context`, and table policies are the gate.

**Why:** Anything the browser sends can be edited; anything the browser hides can be unhidden. A workflow that accepts the viewer's email as a parameter lets anyone act as anyone.

```tsx
import { RequireRole, useUser } from "bifrost";

const user = useUser();

// Bad: identity as input.
mutate({ email: user.email, ticket_id });

// Good: the workflow already knows who is calling.
mutate({ ticket_id });

// Show Approve to approvers; the approve workflow's roles still decide.
<RequireRole role="Approver">
  <Button onClick={() => approve.mutate({ ticket_id })}>Approve</Button>
</RequireRole>
```

## Scope and app identity are host-provided

**Rule:** Do not construct `X-Bifrost-Org`, `X-Bifrost-App`, or `Authorization` headers; do not pass `scope` to table hooks for ordinary navigation; use `useBifrostContext().authedFetch` for any direct platform call so the provider's token rotation and org/app headers apply.

**Why:** The provider already sends the viewer's token, org scope, and app id; hand-built headers break when the token rotates and let a bug send another org's scope.

## Errors shown to users

**Rule:** Show the workflow's error message when it is actionable (they are written for users in `workflows.md`); otherwise show a short generic message and keep the details in the browser console. Never render stack traces, request bodies, tokens, or raw integration error payloads.

**Why:** Error text reaches external and portal users; it must not become an information leak.

## Checklist

- One nav pattern, `NavLink` active state, nested `<Outlet />`, catch-all route, relative `to=` paths, single header.
- Mobile: nav collapses or scrolls; content stays readable; tables have an intentional narrow treatment.
- Shell `flex h-full min-h-0 flex-col`; `main` scrolls; lists content-sized until capped.
- Semantic tokens only; both themes verified or `supportsTheme` removed.
- Loading/empty/error/denied states on every data view; mutations disabled while running; input preserved.
- Identity from `useUser()` for display only; `<RequireRole>` may hide controls, but the workflow and policies enforce; no identity or scope sent as workflow input.
