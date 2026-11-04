---
name: typescript-best-practices
description: Sixteen type-safety rules for writing and reviewing TypeScript, with do and don't examples in references/patterns.md. Use whenever you open or edit a .ts or .tsx file, or on /typescript-best-practices.
disable-model-invocation: true
---

# typescript-best-practices

Read `principle-type-system-discipline` ([../principle-type-system-discipline/SKILL.md](../principle-type-system-discipline/SKILL.md)) first. These rules apply it to TypeScript. [references/patterns.md](references/patterns.md) has a short code example for each rule, numbered to match.

If your agent supports path-scoped skills, attach this one to `**/*.ts` and `**/*.tsx`. Otherwise the router or the user loads it when TypeScript is in play. For other languages, use `principle-type-system-discipline` and `principle-boundary-discipline` ([../principle-boundary-discipline/SKILL.md](../principle-boundary-discipline/SKILL.md)) directly.

Before you write anything, find the repo's existing conventions: its schema library, its logger, the name it uses for union tags, and the shape of its brand marker. Follow them over the examples in the reference.

## Modeling

1. **Tagged unions for variants.** Model alternative states as a union of object types that share one literal tag field. A boolean flag plus optional fields lets contradictory combinations exist (`loading: true` with an `error` set). Use one tag name across the codebase.
2. **Branded primitives.** Intersect a primitive with a readonly brand property so an `InvoiceId` cannot be passed where a `CustomerId` is expected. Mint the brand only through a type guard that validates (`value is InvoiceId`) and a parse function that wraps the guard and throws on failure. Never brand with `as`. Check once where the value enters; downstream code trusts the brand.
3. **Make illegal values unconstructible.** Prefer a shape that cannot hold a bad value to a runtime check: `[T, ...T[]]` for a non-empty list, `Array<[K, V]>` for paired data, a start plus a duration instead of start and end with an ordering invariant in a comment. Provide helpers for derived views (the computed end time). Brand the duration only if some unrelated number could be passed in its place.
4. **Use the simplest type that keeps every operation total.** A plain array is fine while every operation on it works for empty input (a sum of nothing is zero). Strengthen to non-empty only where the weak type forces a lie: a `!`, an index cast, or an "unreachable" throw. Or widen the return type to include `undefined`. Provide a guard so a plain array can be checked once and then carried as non-empty.

## Untrusted data

5. **External data is `unknown`, never `any`.** RPC payloads, parsed JSON, `postMessage` events, IPC, files, environment variables, and database rows all arrive as `unknown` and get narrowed before use. `any` turns off the checker exactly where an attacker controls the input.
6. **Schemas before hand-written guards.** Check whether the codebase uses a runtime validation library and already defines a schema for this data. Define one schema and infer the static type from it. Use the non-throwing parse call when bad input is an expected outcome (a user form), and the throwing one when it is a bug. Never add a validation library for one guard. If the static type already exists, annotate the schema with it so the compiler rejects a schema that checks less than the type promises.
7. **No `as` except after validation.** When you remove an assertion, find out why inference failed: add a missing discriminant, narrow a source typed as `Record<string, unknown>`, parse at the untyped boundary with the owning schema, or, if the fact truly cannot be expressed, use a brand or `satisfies`.
8. **Narrow in this order, best first:** switch on the tag; an `in` check; `typeof` or `instanceof`; a custom guard; an assertion after validation.
9. **Guards must check what they claim.** A guard that lies is worse than `as` because its name promises safety. Name guards `isX` or `hasX`. Prefer tag narrowing when a tag exists.
10. **Exhaustive switches.** In the `default` branch of a switch over a union, assign the value to a local typed `never`. Adding a variant then fails to compile at every switch that forgot it. Return that local in value-returning switches; mark it used with `void` in statement switches.
11. **`satisfies` over `as` for literals.** It checks conformance and keeps the literal types.
12. **Parse once at the boundary.** Data crossing into the system is parsed once into a named domain type. A loose record type never travels past that parse. Wire formats tolerate unknown fields so older code can read newer messages. Persisted JSON is a versioned blob parsed inside `try`/`catch`. Inner functions do not re-validate. See `principle-boundary-discipline`.
13. **Derive types from generated sources.** When types already come from protobuf, OpenAPI, GraphQL, or database migrations, build on them with `Pick`, `Omit`, `Partial`, and `typeof`. A hand-written duplicate interface drifts the first time the source changes.

## Calls, tests, and telemetry

14. **One object parameter over several positional ones.** Swapped positional arguments of the same type compile without complaint; named fields do not. Exempt hot paths (per-frame rendering, tokenizers, parsers, tight loops) where the allocation shows up in a profile.
15. **Run real code in tests.** Do not mock what can run on a dev machine. Use the test framework's own facilities, including its checks for leaked handles and undisposed resources. Check UI behavior in a real running build. Keep mocks for dependencies that cannot run locally. See the `tdd` skill ([../tdd/SKILL.md](../tdd/SKILL.md)).
16. **Structured telemetry.** Log through the project's structured logger with enough fields that an id alone lets someone debug the case. No bare `console.log` in shipped code. Never log secrets, tokens, or full request bodies that may contain them.

## Done when

No `any` touches external data, every `as` follows a validation, no guard lies, every switch over a union is exhaustive, and boundary data is parsed once into a domain type.
