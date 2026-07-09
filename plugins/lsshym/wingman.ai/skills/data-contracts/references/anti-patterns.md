# Contract Alignment Anti-patterns

Use these anti-patterns to catch real contract failures before patching type errors, replacing mocks, mapping fields, or filling missing data. If one matches, fix the boundary decision instead of hiding the mismatch.

## Contents

- [Casting Away Drift](#casting-away-drift)
- [Claiming Source Fields That Do Not Exist](#claiming-source-fields-that-do-not-exist)
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

Bad smell:

```ts
return payload as unknown as Order;
```

Why it fails:
The source shape was not converted into the receiver contract. Assertions hide missing, renamed, optional, or semantically different fields.

Do instead:
Convert or validate at the API, parser, repository, adapter, request builder, or event boundary that already owns external input.

## Claiming Source Fields That Do Not Exist

Bad smell:

```ts
type ApiUser = {
  id: string;
  name: string;
  avatarUrl: string;
};
```

Why it fails:
The source type now claims data exists even though no schema, fixture, generated type, migration, sample, or runtime payload proves it.

Do instead:
Keep source types faithful to evidence. Make the receiver optional-aware, fetch the field from a real alternate source, fail validation, or ask for the source-of-truth decision.

## Fake Defaults To Satisfy Types

Bad smell:

```ts
return { id: row.id, name: row.name, avatarUrl: "" };
```

Why it fails:
Empty strings, zeroes, placeholder paths, or catch-all enum values turn missing data into misleading data.

Do instead:
Use only documented fallbacks. Otherwise represent absence explicitly or fail at the boundary with a clear error.

## Semantic Mismatch Treated As Rename

Bad smell:

```ts
const workflowKind = job.status;
```

Why it fails:
Similar names or compatible primitive types do not prove the same business meaning. A source `status` may be lifecycle state while a receiver `workflowKind` may be product category.

Do instead:
Preserve distinct concepts. Find the real source field, change the receiver only when meanings are proven identical, or surface the unresolved contract gap.

## Guessed Multi-Field Fallbacks

Bad smell:

```ts
const displayName = user.displayName || user.user_name || user.name;
```

Why it fails:
Alias chains guess at multiple possible contracts and can hide API, SDK, fixture, or generated-type drift.

Do instead:
Use the documented source field. Support multiple aliases only for proven version compatibility, and keep that compatibility handling in one boundary location.

## Vendor Shape Leaks Into Domain Model

Bad smell:

```ts
export type Order = VendorOrder;
```

Why it fails:
A stable internal model becomes coupled to one external source's nesting, naming, optionality, enum values, and release cadence.

Do instead:
Keep the domain model stable. Translate vendor payloads at the project-owned parser, repository, adapter, or SDK boundary.

## Mapper Scattered Across Call Sites

Bad smell:

```ts
renderOrder({ id: api.order_id, totalCents: api.amount.value });
saveOrder({ id: api.order_id, totalCents: api.amount.value });
```

Why it fails:
The same translation repeats in multiple receivers, so later contract changes become inconsistent.

Do instead:
Put the translation in one binding location that matches the local architecture.

## Overbuilt Adapter For Local Naming Only

Bad smell:

```ts
function toUserView(user: ApiUser): UserView {
  return { userId: user.user_id, displayName: user.display_name };
}
```

Why it fails:
If the receiver is a single local render path and meanings are identical, a mapper exists only to preserve naming style.

Do instead:
Use direct source fields or local aliases for local, temporary, display-only receivers.

## Optionality Drift Ignored

Bad smell:

```ts
return payload.customer.email.toLowerCase();
```

Why it fails:
The receiver assumes a stricter field than the source can guarantee. Optional fields, nullable fields, and absent nested objects must be handled as contract facts.

Do instead:
Validate before use, make the receiver optional-aware, or parse and reject invalid payloads at the boundary.

## Enum Or Status Collapse

Bad smell:

```ts
const status: InternalStatus = sdk.status as InternalStatus;
```

Why it fails:
Source statuses can differ in lifecycle, terminal states, retryability, capitalization, or future unknown values.

Do instead:
Map each known source value intentionally, handle unknowns explicitly, and test representative source states.

## Receiver Overreach

Bad smell:

```text
While fixing a field mismatch, the patch rewrites layout, prop names, visible text,
handler branching, and unrelated receiver behavior.
```

Why it fails:
Contract alignment should change the data boundary, not redesign unrelated receiver behavior.

Do instead:
Make the smallest change that aligns source and receiver. Leave unrelated UI, handler, config, domain, and call-site behavior unchanged unless the contract decision requires it.
