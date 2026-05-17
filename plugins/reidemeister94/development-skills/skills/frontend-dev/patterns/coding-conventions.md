# Coding Conventions

Framework-agnostic rules — readability, structure, type safety, comments, naming. Loaded alongside `typescript.md` for every framework. Referenced by the frontend-dev skill during Research and Implementation phases.

The "What NOT to Do" table at the end of this file is the single summary — Phase 4 staff review checks each row. Don't expect a separate up-front checklist; the rules ARE the headings of each section below.

---

## Files & Structure

### One responsibility per file

A file's name should describe everything in it. If you'd reach for a generic name like `utils.ts`, `helpers.ts`, or `misc.ts` — split the file. The same applies if you'd add a section divider comment to organise it: that divider is a "this file should be two files" signal.

When extracting from a large file, place each distinct concern (columns, formatters, hooks, validators) in its own file rather than grouping unrelated logic by proximity.

### Filenames in English

Even when the domain uses non-English terms in UI copy, data fields, or identifiers, filenames are always English (e.g. `ApplyToProductionButton.tsx`, not `ApplicaProduzioneButton.tsx`). Mixed-language filenames break grep, IDE search, and onboarding.

### No section dividers

Never use `// ---`, `// ===`, `// ------`, `// === SECTION ===` etc. inside files. If a file needs visual separation between groups, it should be split. Inside a React component, section dividers signal the component needs decomposition into sub-components.

---

## Naming

### Variable names must convey purpose

Single-letter names are acceptable only in tightly-scoped iterations (`arr.map((x) => x.id)` is fine; a long block where `x` survives is not). Names describe purpose, not type:

```typescript
// Good
const productivityRate = computeProductivity(machine, hours);
const activeCampaigns = campaigns.filter(c => c.active);

// Bad
const p = computeProductivity(machine, hours);
const data = campaigns.filter(c => c.active);
```

### Single source of truth for repeated literals

When the same literal value appears in multiple places, extract to a named constant and reference it everywhere. Default param objects, magic numbers, status strings, column keys — anywhere a value is duplicated, it must be referenced, not duplicated.

### No unnecessary import aliases

Don't rename on import unless there's a real collision in the file. `import { Button as ActionButton }` is noise when no other `Button` is in scope.

---

## Types

### No `!` non-null assertions; no `as` casts

Narrow with `if` guards:

```typescript
// Good
const week = weeks[i];

if (week === undefined) {
  continue;
}

doStuff(week);

// Bad
doStuff(weeks[i]!);
```

```typescript
// Good — annotate the receiver
const result: MyType = computeResult();

// Bad — cast the producer
const result = computeResult() as MyType;
```

`as` is acceptable in two narrow cases: `as const` for literal narrowing, and `satisfies` patterns. Everywhere else, fix the source type or use a type guard.

### Schema-first across trust boundaries

For any data crossing a trust boundary (API responses, URL/query params, `JSON.parse` results, persist rehydration), define a schema (Zod, Valibot, ArkType, io-ts) and derive the TypeScript type via `z.infer`. **Never write a manual `type`/`interface` for boundary data** — the runtime check and the static type must come from the same source.

```typescript
// Good — schema is source of truth
const UserSchema = z.object({ id: z.string(), name: z.string() });
type User = z.infer<typeof UserSchema>;

const data = UserSchema.parse(json); // validated + typed

// Bad — manual type, no runtime check
type User = { id: string; name: string };
const data = json as User;
```

For purely internal types that never cross a boundary, plain `type`/`interface` is fine — the validation cost isn't justified.

---

## Operations

### Prefer immutable array methods

Use `toSorted()`, `toReversed()`, `toSpliced()` over `sort()`, `reverse()`, `splice()`. The mutating versions modify the array in place, causing bugs when callers don't expect it.

```typescript
// Good
const sorted = items.toSorted((a, b) => a.id - b.id);

// Bad — mutates the array passed in
items.sort((a, b) => a.id - b.id);
doSomething(items); // items is now sorted, surprise
```

---

## Formatting

### No nested ternaries

A single ternary (`condition ? a : b`) is fine. Chained ternaries are not — extract to a function with early returns:

```typescript
// Good
function statusLabel(status: Status): string {
  if (status === "active") return "Active";
  if (status === "paused") return "Paused";
  if (status === "archived") return "Archived";
  return "Unknown";
}

// Bad
const label = status === "active" ? "Active"
  : status === "paused" ? "Paused"
  : status === "archived" ? "Archived"
  : "Unknown";
```

### Blank lines around control flow

```typescript
// Good
const value = getValue();

if (value === null) {
  return null;
}

doSomething(value);

// Bad
const value = getValue();
if (value === null) return null;
doSomething(value);
```

Curly braces required on `if`/`else`. Bodies on a new line — never single-line `if (x) return`.

---

## Comments

Before writing ANY comment, apply this filter:

1. **Would removing the comment lose information?** If the name/code already says it → no comment.
2. **Does it explain WHY, not WHAT?** Workarounds, non-obvious constraints, business rules → comment.
3. **Is it on a constant/variable with a descriptive name?** → No comment. The name is the doc.

Common traps:

- Commenting constants with meaningful names (`TOLERANCE = 0.05` needs no "tolerance for matching" comment)
- JSDoc body that enumerates code branches ("if X returns Y, if Z returns W")
- Restating the function signature in prose ("takes an array and returns a new array")

No spec/ticket references in code — they belong in commit messages or PR descriptions.

---

## JSDoc

- JSDoc on functions only (`@param`/`@returns`). **No JSDoc on React components.**
- **One sentence** describing what the function does. No second sentence restating branches or edge cases — the code handles those.
- Must not restate the function name/signature or include implementation details:

```typescript
// Good
/**
 * Round to 0 decimals and apply locale formatting.
 *
 * @param value - the numeric value
 * @returns the formatted string
 */
function formatInteger(value: number): string { ... }

// Bad — restates the name, adds purpose context
/**
 * Format a number as integer for KPI display.
 */
function formatInteger(value: number): string { ... }

// Bad — body enumerates code branches
/**
 * Set the flag on each requirement based on commercial classification.
 * Non-commercial lengths get flag = true, commercial lengths get flag = false.
 * Returns requirements unchanged if commercialLengths is empty.
 */
```

---

## User-Facing Labels

User-facing labels for data fields (table headers, form field labels, chart axis labels, dialog field labels) come from a centralised mapping module rooted to the type that defines the field. Never hardcode display strings inline at the data binding site.

When adding a new domain entity, add a corresponding mapping object alongside its type. This:

- Makes i18n possible later without grepping the codebase
- Prevents copy drift between table headers, Excel exports, and dialog labels for the same field
- Lets a non-developer change wording in one place

```typescript
// Good — central source, rooted to the type
// labels/user.ts
export const userLabels: Record<keyof User, string> = {
  id: "ID",
  name: "Full name",
  email: "Email address",
  age: "Age",
};

// In the column / form / chart definition
{ field: "email", headerName: userLabels.email, ... }

// Bad — hardcoded inline, drifts on next edit
{ field: "email", headerName: "Email", ... }
```

---

## Analytics Event Naming

**Applies only when the project ships analytics events** (product analytics, telemetry, tracking pixels). Skip this section for libraries, CLIs, internal tools, or backend services with no instrumentation.

When applicable: pick and document a single event-naming format per project, then enforce it everywhere. The format itself matters less than its consistency — but it must encode at least feature area + entity + action so that filtering events stays sane as event count grows.

A common format that works well: `feature_area:entity_action` (snake_case, `:` as separator, e.g. `dashboard:campaign_create`, `settings:limits_save`).

Without a convention, event names drift (`campaign_created`, `campaignCreated`, `create_campaign`, `dashboard.campaign.create`) and become impossible to query reliably. Document the chosen format in the project README or analytics setup doc.

---

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| Generic filenames (`utils.ts`, `helpers.ts`, `misc.ts`) | Split until each file's name describes its contents |
| Section dividers (`// ---`, `// ===`) | Split the file or extract a sub-component |
| Single-letter variable names | Names that convey purpose |
| `import { X as Y }` without a collision | Use `X` directly |
| `value!` non-null assertion | `if (value === undefined) ...` guard |
| `data as MyType` cast | Schema validation or type-guard the source |
| Manual `type` for API/URL/JSON.parse data | Schema-first with `z.infer` |
| `arr.sort()` (mutates caller) | `arr.toSorted()` |
| Chained ternaries | Function with early returns |
| `if (x) return y;` (one-liner) | Multi-line block with blank lines around |
| Comment restating well-named code | Delete the comment |
| JSDoc on React components | JSDoc on functions only |
| Hardcoded display strings | Central mappings module |
| Drift in analytics event names | One documented format |
