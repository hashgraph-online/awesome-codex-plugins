# React Patterns & Standards

Shared React patterns for all React-based projects (standalone, Vite, Raycast, Next.js). Referenced by the frontend-dev skill during Research and Implementation phases.

---

## Review Standards

Enforce these during Staff Engineer Review (Phase 4):

- Hooks follow Rules of Hooks (no conditional hooks, no hooks in loops)
- Components decomposed (< 70 lines each, single responsibility)
- State management appropriate — local state for UI, context/stores for shared state
- No premature memoization (`useMemo`/`useCallback` only when profiling shows need)
- Props typed with TypeScript — inline for simple, separate type for complex/reusable
- Props order: non-function fields first, callbacks last
- One component per file; modals/dialogs always in their own file (never inline in parent)
- Event handlers named with `handle` prefix (`handleClick`, `handleSubmit`)
- Custom hooks extract reusable logic — named with `use` prefix
- User-triggered async ops use the framework's loading-toast idiom — not local `isLoading` + spinner state
- Styling: see [styling.md](styling.md) when project uses Tailwind / CSS-in-JS / CSS Modules
- Radix / shadcn: see [shadcn.md](shadcn.md) when project uses Radix primitives or `components/ui/`
- No `any` types
- No direct DOM manipulation — use refs when necessary

---

## Component Patterns

### Props Typing

```tsx
// Inline type for simple components
function Button({ label, onClick }: { label: string; onClick: () => void }) {
  return <button onClick={onClick}>{label}</button>;
}

// Separate type for complex/reusable components
type CardProps = {
  title: string;
  children: React.ReactNode;
  variant?: "default" | "outlined";
};

function Card({ title, children, variant = "default" }: CardProps) {
  return <div className={variant}><h2>{title}</h2>{children}</div>;
}

// Extend HTML element props
type ButtonProps = React.ComponentProps<"button"> & {
  variant?: "primary" | "secondary";
};

function Button({ variant = "primary", ...props }: ButtonProps) {
  return <button className={variant} {...props} />;
}
```

---

## Component file structure

- **One component per file.** When a component grows sub-components, create a directory with one file per component and an `index.tsx` that assembles them (e.g. `MyComponent/index.tsx`, `MyComponent/Header.tsx`, `MyComponent/List.tsx`). Don't keep multiple top-level components in one file.
- **Modals and dialogs always in their own file.** Never inline a modal inside its parent component — even a small confirm dialog. An inline modal is a refactoring cue, not a shortcut.
- **Providers go as high in the tree as the state they hold** (root layout, page entry, feature root) — not nested inside the consumer.
- **Props order: non-function fields first, callbacks last.** Group the data the component shows, then the callbacks it fires.

```tsx
// Good
type Props = {
  open: boolean;
  user: User;
  onClose: () => void;
  onSave: (user: User) => void;
};

// Bad — callbacks scattered between data
type Props = {
  open: boolean;
  onClose: () => void;
  user: User;
  onSave: (user: User) => void;
};
```

---

## Watch the state surface area

When a component reads state that serves multiple unrelated purposes — e.g., filter values _and_ table configuration _and_ dialog state — each group of related reads likely belongs in its own sub-component. A component reading many pieces of state for one cohesive purpose (e.g., a form reading all its field values) is fine. The signal is unrelated concerns mixing, not the raw count.

---

## Keep the return statement clean

The `return` should be easy to scan. Minimize logic inlined in JSX:

- **Inline callbacks**: only single short expressions (e.g. `onClick={() => setOpen(true)}`). Anything longer belongs in a named function or hook.
- **Conditional rendering**: `{condition && <X />}` or a simple ternary is fine. Nested ternaries or multi-branch logic should be extracted to a variable or sub-component.
- **Computed values**: extract to a `const` above the return if the expression involves template literals with logic, chained `??`/`?` operators, or formatting.

---

## Hooks Patterns

### Custom Hooks

```tsx
// Extract reusable logic into custom hooks
function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : initialValue;
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue] as const;
}

// Async data hook
function useFetch<T>(url: string) {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });

    fetch(url)
      .then(res => res.json())
      .then(data => { if (!cancelled) setState({ status: "success", data }); })
      .catch(error => { if (!cancelled) setState({ status: "error", error }); });

    return () => { cancelled = true; };
  }, [url]);

  return state;
}
```

### Rules of Hooks

```tsx
// GOOD: Hooks at top level, always called
function Component({ showDetails }: { showDetails: boolean }) {
  const [count, setCount] = useState(0);
  const data = useFetch("/api/data");

  if (!showDetails) return null;
  return <div>{count} - {JSON.stringify(data)}</div>;
}

// BAD: Conditional hook
function Component({ showDetails }: { showDetails: boolean }) {
  if (showDetails) {
    const [count, setCount] = useState(0); // VIOLATION
  }
}
```

---

## Avoid unnecessary `useEffect`

Before writing an Effect, ask: _"Is this running because the component was displayed, or because a specific event happened?"_ If an event caused it, the logic belongs in an event handler — not an Effect.

| Instead of...                                               | Do this                                                                   |
| ----------------------------------------------------------- | ------------------------------------------------------------------------- |
| Effect that derives state from props/state                  | Compute it during render (`const x = fn(a, b)`) or `useMemo` if expensive |
| Effect that resets state when a prop changes                | Use a `key` prop to remount the component                                 |
| Effect that syncs state to a parent via `onChange`          | Call `onChange` in the same event handler that updates local state        |
| Effect that fires an API call after a state change          | Call the API directly in the event handler that caused the state change   |
| Chain of Effects where one sets state that triggers another | Compute all state updates in a single event handler                       |

Legitimate uses: subscriptions to external systems (WebSocket, browser API, third-party library), data fetching on mount/param change (with cleanup), synchronizing with non-React DOM (e.g. a map or chart widget).

---

## State Management

### When to Use What

```
Local state (useState):        UI state — modals, tabs, form inputs
Derived state (useMemo):       Computed from existing state/props
Context (createContext):        Theme, auth, locale — read by many, updated rarely
External store (Zustand/Redux): Complex shared state, frequent updates, DevTools needed
URL state (searchParams):       Filters, pagination, shareable state
```

### React Context

```tsx
"use client"; // Only needed in Next.js

import { createContext, useContext, useState, ReactNode } from "react";

type Theme = "light" | "dark";

const ThemeContext = createContext<{
  theme: Theme;
  toggle: () => void;
} | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");
  const toggle = () => setTheme(t => (t === "light" ? "dark" : "light"));

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
}
```

---

## Async user feedback

For operations the user explicitly triggered (button click, form submit, drag-drop), use the framework's loading-toast / snackbar idiom — never roll a local `isLoading` state with a spinner.

Why: spinners scattered through the UI compound when multiple operations run; a global toast surface gives one consistent place to see progress, success, and failure. It also forces error handling — every loading toast must terminate in success or error, which makes silent failures impossible to ignore.

```typescript
// Good — single source of feedback, error path explicit
const toastId = toast.loading("Saving changes");

try {
  const res = await save(data);

  if (!res.ok) {
    toast.error("Save failed", { id: toastId });
    return;
  }

  toast.success("Changes saved", { id: toastId });
} catch (err) {
  toast.error("Save failed", { id: toastId });
  reportError(err);
}

// Bad — local state, easy to forget the error branch
const [isSaving, setIsSaving] = useState(false);

async function handleSave() {
  setIsSaving(true);
  await save(data);
  setIsSaving(false);
}
```

The exact API differs by library (sonner, react-hot-toast, MUI Snackbar, Radix Toast) — pick one per project and use it for every user-triggered async op.

Loading messages: gerund form, no trailing `"..."`, no "in progress" — `"Saving changes"`, not `"Saving... please wait"`.

---

## Demand-loaded patterns

Two adjacent pattern files are loaded on detection, not by default — keeps `react.md` lean for projects that don't use these stacks:

- **[styling.md](styling.md)** — read if the project uses Tailwind, CSS-in-JS (MUI, Chakra, Mantine, Emotion, styled-components), or CSS Modules. Covers `cn()`/`clsx()` for conditional classes, mixing Tailwind + component-library styles via `@layer` order.
- **[shadcn.md](shadcn.md)** — read if `@radix-ui/*` is in deps, `components/ui/` exists, or a `components.json` shadcn config is at the project root. Covers controlled-vs-uncontrolled Radix state and the `shadcn add` overwrite caveat.

---

## Testing

### Component Tests with @testing-library/react

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "./Button";

describe("Button", () => {
  it("renders with label", () => {
    render(<Button label="Click me" onClick={() => {}} />);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const handleClick = vi.fn();
    render(<Button label="Click" onClick={handleClick} />);
    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Testing Hooks

```tsx
import { renderHook, act } from "@testing-library/react";
import { useCounter } from "./useCounter";

describe("useCounter", () => {
  it("increments count", () => {
    const { result } = renderHook(() => useCounter());
    act(() => result.current.increment());
    expect(result.current.count).toBe(1);
  });
});
```

---

## Quick Reference

| Need | Do This |
|------|---------|
| Type component props | Inline type or separate type |
| Extend HTML props | `React.ComponentProps<"element">` |
| Reusable logic | Custom hook with `use` prefix |
| Share state across tree | React Context or external store |
| URL-based state | URLSearchParams |
| User-triggered async feedback | Loading-toast idiom — never local `isLoading` |
| Test component | @testing-library/react with `render`, `screen` |
| Test hook | `renderHook` from @testing-library/react |

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| Giant components (> 70 lines) | Split into smaller, focused components |
| Inline modal in parent component | Modal in its own file |
| Barrel exports for everything | Direct imports, barrel only for public API |
| `useEffect` for derived state or event responses | See "Avoid unnecessary useEffect" section above |
| Premature `useMemo`/`useCallback` | Profile first, optimize when measured |
| Prop drilling through 3+ levels | Context or composition pattern |
| Local `isLoading` + spinner for user-triggered async | Loading-toast idiom |

See also: [typescript.md](typescript.md) for TypeScript-specific anti-patterns (`any`, `@ts-ignore`, etc.). Styling and Radix/shadcn anti-patterns live in [styling.md](styling.md) and [shadcn.md](shadcn.md) respectively (demand-loaded).
