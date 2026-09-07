# CONTEXT.md Format

## Canonical Write Shape

```markdown
# <Context Name>

<One or two sentences describing this domain context.>

## Language

**Customer**:
A person or organization that purchases the product.
_Avoid_: User, account, client
_Authority_: docs/current/product-language.md (optional)

## Relationships

- A **Customer** may place many **Orders**.

## Resolved Ambiguities

- "account" is split into **Customer** and **User** according to role.

## Open Ambiguities

- Whether partial cancellation belongs to **Order** or **Order Line** remains
  unresolved.
```

`active` is implicit. Add `proposed` or `deprecated` only when needed; open
ambiguities are never active truth.

## Rules

1. **Terms only**: no classes, functions, file paths, config keys, architecture
   inventories, API details, task state, logs, or session memory.
2. **Domain expert test**: definitions should be concise and understandable to
   a domain expert. Use a second sentence only when it prevents a real boundary
   ambiguity.
3. **Avoid aliases**: record deprecated, misleading, or overloaded names when
   useful; omit an empty `_Avoid_` line.
4. **Stable bytes**: no timestamps, task/session IDs, automatic review dates,
   unrelated reordering, or cosmetic rewrites.
5. **Optional provenance**: use `_Authority_` only for formal or
   drift-sensitive definitions. The linked authority remains the owner.
6. **Immediate minimal delta**: write a resolved fact inline; leave bytes
   unchanged when meaning did not change.
7. **Safe paths**: mapped files must resolve inside the project root.

## Multi-Context Map

```markdown
# Context Map

- ordering -> src/ordering/CONTEXT.md
- billing -> src/billing/CONTEXT.md
```

Use project-relative paths only. Root `CONTEXT.md` owns system-wide language;
local files own bounded-context language.

## Legacy Read Compatibility

Existing three-column tables remain readable:

```markdown
| Term | Definition | Avoid |
| --- | --- | --- |
| Customer | A purchaser. | User, account |
```

Do not rewrite a legacy file merely to modernize formatting. When a semantic
change is required, preserve unrelated rows and use the smallest compatible
edit; new files use the canonical write shape.
