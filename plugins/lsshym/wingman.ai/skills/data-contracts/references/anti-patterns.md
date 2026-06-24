# Contract Alignment Anti-patterns

Use these anti-patterns to catch real contract failures before patching type errors or mapping fields.

## Contents

- [Casting Away Drift](#casting-away-drift)
- [Adding Provider Fields That Do Not Exist](#adding-provider-fields-that-do-not-exist)
- [Fake Defaults To Satisfy Types](#fake-defaults-to-satisfy-types)
- [Semantic Mismatch Treated As Rename](#semantic-mismatch-treated-as-rename)
- [Vendor Shape Leaks Into Domain Model](#vendor-shape-leaks-into-domain-model)
- [Mapper Scattered Across Call Sites](#mapper-scattered-across-call-sites)
- [Overbuilt Adapter For Local Naming Only](#overbuilt-adapter-for-local-naming-only)
- [Optionality Drift Ignored](#optionality-drift-ignored)
- [Enum Or Status Collapse](#enum-or-status-collapse)

## Casting Away Drift

Bad:

```ts
return payload as unknown as Order;
```

Why it fails:
The provider shape is not converted into the stable consumer contract. Type assertions hide missing, renamed, or semantically different fields.

Better:
Convert at the API, parser, repository, or adapter boundary that already owns external input.

## Adding Provider Fields That Do Not Exist

Bad:

```ts
type ApiUser = {
  id: string;
  name: string;
  avatarUrl: string;
};
```

Why it fails:
The provider contract now claims to supply data that no schema, sample, fixture, migration, or runtime payload proves exists.

Better:
Expose the missing field explicitly: make the consumer field optional, fetch it from a real alternate source, return a validation error, or ask for the product/source-of-truth decision.

## Fake Defaults To Satisfy Types

Bad:

```ts
return { id: row.id, name: row.name, avatarUrl: "" };
```

Why it fails:
An empty string, zero, placeholder enum, or fake path turns missing provider data into misleading consumer data.

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
Preserve both concepts. Find the source of the missing concept, change the consumer contract only if the meaning is identical, or stop and surface the unresolved contract gap.

## Vendor Shape Leaks Into Domain Model

Bad:

```ts
export type Order = VendorOrder;
```

Why it fails:
A stable internal model becomes coupled to one external provider payload. Other consumers inherit provider-specific nesting, naming, optionality, and enum semantics by accident.

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
If the consumer is a single local render function and the fields are naming-only differences, a dedicated adapter can add unnecessary architecture.

Better:
Use direct source access or local aliasing when scope is small and semantics are identical.

## Optionality Drift Ignored

Bad:

```ts
return payload.customer.email.toLowerCase();
```

Why it fails:
If the provider marks `email` as optional or runtime samples omit it, the consumer contract is stricter than the provider contract.

Better:
Validate before use, make the consumer optional-aware, or enforce a boundary parse that rejects invalid payloads with a clear error.

## Enum Or Status Collapse

Bad:

```ts
const status: InternalStatus = sdk.status as InternalStatus;
```

Why it fails:
SDK status values often differ in lifecycle, failure states, capitalization, retryability, or terminal-state meaning.

Better:
Map every known provider value intentionally, handle unknown values explicitly, and test representative values.
