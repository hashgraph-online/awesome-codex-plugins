# Contract Alignment Anti-patterns

Use these anti-patterns to catch real contract failures before patching type errors or mapping fields.

## Contents

- [Casting Away Drift](#casting-away-drift)
- [Adding Source Fields That Do Not Exist](#adding-source-fields-that-do-not-exist)
- [Fake Defaults To Satisfy Types](#fake-defaults-to-satisfy-types)
- [Semantic Mismatch Treated As Rename](#semantic-mismatch-treated-as-rename)
- [Guessed Multi-Field Fallbacks](#guessed-multi-field-fallbacks)
- [Vendor Shape Leaks Into Domain Model](#vendor-shape-leaks-into-domain-model)
- [Mapper Scattered Across Call Sites](#mapper-scattered-across-call-sites)
- [Overbuilt Adapter For Local Naming Only](#overbuilt-adapter-for-local-naming-only)
- [Optionality Drift Ignored](#optionality-drift-ignored)
- [Enum Or Status Collapse](#enum-or-status-collapse)
- [Receiver Overreach](#receiver-overreach)

## Casting Away Drift

Bad:

```ts
return payload as unknown as Order;
```

Why it fails:
The source shape is not converted into the stable receiver contract. Type assertions hide missing, renamed, or semantically different fields.

Better:
Convert at the API, parser, repository, or adapter boundary that already owns external input.

## Adding Source Fields That Do Not Exist

Bad:

```ts
type ApiUser = {
  id: string;
  name: string;
  avatarUrl: string;
};
```

Why it fails:
The source contract now claims to supply data that no schema, sample, fixture, migration, or runtime payload proves exists.

Better:
Expose the missing field explicitly: make the receiver field optional, fetch it from a real alternate source, return a validation error, or ask for the product/source-of-truth decision.

## Fake Defaults To Satisfy Types

Bad:

```ts
return { id: row.id, name: row.name, avatarUrl: "" };
```

Why it fails:
An empty string, zero, placeholder enum, or fake path turns missing source data into misleading receiver data.

Better:
Use a real documented fallback, model absence explicitly, or fail at the contract boundary with a clear error.

## Semantic Mismatch Treated As Rename

Bad:

```ts
const workflowKind = job.status;
```

Why it fails:
`status` may mean processing state while `workflowKind` may mean product category. Matching types or similar names do not prove matching business meaning.

Better:
Preserve both concepts. Find the source of the missing concept, change the receiver contract only if the meaning is identical, or stop and surface the unresolved contract gap.

## Guessed Multi-Field Fallbacks

Bad:

```ts
const displayName = user.displayName || user.user_name || user.name;
```

Why it fails:
This guesses multiple possible source contracts instead of identifying the real source field. It can hide API, SDK, fixture, or generated-type drift and makes later contract changes unpredictable.

Better:
Use the documented source field. Only support multiple aliases when a real version-compatibility requirement proves each variant can appear, and keep that compatibility handling in one boundary location.

## Vendor Shape Leaks Into Domain Model

Bad:

```ts
export type Order = VendorOrder;
```

Why it fails:
A stable internal model becomes coupled to one external source payload. Other receivers inherit source-specific nesting, naming, optionality, and enum semantics by accident.

Better:
Keep the stable domain model stable. Translate vendor payloads at the API, repository, parser, or adapter boundary.

## Mapper Scattered Across Call Sites

Bad:

```ts
renderOrder({ id: api.order_id, totalCents: api.amount.value });
saveOrder({ id: api.order_id, totalCents: api.amount.value });
```

Why it fails:
The same boundary translation is repeated in multiple places, making future contract changes inconsistent.

Better:
Put the translation in one binding location that matches the project architecture.

## Overbuilt Adapter For Local Naming Only

Bad:

```ts
function toUserView(user: ApiUser): UserView {
  return { userId: user.user_id, displayName: user.display_name };
}
```

Why it may fail:
If the receiver is a single local render function and the fields are naming-only differences, a dedicated adapter can add unnecessary architecture.

Better:
Use direct source access or local aliasing when scope is small and semantics are identical.

## Optionality Drift Ignored

Bad:

```ts
return payload.customer.email.toLowerCase();
```

Why it fails:
If the source marks `email` as optional or runtime samples omit it, the receiver contract is stricter than the source contract.

Better:
Validate before use, make the receiver optional-aware, or enforce a boundary parse that rejects invalid payloads with a clear error.

## Enum Or Status Collapse

Bad:

```ts
const status: InternalStatus = sdk.status as InternalStatus;
```

Why it fails:
SDK status values often differ in lifecycle, failure states, capitalization, retryability, or terminal-state meaning.

Better:
Map every known source value intentionally, handle unknown values explicitly, and test representative values.

## Receiver Overreach

Bad:

```text
While fixing a field mismatch, the patch rewrites layout, prop names, visible text,
handler branching, and unrelated receiver behavior.
```

Why it fails:
Contract alignment should change the data boundary, not redesign unrelated receiver behavior.

Better:
Make the smallest change that aligns source and receiver. Leave UI, handlers, config behavior, domain behavior, and unrelated call sites unchanged unless the contract decision requires them.
