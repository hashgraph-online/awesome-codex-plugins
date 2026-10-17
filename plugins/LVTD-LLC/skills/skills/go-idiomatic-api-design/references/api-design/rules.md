# API Design Rules

## Packages and Names

- Give each package one coherent purpose.
- Choose names that read clearly at the call site.
- Avoid package-name stutter and vague packages such as `utils`.
- Document every exported declaration and the package itself.
- Give deprecated declarations a `Deprecated:` note with a migration target.

## Types and State

- Prefer a useful, safe zero value when practical; otherwise require a constructor.
- Keep fields private when they protect invariants, synchronization, or evolution.
- Document whether values may be copied and whether methods are concurrency-safe.
- Use pointer receivers for mutation, identity, or noncopyable fields.
- Prefer value receivers for small natural value types; benchmark size claims.
- Keep receiver kinds consistent unless a concrete semantic constraint differs.
- Remember that value receivers make shallow copies and may share referenced state.
- Embed only when every promoted field and method is deliberately public.
- Never embed mutexes or private controls for selector convenience.

## Functions, Methods, and Interfaces

- Use a method when behavior belongs to the receiver's domain.
- Use a function when no receiver naturally owns the operation.
- Start concrete and extract an interface only at a substitution boundary.
- Compare an options struct, functional options, and a configured concrete type
  from caller code rather than defaulting to one fashionable pattern.
- Put consumer interfaces beside the consumer.
- Keep optional capability interfaces narrow and behaviorally meaningful.
- Return literal `nil` on empty interface success paths; test typed-nil cases.
- Use `any` only for genuinely heterogeneous data.
- Use generics for demonstrated type relationships, not to avoid a small concrete API.
- Define functional-option defaults, ordering, duplicates, conflicts, and validation.

## Errors

- Return errors last and preserve causes with `%w` when callers need inspection.
- Document stable error identities or types; do not expose driver details by accident.
- Keep error messages useful but do not make callers parse prose.

## Verification

- Add external tests for exported behavior.
- Add executable examples for the most important call sites.
- Verify standard-interface behavior, not merely method presence.
- Run API compatibility tooling when a published module evolves.
- Treat variadic parameter additions as signature changes during compatibility review.
- Review promoted methods, accidental interface satisfaction, JSON shape, typed
  nils, receiver method sets, and option conflicts.
- Route language-level numeric, slice, map, range, and Unicode invariants to
  `go-language-correctness`.
