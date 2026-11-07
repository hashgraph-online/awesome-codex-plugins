# Legacy v1 Platform Surface

Use this file only as exact lookup while maintaining an existing `inline_v1` app. It lists every name injected through the v1 `"bifrost"` module. New `standalone_v2` apps use the much smaller surface in `../generated/web-sdk-surface.md`.

Canonical source: `api/bifrost/platform_names.py` (`PLATFORM_EXPORT_NAMES`). A drift test (`api/tests/unit/test_platform_api_docs.py`) enforces that every name in that set has a matching `### <Name>` section here. Search this file for `### <ExportName>` instead of reading it from beginning to end.

Conventions:
- Signatures are TypeScript-shaped. UI component props shadow the underlying shadcn/ui (or react-day-picker) primitive — only load-bearing differences are called out.
- All imports are `import { X } from "bifrost"`.
- "shadcn/ui compatible props" means the component is a re-export of the project's `@/components/ui/<name>` shadcn primitive and accepts the standard Radix / shadcn prop surface.

## React

### Fragment

Signature: `React.Fragment` — groups children without introducing a DOM node.

```tsx
import { Fragment } from "bifrost";
<Fragment><h1>Title</h1><p>Body</p></Fragment>
// Or the shorthand `<>...</>` (JSX fragment) — equivalent.
```

### React

Signature: the React namespace. Most usage is via individual named exports (hooks, `Fragment`, `memo`, etc.), but `React` itself is available.

```tsx
import { React } from "bifrost";
const ref = React.createRef<HTMLDivElement>();
```

### Suspense

Signature: `<Suspense fallback={ReactNode}>{children}</Suspense>` — boundary for lazy-loaded components / data.

```tsx
import { Suspense, lazy } from "bifrost";
const Heavy = lazy(() => import("./pages/heavy"));
<Suspense fallback={<div>Loading…</div>}><Heavy /></Suspense>
```

### createContext

Signature: `createContext<T>(defaultValue: T): Context<T>`.

```tsx
import { createContext } from "bifrost";
const ThemeContext = createContext<"light" | "dark">("light");
```

### createElement

Signature: `createElement(type, props?, ...children): ReactElement`.

```tsx
import { createElement } from "bifrost";
const status = createElement("span", { className: "text-sm" }, "Ready");
```

### forwardRef

Signature: `forwardRef<Ref, Props>((props, ref) => ReactElement): ForwardRefExoticComponent`.

```tsx
import { forwardRef } from "bifrost";
const Box = forwardRef<HTMLDivElement, { label: string }>(function Box({ label }, ref) {
  return <div ref={ref}>{label}</div>;
});
```

### lazy

Signature: `lazy<T>(loader: () => Promise<{ default: ComponentType<T> }>): LazyExoticComponent<T>` — code-split entry point.

```tsx
import { lazy, Suspense } from "bifrost";
const Reports = lazy(() => import("./pages/reports"));
<Suspense fallback={<div>…</div>}><Reports /></Suspense>
```

### memo

Signature: `memo<P>(Component, areEqual?): MemoExoticComponent<Component>` — skips re-render when props are shallow-equal.

```tsx
import { memo } from "bifrost";
const Row = memo(function Row({ item }: { item: any }) { return <div>{item.name}</div>; });
```

### useCallback

Signature: `useCallback<T extends (...args: any[]) => any>(fn: T, deps: DependencyList): T`.

```tsx
import { useCallback } from "bifrost";
const onClick = useCallback(() => setCount((c) => c + 1), []);
```

### useContext

Signature: `useContext<T>(Context: React.Context<T>): T`.

```tsx
import { useContext } from "bifrost";
const theme = useContext(ThemeContext);
```

### useDeferredValue

Signature: `useDeferredValue<T>(value: T): T` — returns a deferred version for non-urgent updates.

```tsx
import { useDeferredValue } from "bifrost";
const deferredQuery = useDeferredValue(query);
```

### useDebugValue

Signature: `useDebugValue<T>(value: T, format?: (value: T) => unknown): void` — labels custom hook state in React DevTools.

```tsx
import { useDebugValue } from "bifrost";
function useStatusLabel(status: string) {
  useDebugValue(status);
  return status;
}
```

### useEffect

Signature: `useEffect(effect: () => void | (() => void), deps?: DependencyList): void`.

```tsx
import { useEffect } from "bifrost";
useEffect(() => {
  const id = setInterval(() => setTick((t) => t + 1), 1000);
  return () => clearInterval(id);
}, []);
```

### useId

Signature: `useId(): string` — stable unique id for a11y associations.

```tsx
import { useId } from "bifrost";
const id = useId();
<label htmlFor={id}>Name</label><input id={id} />
```

### useImperativeHandle

Signature: `useImperativeHandle<T, R extends T>(ref: Ref<T>, init: () => R, deps?: DependencyList): void`.

```tsx
import { useImperativeHandle, forwardRef } from "bifrost";
forwardRef(function Input(_, ref) {
  useImperativeHandle(ref, () => ({ focus: () => inputRef.current?.focus() }), []);
  return <input ref={inputRef} />;
});
```

### useLayoutEffect

Signature: `useLayoutEffect(effect, deps?): void` — synchronous after DOM mutation, before paint.

```tsx
import { useLayoutEffect } from "bifrost";
useLayoutEffect(() => { el.current!.scrollTop = el.current!.scrollHeight; }, [messages]);
```

### useInsertionEffect

Signature: `useInsertionEffect(effect: () => void | (() => void), deps?: DependencyList): void` — runs before layout effects for CSS-in-JS style insertion.

```tsx
import { useInsertionEffect } from "bifrost";
useInsertionEffect(() => {
  const style = document.createElement("style");
  style.textContent = ".critical { visibility: visible; }";
  document.head.append(style);
  return () => style.remove();
}, []);
```

### useMemo

Signature: `useMemo<T>(factory: () => T, deps: DependencyList): T`.

```tsx
import { useMemo } from "bifrost";
const sorted = useMemo(() => items.slice().sort(byName), [items]);
```

### useReducer

Signature: `useReducer<R extends Reducer<any, any>>(reducer, initial): [State<R>, Dispatch<Action<R>>]`.

```tsx
import { useReducer } from "bifrost";
const [state, dispatch] = useReducer(reducer, { count: 0 });
```

### useRef

Signature: `useRef<T>(initial: T | null): MutableRefObject<T>`.

```tsx
import { useRef } from "bifrost";
const inputRef = useRef<HTMLInputElement>(null);
```

### useState

Signature: `useState<T>(initial: T | (() => T)): [T, Dispatch<SetStateAction<T>>]`.

```tsx
import { useState } from "bifrost";
const [count, setCount] = useState(0);
```

### useSyncExternalStore

Signature: `useSyncExternalStore<Snapshot>(subscribe, getSnapshot, getServerSnapshot?): Snapshot`.

```tsx
import { useSyncExternalStore } from "bifrost";
const online = useSyncExternalStore(
  (notify) => {
    window.addEventListener("online", notify);
    window.addEventListener("offline", notify);
    return () => {
      window.removeEventListener("online", notify);
      window.removeEventListener("offline", notify);
    };
  },
  () => navigator.onLine,
  () => true,
);
```

### useTransition

Signature: `useTransition(): [boolean, (callback: () => void) => void]`.

```tsx
import { useTransition } from "bifrost";
const [isPending, startTransition] = useTransition();
startTransition(() => setQuery(next));
```

## React Router

All names in this section are re-exports of `react-router-dom`. Signatures match the `react-router-dom` v6 API exactly — consult the react-router docs for prop/return details. For new code, prefer `import { ... } from "react-router-dom"` directly; imports from `"bifrost"` continue to work.

Common examples:

```tsx
import { Link, NavLink, Outlet, useNavigate, useLocation, useParams, useSearchParams } from "bifrost";

// Link — anchor that navigates without a full page load.
// NOTE: `<Link to="/clients">` correctly navigates to /apps/<slug>/preview/clients
// (or /apps/<slug>/clients in live mode) because the shell's BrowserRouter has
// `basename` set. Do NOT pre-prefix the path yourself.
<Link to="/clients">Clients</Link>

// NavLink — Link with active-state.
<NavLink to="/clients" className={({ isActive }) => isActive ? "bg-accent" : ""}>Clients</NavLink>

// Outlet — where child routes render in a layout.
export default function Layout() { return <div><Sidebar /><Outlet /></div>; }

// useNavigate — imperative navigation.
const navigate = useNavigate();
<Button onClick={() => navigate("/clients/new")}>New</Button>

// useParams — URL path params.
const { id } = useParams<{ id: string }>();

// useSearchParams — query string. Note: returns [URLSearchParams, setter].
const [searchParams] = useSearchParams();
const q = searchParams.get("q");
```

Alphabetical list of the React Router names exported through `"bifrost"`. Each is a direct re-export; signatures match `react-router-dom`.

### Await
Usage: `<Await resolve={promise}>{(value) => <Page value={value} />}</Await>` — renders deferred loader data.

### BrowserRouter
Usage: `<BrowserRouter basename="/app">...</BrowserRouter>` — HTML5 history router. Apps do NOT instantiate this; the shell does.

### createBrowserRouter
Usage: `createBrowserRouter(routes, opts?)` — data router factory.

### createHashRouter
Usage: `createHashRouter(routes, opts?)` — hash-based router factory.

### createMemoryRouter
Usage: `createMemoryRouter(routes, opts?)` — in-memory router factory (tests).

### createRoutesFromChildren
Usage: `createRoutesFromChildren(children)` — build route config from JSX.

### createRoutesFromElements
Usage: alias for `createRoutesFromChildren`.

### createSearchParams
Usage: `createSearchParams(init?): URLSearchParams`.

### Form
Usage: `<Form method="post" action="/route">...</Form>` — router-aware form submission.

### generatePath
Usage: `generatePath("/users/:id", { id: "123" }) // "/users/123"`.

### HashRouter
Usage: `<HashRouter>...</HashRouter>` — hash-based router.

### Link
Usage: `<Link to="/clients">Clients</Link>` — client-side navigation anchor. Respects the shell's `basename`.

### matchPath
Usage: `matchPath({ path: "/users/:id" }, "/users/123"): PathMatch | null`.

### matchRoutes
Usage: `matchRoutes(routes, location): RouteMatch[] | null`.

### MemoryRouter
Usage: `<MemoryRouter initialEntries={["/"]}>...</MemoryRouter>`.

### Navigate
Usage: `<Navigate to="/login" replace />` — declarative redirect.

### navigate
Usage: `navigate("/clients")` — imperative navigation function (the platform version prepends basename). Prefer `useNavigate()` inside components; `navigate` is for event handlers outside React.

### NavLink
Usage: `<NavLink to="/clients" className={({ isActive }) => isActive ? "on" : ""}>` — Link with active/pending state props.

### Outlet
Usage: `<Outlet />` — renders the matched child route in a layout.

### renderMatches
Usage: `renderMatches(matches): ReactElement | null`.

### resolvePath
Usage: `resolvePath("edit", "/users/123"): Path // { pathname: "/users/123/edit", ... }`.

### Route
Usage: `<Route path="/clients" element={<Clients />} />` — route definition.

### Router
Usage: low-level `<Router location navigator>` — apps rarely need this.

### RouterProvider
Usage: `<RouterProvider router={browserRouter} />` — renders a data router.

### Routes
Usage: `<Routes>{routes.map(r => <Route ... />)}</Routes>` — route table.

### ScrollRestoration
Usage: `<ScrollRestoration />` — preserves scroll position across navigations (data router only).

### unstable_usePrompt
Usage: `unstable_usePrompt({ when: isDirty, message: "..." })` — confirm before navigation.

### useActionData
Usage: `const data = useActionData<T>()` — result from latest `Form` action.

### useAsyncError
Usage: `const err = useAsyncError()` — error thrown by `<Await>` resolver.

### useAsyncValue
Usage: `const value = useAsyncValue()` — resolved value inside `<Await>`.

### useBeforeUnload
Usage: `useBeforeUnload((e) => e.preventDefault(), { capture: true })`.

### useBlocker
Usage: `const blocker = useBlocker(({ currentLocation, nextLocation }) => isDirty)` — block navigation conditionally.

### useFetcher
Usage: `const fetcher = useFetcher<T>()` — imperative form/load outside the main navigation.

### useFetchers
Usage: `const fetchers = useFetchers(): Fetcher[]` — all in-flight fetchers.

### useHref
Usage: `const href = useHref("/relative")` — href including basename.

### useInRouterContext
Usage: `const inRouter = useInRouterContext(): boolean`.

### useLinkClickHandler
Usage: `const onClick = useLinkClickHandler(to, opts)` — handler for custom Link-alikes.

### useLoaderData
Usage: `const data = useLoaderData<T>()` — data from route loader (data router).

### useLocation
Usage: `const loc = useLocation()` — `{ pathname, search, hash, state, key }`.

### useMatch
Usage: `const match = useMatch("/users/:id"): PathMatch | null`.

### useNavigate
Usage: `const navigate = useNavigate(); navigate("/x");` or `navigate(-1)` to go back. Respects basename.

### useNavigation
Usage: `const nav = useNavigation()` — `{ state, location, formData }` of pending navigation (data router).

### useNavigationType
Usage: `const type = useNavigationType(): "POP" | "PUSH" | "REPLACE"`.

### useOutlet
Usage: `const element = useOutlet(): ReactElement | null`.

### useOutletContext
Usage: `const ctx = useOutletContext<T>()` — context passed via `<Outlet context={...} />`.

### useParams
Usage: `const { id } = useParams<{ id: string }>()` — URL path params.

### useResolvedPath
Usage: `const path = useResolvedPath("./edit")` — resolve relative to current route.

### useRevalidator
Usage: `const { revalidate, state } = useRevalidator()` (data router).

### useRouteError
Usage: `const error = useRouteError()` — inside an `errorElement` route.

### useRouteLoaderData
Usage: `const data = useRouteLoaderData<T>("route-id")`.

### useRoutes
Usage: `const element = useRoutes(routes)` — render a route config as an element.

### useSearchParams
Usage: `const [params, setParams] = useSearchParams()` — read/write query string.

### useSubmit
Usage: `const submit = useSubmit(); submit(formData, { method: "post" })`.

### UNSAFE_DataRouterContext
Internal React Router context. Apps should not use this directly.

### UNSAFE_DataRouterStateContext
Internal React Router context. Apps should not use this directly.

### UNSAFE_LocationContext
Internal React Router context. Apps should not use this directly.

### UNSAFE_NavigationContext
Internal React Router context. Apps should not use this directly.

### UNSAFE_RouteContext
Internal React Router context. Apps should not use this directly.

## Hooks

### RequireRole

Signature: `<RequireRole role: string fallback?: ReactNode>{children}</RequireRole>` — renders `children` only if `useUser().hasRole(role)` is true; otherwise renders `fallback` (default: nothing).

```tsx
import { RequireRole, Navigate } from "bifrost";

<RequireRole role="Admin" fallback={<Navigate to="/" />}>
  <AdminPanel />
</RequireRole>
```

### useAppState

Signature: `useAppState<T>(key: string, initialValue: T): [T, (value: T) => void]` — `useState`-shaped tuple, but the value persists across page navigations within the same app session (Zustand-backed).

Scope: app session. Cleared on browser refresh or when switching apps. NOT persistent — use workflows to save to the DB for durable data.

```tsx
import { useAppState, Button, useNavigate } from "bifrost";

// List page — write
const [, setSelectedClient] = useAppState<Client | null>("selectedClient", null);
const navigate = useNavigate();
<Button onClick={() => { setSelectedClient(c); navigate("/details"); }}>View</Button>

// Detail page — read
import { Navigate } from "bifrost";
const [selectedClient] = useAppState<Client | null>("selectedClient", null);
if (!selectedClient) return <Navigate to="/" />;
```

Use cases: selected list-item passed to a detail page, filter/sort preferences, multi-step form state, cart contents, sidebar collapse state.

### useUser

Signature: `useUser(): { id: string; email: string; name: string; roles: string[]; hasRole(role: string): boolean; organizationId: string }`.

```tsx
import { useUser, Navigate } from "bifrost";

export default function AdminPage() {
  const user = useUser();
  if (!user.hasRole("Admin")) return <Navigate to="/" />;
  return <div>Welcome, {user.name} ({user.email})</div>;
}
```

### useWorkflowMutation

Signature:
```ts
useWorkflowMutation<T = unknown>(workflowId: string): {
  execute: (params?: Record<string, unknown>) => Promise<T>;
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  /** @deprecated use errorMessage */
  error: string | null;
  data: T | null;
  logs: StreamingLog[];
  reset: () => void;
  executionId: string | null;
  status: ExecutionStatus | null;
}
```

Imperative workflow execution. Use it for click/submit actions: save, approve, delete, sync, generate, send. It does nothing until `execute()` is called. `execute()` resolves with the final workflow result or rejects on failure / timeout (5min); it does **not** return the execution ID.

`executionId` is reactive hook state. It becomes non-null as soon as the platform returns `execution_id` from `POST /api/workflows/execute`, before the workflow result resolves. If you need to redirect or show an execution link, watch `executionId` with `useEffect`. The hook state is latest-execution state, not per-call state; avoid concurrent `execute()` calls from one hook if the UI needs separate state for each run.

```tsx
import { useWorkflowMutation, Button, toast } from "bifrost";

const WF_SAVE_CLIENT = "4f262085-f4d1-4b3d-a601-575ba4c9d207";

export default function SaveButton({ client }: { client: any }) {
  const { execute, isLoading } = useWorkflowMutation(WF_SAVE_CLIENT);
  async function save() {
    try {
      await execute(client);
      toast.success("Saved");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed");
    }
  }
  return <Button onClick={save} disabled={isLoading}>Save</Button>;
}
```

```tsx
import { useEffect, useState, useWorkflowMutation, useNavigate, Button } from "bifrost";

const WF_START_REPORT = "uuid-here";

export default function StartReportButton() {
  const navigate = useNavigate();
  const [shouldRedirect, setShouldRedirect] = useState(false);
  const { execute, executionId, isLoading } = useWorkflowMutation(WF_START_REPORT);

  useEffect(() => {
    if (!shouldRedirect || !executionId) return;
    navigate(`/executions/${executionId}`);
  }, [shouldRedirect, executionId, navigate]);

  function start() {
    setShouldRedirect(true);
    execute({ reportType: "monthly" }).catch(() => setShouldRedirect(false));
  }

  return <Button onClick={start} disabled={isLoading}>Start report</Button>;
}
```

### useWorkflowQuery

Signature:
```ts
useWorkflowQuery<T = unknown>(
  workflowId: string,
  params?: Record<string, unknown>,
  options?: { enabled?: boolean },
): {
  data: T | null;
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  /** @deprecated use errorMessage */
  error: string | null;
  logs: StreamingLog[];
  refetch: () => Promise<T>;
  executionId: string | null;
  status: ExecutionStatus | null;
}
```

Declarative workflow execution for page data. Use it when rendering the page should run the workflow: list pages, detail pages, dashboards, and reports. It executes on mount and re-executes when `params` change (`JSON.stringify(params ?? {})`, so object key order matters). Pass `{ enabled: false }` to gate execution.

`useWorkflowQuery` wraps `useWorkflowMutation`, so `executionId`, `status`, and `logs` behave the same way: `executionId` starts as `null`, becomes non-null after the execution is created, and stays as the latest execution ID for this hook. Use `useEffect` if you need to react when it appears.

```tsx
import { useWorkflowQuery, Alert, AlertDescription } from "bifrost";

const WF_LIST_CLIENTS = "uuid-here";

export default function Clients() {
  const { data, isLoading, isError, errorMessage, refetch } = useWorkflowQuery<{ items: any[] }>(WF_LIST_CLIENTS);
  if (isLoading) return <div>Loading…</div>;
  if (isError) return <Alert variant="destructive"><AlertDescription>{errorMessage}</AlertDescription></Alert>;
  return <ul>{data?.items?.map((c) => <li key={c.id}>{c.name}</li>)}</ul>;
}
```

## UI Components

Every name in this section is shadcn/ui compatible — the component re-exports `@/components/ui/<name>` from the host client. Props match shadcn/ui; see shadcn/ui docs for the full prop surface. Non-shadcn components (Combobox, MultiCombobox, TagsInput, DateRangePicker) have full signatures below.

### Accordion
Shadcn compatible. Composed of `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent`.
```tsx
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "bifrost";
<Accordion type="single" collapsible>
  <AccordionItem value="q1">
    <AccordionTrigger>Question?</AccordionTrigger>
    <AccordionContent>Answer.</AccordionContent>
  </AccordionItem>
</Accordion>
```

### AccordionContent
See `Accordion`.

### AccordionItem
See `Accordion`.

### AccordionTrigger
See `Accordion`.

### Alert
```tsx
import { Alert, AlertTitle, AlertDescription } from "bifrost";
<Alert variant="destructive"><AlertTitle>Error</AlertTitle><AlertDescription>Something broke</AlertDescription></Alert>
```
Variants: `default`, `destructive`.

### AlertDescription
See `Alert`.

### AlertAction
See `Alert`. Optional action slot rendered at the end of the alert (e.g. a dismiss or undo button).

### AlertDialogMedia
See `AlertDialog`. Optional icon/media slot rendered above the title (Rhea style).

### AlertDialog
Modal confirmation dialog. Composed of `AlertDialog`, `AlertDialogTrigger`, `AlertDialogContent`, `AlertDialogHeader`, `AlertDialogTitle`, `AlertDialogDescription`, `AlertDialogFooter`, `AlertDialogAction`, `AlertDialogCancel`.
```tsx
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogAction, AlertDialogCancel, Button } from "bifrost";
<AlertDialog>
  <AlertDialogTrigger asChild><Button variant="destructive">Delete</Button></AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader><AlertDialogTitle>Delete?</AlertDialogTitle><AlertDialogDescription>This cannot be undone.</AlertDialogDescription></AlertDialogHeader>
    <AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction onClick={doDelete}>Delete</AlertDialogAction></AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

### AlertDialogAction
See `AlertDialog`.

### AlertDialogCancel
See `AlertDialog`.

### AlertDialogContent
See `AlertDialog`.

### AlertDialogDescription
See `AlertDialog`.

### AlertDialogFooter
See `AlertDialog`.

### AlertDialogHeader
See `AlertDialog`.

### AlertDialogOverlay
See `AlertDialog`. Radix overlay primitive — rarely used directly.

### AlertDialogPortal
See `AlertDialog`. Radix portal primitive — rarely used directly.

### AlertDialogTitle
See `AlertDialog`.

### AlertDialogTrigger
See `AlertDialog`.

### AlertTitle
See `Alert`.

### Avatar
```tsx
import { Avatar, AvatarImage, AvatarFallback } from "bifrost";
<Avatar className="h-8 w-8"><AvatarImage src={user.avatar} /><AvatarFallback>{user.name[0]}</AvatarFallback></Avatar>
```

### AvatarFallback
See `Avatar`.

### AvatarImage
See `Avatar`.

### Badge
```tsx
import { Badge } from "bifrost";
<Badge variant="secondary">New</Badge>
```
Variants: `default`, `secondary`, `destructive`, `outline`.

### badgeVariants
Signature: `badgeVariants({ variant }): string` — class-variance-authority helper. Use when you need Badge classes on a non-Badge element.
```tsx
import { badgeVariants } from "bifrost";
<a className={badgeVariants({ variant: "outline" })}>click me</a>
```

### Button
```tsx
import { Button } from "bifrost";
<Button variant="default" size="default" onClick={save} disabled={isLoading}>Save</Button>
<Button asChild><a href="/x">Go</a></Button>
```
Variants: `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`. Sizes: `default`, `sm`, `lg`, `icon`.

### buttonVariants
Signature: `buttonVariants({ variant, size }): string` — CVA helper for Button classes on non-Button elements.

### Calendar
In the current runtime `Calendar` resolves to the Lucide `Calendar` icon (Lucide's full icon set is spread into the `$` registry; the shadcn calendar component is re-exported as `CalendarPicker` specifically so the Lucide icon can keep its natural name). For a date-picker component use `CalendarPicker`; for the icon prefer `import { Calendar } from "lucide-react"` explicitly.
```tsx
// Icon
import { Calendar } from "bifrost";   // equivalent to: import { Calendar } from "lucide-react"
<Calendar className="h-4 w-4" />
```

### CalendarDayButton
Signature: day-cell button used internally by the calendar. Rarely imported directly; available for custom day rendering.

### CalendarPicker
Alias of the shadcn Calendar component (re-exported from `@/components/ui/calendar`). Use when the platform `Calendar` isn't the primitive you want.
```tsx
import { CalendarPicker } from "bifrost";
<CalendarPicker mode="range" selected={range} onSelect={setRange} />
```

### Card
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, CardAction } from "bifrost";
<Card>
  <CardHeader><CardTitle>Clients</CardTitle><CardDescription>All active</CardDescription></CardHeader>
  <CardContent>…</CardContent>
  <CardFooter><Button>View all</Button></CardFooter>
</Card>
```

### CardAction
Slot for a right-aligned action in `CardHeader`.

### CardContent
See `Card`.

### CardDescription
See `Card`.

### CardFooter
See `Card`.

### CardHeader
See `Card`.

### CardTitle
See `Card`.

### Checkbox
```tsx
import { Checkbox } from "bifrost";
const [checked, setChecked] = useState(false);
<Checkbox checked={checked} onCheckedChange={(v) => setChecked(v === true)} />
```

### Collapsible
```tsx
import { Collapsible, CollapsibleTrigger, CollapsibleContent, Button } from "bifrost";
<Collapsible>
  <CollapsibleTrigger asChild><Button variant="ghost">Toggle</Button></CollapsibleTrigger>
  <CollapsibleContent>Hidden content</CollapsibleContent>
</Collapsible>
```

### CollapsibleContent
See `Collapsible`.

### CollapsibleTrigger
See `Collapsible`.

### Combobox

Platform-specific (not shadcn). Single-select searchable combobox.

Signature:
```ts
<Combobox
  value: string | undefined
  onChange: (value: string) => void
  options: { value: string; label: string }[]
  placeholder?: string
  emptyMessage?: string
  className?: string
/>
```

```tsx
import { Combobox } from "bifrost";
const [value, setValue] = useState<string>("");
<Combobox
  value={value}
  onChange={setValue}
  options={[{ value: "us", label: "United States" }, { value: "ca", label: "Canada" }]}
  placeholder="Pick a country"
/>
```

### Command
Command palette / search UI built on cmdk.
```tsx
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from "bifrost";
<Command>
  <CommandInput placeholder="Search…" />
  <CommandList>
    <CommandEmpty>No results.</CommandEmpty>
    <CommandGroup heading="Clients">
      <CommandItem onSelect={() => navigate("/clients/1")}>Acme</CommandItem>
    </CommandGroup>
  </CommandList>
</Command>
```

### CommandDialog
Command wrapped in a Dialog for modal palettes.

### CommandEmpty
See `Command`.

### CommandGroup
See `Command`.

### CommandInput
See `Command`.

### CommandItem
See `Command`.

### CommandList
See `Command`.

### CommandSeparator
See `Command`.

### CommandShortcut
Right-aligned keyboard shortcut hint inside a `CommandItem`.

### ContextMenu
Right-click menu. Composed of `ContextMenu`, `ContextMenuTrigger`, `ContextMenuContent`, `ContextMenuItem`, plus checkbox/radio/submenu variants.
```tsx
import { ContextMenu, ContextMenuTrigger, ContextMenuContent, ContextMenuItem } from "bifrost";
<ContextMenu>
  <ContextMenuTrigger>Right click me</ContextMenuTrigger>
  <ContextMenuContent>
    <ContextMenuItem onSelect={copy}>Copy</ContextMenuItem>
    <ContextMenuItem onSelect={del}>Delete</ContextMenuItem>
  </ContextMenuContent>
</ContextMenu>
```

### ContextMenuCheckboxItem
Checkbox variant of `ContextMenuItem`.

### ContextMenuContent
See `ContextMenu`.

### ContextMenuGroup
Semantic grouping inside `ContextMenuContent`.

### ContextMenuItem
See `ContextMenu`.

### ContextMenuLabel
Non-interactive label inside `ContextMenuContent`.

### ContextMenuPortal
Radix portal primitive for `ContextMenu`.

### ContextMenuRadioGroup
Radio-group container for `ContextMenuRadioItem`.

### ContextMenuRadioItem
Radio variant of `ContextMenuItem`.

### ContextMenuSeparator
Divider inside `ContextMenuContent`.

### ContextMenuShortcut
Right-aligned shortcut hint inside a `ContextMenuItem`.

### ContextMenuSub
Submenu wrapper.

### ContextMenuSubContent
Submenu content panel.

### ContextMenuSubTrigger
Submenu open trigger.

### ContextMenuTrigger
See `ContextMenu`.

### DateRangePicker

Platform-specific. Picks a `{ from, to }` date range.

Signature:
```ts
<DateRangePicker
  value: { from: Date | undefined; to?: Date | undefined } | undefined
  onChange: (range: DateRange | undefined) => void
  placeholder?: string
  className?: string
/>
```

```tsx
import { DateRangePicker } from "bifrost";
const [range, setRange] = useState<{ from: Date; to?: Date } | undefined>();
<DateRangePicker value={range} onChange={setRange} />
```

### Dialog
```tsx
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, Button } from "bifrost";
<Dialog>
  <DialogTrigger asChild><Button>Open</Button></DialogTrigger>
  <DialogContent>
    <DialogHeader><DialogTitle>Title</DialogTitle><DialogDescription>…</DialogDescription></DialogHeader>
    <div>Body</div>
    <DialogFooter><Button>Save</Button></DialogFooter>
  </DialogContent>
</Dialog>
```

### DialogClose
Close button inside `DialogContent`.

### DialogContent
See `Dialog`.

### DialogDescription
See `Dialog`.

### DialogFooter
See `Dialog`.

### DialogHeader
See `Dialog`.

### DialogOverlay
Radix overlay primitive — rarely used directly.

### DialogPortal
Radix portal primitive — rarely used directly.

### DialogTitle
See `Dialog`.

### DialogTrigger
See `Dialog`.

### DropdownMenu
```tsx
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, Button } from "bifrost";
<DropdownMenu>
  <DropdownMenuTrigger asChild><Button variant="ghost">⋯</Button></DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>Actions</DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem onSelect={edit}>Edit</DropdownMenuItem>
    <DropdownMenuItem onSelect={del}>Delete</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### DropdownMenuCheckboxItem
Checkbox variant of `DropdownMenuItem`.

### DropdownMenuContent
See `DropdownMenu`.

### DropdownMenuGroup
Semantic grouping inside `DropdownMenuContent`.

### DropdownMenuItem
See `DropdownMenu`.

### DropdownMenuLabel
Non-interactive label inside `DropdownMenuContent`.

### DropdownMenuPortal
Radix portal primitive for `DropdownMenu`.

### DropdownMenuRadioGroup
Radio-group container for `DropdownMenuRadioItem`.

### DropdownMenuRadioItem
Radio variant of `DropdownMenuItem`.

### DropdownMenuSeparator
Divider.

### DropdownMenuShortcut
Right-aligned shortcut hint.

### DropdownMenuSub
Submenu wrapper.

### DropdownMenuSubContent
Submenu content panel.

### DropdownMenuSubTrigger
Submenu open trigger.

### DropdownMenuTrigger
See `DropdownMenu`.

### HoverCard
Hover-triggered info card.
```tsx
import { HoverCard, HoverCardTrigger, HoverCardContent } from "bifrost";
<HoverCard>
  <HoverCardTrigger asChild><a href="#">@acme</a></HoverCardTrigger>
  <HoverCardContent>Acme Corp — 120 employees</HoverCardContent>
</HoverCard>
```

### HoverCardContent
See `HoverCard`.

### HoverCardTrigger
See `HoverCard`.

### Input
```tsx
import { Input } from "bifrost";
<Input value={v} onChange={(e) => setV(e.target.value)} placeholder="Name" />
```
Props match `<input>`; `type="text"` by default.

### Label
```tsx
import { Label, Input } from "bifrost";
<Label htmlFor="email">Email</Label>
<Input id="email" type="email" />
```

### MultiCombobox

Platform-specific. Multi-select searchable combobox.

Signature:
```ts
<MultiCombobox
  values: string[]
  onChange: (values: string[]) => void
  options: { value: string; label: string }[]
  placeholder?: string
  className?: string
/>
```

```tsx
import { MultiCombobox } from "bifrost";
const [tags, setTags] = useState<string[]>([]);
<MultiCombobox values={tags} onChange={setTags} options={tagOptions} placeholder="Tag this" />
```

### Pagination
Composed of `Pagination`, `PaginationContent`, `PaginationItem`, `PaginationLink`, `PaginationPrevious`, `PaginationNext`, `PaginationEllipsis`.
```tsx
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationPrevious, PaginationNext } from "bifrost";
<Pagination>
  <PaginationContent>
    <PaginationItem><PaginationPrevious href="#" /></PaginationItem>
    <PaginationItem><PaginationLink href="#" isActive>1</PaginationLink></PaginationItem>
    <PaginationItem><PaginationLink href="#">2</PaginationLink></PaginationItem>
    <PaginationItem><PaginationNext href="#" /></PaginationItem>
  </PaginationContent>
</Pagination>
```

### PaginationContent
See `Pagination`.

### PaginationEllipsis
See `Pagination`.

### PaginationItem
See `Pagination`.

### PaginationLink
See `Pagination`.

### PaginationNext
See `Pagination`.

### PaginationPrevious
See `Pagination`.

### Popover
```tsx
import { Popover, PopoverTrigger, PopoverContent, Button } from "bifrost";
<Popover>
  <PopoverTrigger asChild><Button>Open</Button></PopoverTrigger>
  <PopoverContent>Popover body</PopoverContent>
</Popover>
```

### PopoverAnchor
Virtual anchor element for a Popover.

### PopoverHeader
See `Popover`. Header block for structured popover content.

### PopoverTitle
See `Popover`.

### PopoverDescription
See `Popover`.

### PopoverContent
See `Popover`.

### PopoverTrigger
See `Popover`.

### Progress
```tsx
import { Progress } from "bifrost";
<Progress value={percent} />
```

### RadioGroup
```tsx
import { RadioGroup, RadioGroupItem, Label } from "bifrost";
<RadioGroup value={v} onValueChange={setV}>
  <div className="flex items-center gap-2"><RadioGroupItem value="a" id="a" /><Label htmlFor="a">A</Label></div>
  <div className="flex items-center gap-2"><RadioGroupItem value="b" id="b" /><Label htmlFor="b">B</Label></div>
</RadioGroup>
```

### RadioGroupItem
See `RadioGroup`.

### Select
```tsx
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "bifrost";
<Select value={v} onValueChange={setV}>
  <SelectTrigger><SelectValue placeholder="Pick one" /></SelectTrigger>
  <SelectContent>
    <SelectItem value="a">A</SelectItem>
    <SelectItem value="b">B</SelectItem>
  </SelectContent>
</Select>
```

### SelectContent
See `Select`.

### SelectGroup
Groups `SelectItem`s under an optional `SelectLabel`.

### SelectItem
See `Select`.

### SelectLabel
Non-interactive group label inside `SelectContent`.

### SelectScrollDownButton
Auto-inserted scroll button — rarely used directly.

### SelectScrollUpButton
Auto-inserted scroll button — rarely used directly.

### SelectSeparator
Divider inside `SelectContent`.

### SelectTrigger
See `Select`.

### SelectValue
See `Select`.

### Separator
```tsx
import { Separator } from "bifrost";
<Separator orientation="horizontal" />
```

### Sheet
Side drawer. Composed of `Sheet`, `SheetTrigger`, `SheetContent`, `SheetHeader`, `SheetTitle`, `SheetDescription`, `SheetFooter`, `SheetClose`.
```tsx
import { Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle, Button } from "bifrost";
<Sheet>
  <SheetTrigger asChild><Button>Open drawer</Button></SheetTrigger>
  <SheetContent side="right">
    <SheetHeader><SheetTitle>Filters</SheetTitle></SheetHeader>
    …
  </SheetContent>
</Sheet>
```

### SheetClose
See `Sheet`.

### SheetContent
See `Sheet`. `side`: `"top" | "right" | "bottom" | "left"` (default `right`).

### SheetDescription
See `Sheet`.

### SheetFooter
See `Sheet`.

### SheetHeader
See `Sheet`.

### SheetTitle
See `Sheet`.

### SheetTrigger
See `Sheet`.

### Skeleton
Loading placeholder.
```tsx
import { Skeleton } from "bifrost";
<Skeleton className="h-4 w-32" />
```

### Slider
```tsx
import { Slider } from "bifrost";
<Slider value={[val]} onValueChange={(v) => setVal(v[0])} min={0} max={100} step={1} />
```

### Switch
```tsx
import { Switch } from "bifrost";
<Switch checked={on} onCheckedChange={setOn} />
```

### Table
```tsx
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableCaption, TableFooter } from "bifrost";
<Table>
  <TableCaption>Clients</TableCaption>
  <TableHeader>
    <TableRow><TableHead>Name</TableHead><TableHead>Status</TableHead></TableRow>
  </TableHeader>
  <TableBody>
    {rows.map((r) => <TableRow key={r.id}><TableCell>{r.name}</TableCell><TableCell>{r.status}</TableCell></TableRow>)}
  </TableBody>
</Table>
```

### TableBody
See `Table`.

### TableCaption
See `Table`.

### TableCell
See `Table`.

### TableFooter
See `Table`.

### TableHead
See `Table`.

### TableHeader
See `Table`.

### TableRow
See `Table`.

### Tabs
```tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from "bifrost";
<Tabs defaultValue="overview">
  <TabsList><TabsTrigger value="overview">Overview</TabsTrigger><TabsTrigger value="logs">Logs</TabsTrigger></TabsList>
  <TabsContent value="overview">…</TabsContent>
  <TabsContent value="logs">…</TabsContent>
</Tabs>
```

### TabsContent
See `Tabs`.

### TabsList
See `Tabs`.

### tabsListVariants
See `Tabs`. `cva` variants helper for styling custom elements like a `TabsList`.

### TabsTrigger
See `Tabs`.

### TagsInput

Platform-specific. Free-form multi-value text input (chips).

Signature:
```ts
<TagsInput
  value: string[]
  onChange: (tags: string[]) => void
  placeholder?: string
  className?: string
/>
```

```tsx
import { TagsInput } from "bifrost";
const [emails, setEmails] = useState<string[]>([]);
<TagsInput value={emails} onChange={setEmails} placeholder="Add email…" />
```

### Textarea
```tsx
import { Textarea } from "bifrost";
<Textarea value={v} onChange={(e) => setV(e.target.value)} rows={4} />
```

### Toggle
Binary pressed/unpressed toggle button.
```tsx
import { Toggle } from "bifrost";
<Toggle pressed={on} onPressedChange={setOn} aria-label="Bold">B</Toggle>
```

### toggleVariants
CVA helper for Toggle classes. Signature: `toggleVariants({ variant, size }): string`.

### ToggleGroup
Radio-group-style toggles.
```tsx
import { ToggleGroup, ToggleGroupItem } from "bifrost";
<ToggleGroup type="single" value={align} onValueChange={setAlign}>
  <ToggleGroupItem value="left">Left</ToggleGroupItem>
  <ToggleGroupItem value="center">Center</ToggleGroupItem>
  <ToggleGroupItem value="right">Right</ToggleGroupItem>
</ToggleGroup>
```

### ToggleGroupItem
See `ToggleGroup`.

### Tooltip
```tsx
import { Tooltip, TooltipProvider, TooltipTrigger, TooltipContent, Button } from "bifrost";
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild><Button variant="ghost">?</Button></TooltipTrigger>
    <TooltipContent>Help text</TooltipContent>
  </Tooltip>
</TooltipProvider>
```

### TooltipContent
See `Tooltip`.

### TooltipProvider
Wraps a subtree where `Tooltip`s may appear.

### TooltipTrigger
See `Tooltip`.

## Utilities

### clsx

Signature: `clsx(...inputs: ClassValue[]): string` — conditional class joiner (re-export of `clsx`).
```tsx
import { clsx } from "bifrost";
<div className={clsx("base", isActive && "active", { disabled: !on })} />
```

### cn

Signature: `cn(...inputs: ClassValue[]): string` — `clsx` + `tailwind-merge`; dedupes conflicting Tailwind classes.
```tsx
import { cn } from "bifrost";
<div className={cn("px-2 py-1", props.className, isActive && "bg-accent")} />
```

### format

Signature: `format(date: Date | number, format: string, options?): string` — re-export of `date-fns/format`.
```tsx
import { format } from "bifrost";
format(new Date(), "yyyy-MM-dd"); // "2026-04-16"
```

### formatBytes

Signature: `formatBytes(bytes: number, decimals?: number): string`.
```tsx
import { formatBytes } from "bifrost";
formatBytes(1536);     // "1.5 KB"
formatBytes(1048576);  // "1 MB"
```

### formatCost

Signature: `formatCost(cost: string | number | null | undefined): string` — currency formatter that scales precision by magnitude. Returns `"N/A"` for null/undefined.
```tsx
import { formatCost } from "bifrost";
formatCost(0.0012);  // "$0.001200"
formatCost(42.5);    // "$42.50"
formatCost(null);    // "N/A"
```

### formatDate

Signature: `formatDate(dateString: string | Date, options?: Intl.DateTimeFormatOptions): string` — locale-aware date+time, parses UTC ISO strings from the backend.
```tsx
import { formatDate } from "bifrost";
formatDate("2026-04-16T14:30:00");  // "Apr 16, 2026, 02:30:00 PM" (in user timezone)
```

### formatDateShort

Signature: `formatDateShort(dateString: string | Date): string` — `"Jan 15, 2025"`-style date only.
```tsx
import { formatDateShort } from "bifrost";
formatDateShort(new Date());  // "Apr 16, 2026"
```

### parseBackendDate

Signature: `parseBackendDate(value: string): Date`. Parses backend timestamps safely: naive-UTC isoformat strings (no `Z`/offset, as emitted by Python `isoformat()`) are interpreted as UTC instead of local time. Use this instead of `new Date(...)` for any API timestamp.

### formatDuration

Signature: `formatDuration(ms: number | null | undefined): string`. Returns `"N/A"` for null.
```tsx
import { formatDuration } from "bifrost";
formatDuration(450);    // "450ms"
formatDuration(2340);   // "2.34s"
```

### formatNumber

Signature: `formatNumber(num: number): string` — locale-aware thousands separators.
```tsx
import { formatNumber } from "bifrost";
formatNumber(1234567);  // "1,234,567"
```

### formatRelativeTime

Signature: `formatRelativeTime(dateString: string | Date): string` — `"2 hours ago"` / `"in 3 days"`.
```tsx
import { formatRelativeTime } from "bifrost";
formatRelativeTime(new Date(Date.now() - 60_000));  // "1 min ago"
```

### formatTime

Signature: `formatTime(dateString: string | Date): string` — `"03:45:12 PM"`-style time only.
```tsx
import { formatTime } from "bifrost";
formatTime(new Date());  // "02:30:00 PM"
```

### toast

Signature:
```ts
toast.success(message: string, options?): string | number
toast.error(message: string, options?): string | number
toast.info(message: string, options?): string | number
toast.warning(message: string, options?): string | number
toast(message: string, options?): string | number   // default
toast.promise(promise, { loading, success, error }): Promise
toast.dismiss(id?): void
```

Uses `sonner` under the hood. The host app renders `<Toaster />` — just call `toast.*`.

```tsx
import { toast } from "bifrost";
toast.success("Saved");
toast.error("Could not load");
toast.promise(saveClient(), { loading: "Saving…", success: "Saved", error: "Failed" });
```

### twMerge

Signature: `twMerge(...classLists: string[]): string` — dedupes/conflict-resolves Tailwind classes. Used internally by `cn`.
```tsx
import { twMerge } from "bifrost";
twMerge("px-2 px-4");  // "px-4"
```

### tables

Web SDK for the Bifrost Tables API. Direct browser-to-API calls, no workflow required.

Surface (one-line each):
- `tables.get(table, id)` — fetch one row by id
- `tables.insert(table, data | dataArray)` — single object → one row; array → batch
- `tables.update(table, id, data)` — patch one row
- `tables.upsert(table, item | itemArray)` — insert-or-update; array → batch
- `tables.delete(table, id | idArray)` — delete one row OR a batch by ids
- `tables.query(table, query?)` — list with filter/limit/offset
- `tables.count(table)` — count rows
- `tables.subscribe(tableId, filter, onEvent)` — live updates (lower-level; prefer `useTable`)

```tsx
import { tables, useTable } from "bifrost";

// Single insert
await tables.insert("clients", { name: "Acme", status: "active" });

// Batch insert
await tables.insert("clients", [
  { data: { name: "A" } },
  { data: { name: "B" } },
]);

// Live query — preferred React surface
const { rows, loading, error } = useTable("clients", {
  where: { status: "active" },
});
```

**Prerequisite:** the table must have policies that grant the action. A freshly-created table is seeded with an `admin_bypass` policy — admins work, but non-admins are denied unless other policies grant them access. Edit the table's policies in the admin UI (Tables → click table → Policies) or via the API.

**SDK vs Workflow:**
- **SDK** (`tables.*`, `useTable`) — when policies allow the user; lower latency; no execution record. Use for browser apps doing CRUD on policy-gated rows.
- **Workflow** — complex multi-step logic, side effects, state-transition guards. Note that policies are checked against the **pre-update** state, so policies cannot enforce "can't unfinalize" — use a workflow for that.

If you're about to write a workflow just to read/write a table, configure the policies and use the SDK directly.

### useTable

Signature: `useTable(name: string, query?: { where?: DocumentFilter; page?: number; pageSize?: number; order_by?: string; order_dir?: "asc" | "desc"; scope?: string }): { rows: TableRow[]; total: number; totalPages: number; loading: boolean; error: Error | null }`.

Live-updating table data hook with **page-based pagination**. Loads a snapshot of `page` (1-indexed, default 1) at `pageSize` rows per page (default 100, server cap 1000) via `tables.query` and subscribes to live changes via `tables.subscribe`, applying `insert` / `update` / `delete` events to the visible page window. The hook compiles `where` into the policy `Expr` AST internally before passing to subscribe, so the websocket fanout sees the same row visibility as the snapshot.

Returns:
- `rows` — current page only.
- `total` — count of matching rows across all pages.
- `totalPages` — `Math.ceil(total / pageSize)`, or `0` for empty tables.
- `loading`, `error`.

For "Page X of Y" UI, drive `page` from local state and read `totalPages` from the result. For "more on the server" detection, use `rows.length < total`.

Rows are returned in a **flat** shape — JSONB `data` fields (e.g. `status`, `assignee`) are spread at the top level alongside column-mapped fields (`id`, `created_by`, `updated_by`, `created_at`, `updated_at`, `table_id`). This matches the shape websocket events deliver, so live updates merge cleanly with the snapshot.

The `where` filter uses the **dict-shorthand DSL** — same shape the Python SDK uses. Examples:

```tsx
useTable("notes",    { where: { client_id: clientId } });
useTable("invoices", { where: { amount: { gte: 100, lt: 1000 } } });
useTable("clients",  { where: { name: "Acme" } });
useTable("tickets",  { where: { status: { in: ["open", "pending"] } } });
useTable("tasks",    { where: { deleted_at: { is_null: true } } });
```

Live `useTable.where` supports: equality shorthand, `eq`, `neq` / `ne`, `gt`, `gte`, `lt`, `lte`, `in`, and `is_null`. Query-only operators `contains`, `starts_with`, `ends_with`, and `has_key` work with `tables.query` but cannot be represented as the live subscription policy `Expr`; using them in `useTable.where` raises a clear error via `error`.

```tsx
const matches = await tables.query("clients", {
  where: { name: { contains: "acme" } },
});
```

```tsx
import { useTable } from "bifrost";

export default function Tasks() {
  const { rows, loading, error } = useTable("my_tasks", {
    where: { status: "open" },
    order_by: "created_at",
    order_dir: "desc",
  });
  if (loading) return <div>Loading…</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <ul>{rows.map((r) => <li key={r.id}>{r.title as string}</li>)}</ul>;
}
```

The hook respects table policies — `rows` only contains rows the policies allow the current user to read. Inserts that transition into visibility appear; updates that transition out generate `delete` events.

**Scope.** When called inside an org-scoped app (`app.organization_id` is set), `scope` defaults to the app's org — same convention as org-scoped workflows always running as their org. Global apps fall back to caller's-org behavior. Pass `scope` explicitly to override (provider admins only).

**Subscribe errors.** If the server rejects the subscribe (table not found / policy denied / unsupported `where` operator), the rejection is surfaced via `error` rather than silently dropped. Before, this case looked like "snapshot loaded fine, no live updates ever arrive" — now it's a visible failure.

### useInfiniteTable

Signature: `useInfiniteTable(name: string, query?: { where?: DocumentFilter; pageSize?: number; order_by?: string; order_dir?: "asc" | "desc"; scope?: string }): { rows: TableRow[]; loadMore: () => Promise<void>; hasMore: boolean; loading: boolean; error: Error | null }`.

Same DSL as `useTable` but **accumulates** pages on demand for "Load more" / infinite-scroll UI. Each `loadMore()` call appends the next page to `rows`. The first page fetches with a count; subsequent pages set `skip_count: true` automatically for speed. Pages stop when a partial page comes back (`hasMore` flips false). Live updates apply to whatever's been loaded.

```tsx
import { useInfiniteTable } from "bifrost";

export default function Contacts() {
  const { rows, loadMore, hasMore, loading } = useInfiniteTable("contacts", {
    pageSize: 100,
  });
  return (
    <>
      <ul>{rows.map((r) => <li key={r.id}>{r.name as string}</li>)}</ul>
      {hasMore && <button onClick={loadMore} disabled={loading}>Load more</button>}
    </>
  );
}
```

Pick `useTable` for "Page X of Y" numbered-page UI; pick `useInfiniteTable` for "Load more" / infinite-scroll. Both wire live updates the same way.

### files

Web SDK for the Bifrost Files API. Direct browser-to-API file reads/writes, no workflow required — the mirror of `tables.*` for blob storage.

Surface (one-line each):
- `files.read(path, options?)` — read a text file, returns the decoded string
- `files.readBytes(path, options?)` — read a file as a `Uint8Array`
- `files.write(path, text, options?)` — write a text file
- `files.writeBytes(path, bytes, options?)` — write binary content
- `files.delete(path, options?)` — delete a file
- `files.list(prefix, options?)` — list files under a prefix (optionally with metadata)
- `files.exists(path, options?)` — existence check
- `files.signedUrl(path, options?)` — one presigned `PUT`/`GET` URL for direct-to-storage transfer
- `files.signedUrls(paths, options?)` — batch presigned URLs
- `files.upload(path, blob, options?)` — presign + PUT + finalize an upload in one call
- `files.download(path, options?)` — presign + GET a file as a `Blob`

`options` carries `location` (`"workspace"` default, plus `"uploads"`, `"temp"`, `"shared"`, …), `mode` (`"local"` | `"cloud"`), and `scope` (org id; defaults to the app's org inside an org-scoped app, same convention as `useTable`).

```tsx
import { files, useFiles } from "bifrost";

// Direct upload to shared storage (presign → PUT → finalize)
await files.upload("gallery/logo.png", fileBlob, { location: "shared" });

// Read it back as text
const readme = await files.read("gallery/README.md", { location: "shared" });

// Live listing — preferred React surface
const { files: names, loading, denied } = useFiles("gallery", { location: "shared" });
```

**Prerequisite:** the location/prefix must have a **file policy** that grants the action. Files are **default-deny** — with no matching policy the API returns 403 (read/write/delete/list) so an un-policied app surface fails closed. Create policies in the admin UI (Files → Policies) or via `bifrost files policies` / the REST endpoint. Policies reuse the same evaluator as table policies (`{user}`, `{claims}`, `has_role`, Custom Claims) plus a `{file: …}` resolver.

**SDK vs Workflow:** same trade-off as tables — use `files.*` / `useFiles` when policies allow the user directly (lower latency, no execution record); use a workflow for multi-step logic or side effects. Direct SDK file operations do **not** create workflow executions.

### useFiles

Signature: `useFiles(prefix: string, options?: { location?: string; mode?: "local" | "cloud"; scope?: string | null; includeMetadata?: boolean }): { files: string[]; filesMetadata: FileListMetadataItem[]; loading: boolean; error: Error | null; denied: boolean; empty: boolean; refetch: () => Promise<void> }`.

Live-updating file-listing hook — the files mirror of `useTable`. Loads the listing under `prefix` via `files.list` and subscribes to live change events (`files:{location}:{prefix}`) so uploads/deletes by anyone the policy permits refresh the list in place.

Returns:
- `files` — file paths under the prefix.
- `filesMetadata` — per-file metadata (etag, size, …) when `includeMetadata` is set.
- `denied` — `true` when the policy denies listing (distinct from `empty`, an allowed-but-empty folder).
- `empty` — `true` for an allowed folder with no files.
- `loading`, `error`, `refetch`.

```tsx
import { useFiles } from "bifrost";

export default function Gallery() {
  const { files, loading, denied, empty } = useFiles("gallery", { location: "shared" });
  if (loading) return <div>Loading…</div>;
  if (denied) return <div>You don't have access to this folder.</div>;
  if (empty) return <div>No files yet.</div>;
  return <ul>{files.map((f) => <li key={f}>{f}</li>)}</ul>;
}
```

**Scope.** Same convention as `useTable`: inside an org-scoped app `scope` defaults to the app's org; pass `scope` explicitly to override (provider admins only).

**Subscribe errors / revocation.** If the server rejects or revokes the file subscription (policy denied), `denied` flips and the listing stops — a visible failure rather than a silently-stale list.

## Global Built-ins

JavaScript built-in constructors are exposed on the bifrost scope to win the spread order over Lucide icons of the same name. Without this, a bare `new Map()` in user code would resolve to the Lucide `Map` icon (a React component, not a constructor) and crash at runtime with `TypeError: Map2 is not a constructor`.

Importing these from `"bifrost"` is rare — they're already global. The entries exist so the bare references resolve correctly.

### Map

The native `Map` constructor (`globalThis.Map`). Without this entry, Lucide's `Map` icon would shadow it inside the platform scope. `import { Map } from "bifrost"` resolves to the constructor; for the icon, import a more specific name (e.g. `MapPin`) or import from `"lucide-react"` directly.

### Set

The native `Set` constructor (`globalThis.Set`). Lucide also ships a `Set` icon — same shadowing concern as `Map`.

### WeakMap

The native `WeakMap` constructor (`globalThis.WeakMap`). Re-asserted for symmetry with `Map`.

### WeakSet

The native `WeakSet` constructor (`globalThis.WeakSet`). Re-asserted for symmetry with `Set`.

### Date

The native `Date` constructor (`globalThis.Date`). Lucide ships a `Calendar`-adjacent icon set — re-asserted to keep `new Date()` resolving to the constructor.
