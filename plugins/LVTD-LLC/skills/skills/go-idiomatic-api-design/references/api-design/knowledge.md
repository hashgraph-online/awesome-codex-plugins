# API Design Knowledge

## Caller-First Design

An API is the code its callers must write and the commitments maintainers must
keep. Sketch successful, invalid, optional, and concurrent call sites before
choosing exported declarations.

## Concrete Types and Interfaces

Return concrete types when callers benefit from their stable behavior. Let each
consumer declare the smallest interface it needs. A provider-owned interface
often freezes every method and burdens tests with irrelevant fakes.

Implicit satisfaction decouples a consumer from the provider, but method sets
still matter. Pointer and value receivers satisfy different interfaces.
Compile-time assertions document intent; they do not validate semantics.

An interface containing a typed nil pointer has a dynamic type and is therefore
not a nil interface. Interface-returning success paths must return literal
`nil` when no value or error exists.

For configuration, compare a constructor with an exported options struct,
functional options, and a reusable configured object by sketching real call
sites. A small stable option set may favor a struct. Functional options help
when configuration grows or combinations need constructor validation, but they
add indirection. A reusable object can precompute immutable state and make
lifecycle or concurrency guarantees explicit.

Functional options need defined defaults, ordering, duplicate, conflict, and
validation behavior. A config struct must define whether zero means "explicit
zero" or "omitted."

## Embedding, Receivers, and Generics

Embedding promotes fields and methods and may silently enlarge an exported
type's method set as the embedded dependency evolves. Embed only when every
promoted behavior is intentionally public; otherwise use a named field.
Embedding is composition, not inheritance.

A value receiver copies the outer value but may still share pointer-like fields.
Receiver choice communicates value versus entity semantics and affects method
sets. Use pointer receivers for mutation and noncopyable fields; benchmark
rather than inventing a universal size threshold. Avoid mixed receiver kinds
without a concrete interface or semantic reason.

Choose an abstraction by the relationship it must preserve. Use `any` for
genuinely heterogeneous values, generics for demonstrated uniform type
relationships, and ordinary interfaces when code only invokes shared behavior.
Do not introduce type parameters before concrete duplication or caller needs
justify them.

## Compatibility Commitments

Exported names, fields, methods, interface methods, error identities, and
documented zero-value behavior are compatibility commitments. Exported fields
also expose representation and mutation. Adding a method to a public interface
can break every external implementation.

Changing `F(x)` to `F(x, opts ...Option)` is still a function-signature change:
existing direct calls compile, but assignments, interfaces, callbacks, and
other uses of the old function type can break.

Public embedding, promoted marshaling methods, generic constraints, functional
option conflict rules, and serialized JSON shape are compatibility commitments.

## Standard Interfaces

Implement `fmt.Stringer`, `encoding.TextMarshaler`,
`encoding.TextUnmarshaler`, `sql.Scanner`, `driver.Valuer`, or similar
interfaces only when the type can honor their established contract. Keep
formatting safe for logs and avoid exposing secrets.

## Tests as Caller Evidence

External test packages prove the exported caller view. Same-package tests remain
appropriate for internal invariants. Example tests double as documentation only
when their output is deterministic and their names associate with real symbols.

## Version Awareness

Check the module's `go` directive and toolchain before relying on loop-variable
semantics, iterator APIs, generic library types, or newer error and testing APIs.
