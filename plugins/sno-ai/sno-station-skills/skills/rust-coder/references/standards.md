# Rust Standards

Apply these defaults only when repository instructions, published contracts, and declared tooling
do not establish a more specific rule. Prefer code whose correctness is visible in its types,
ownership, and control flow over code that relies on comments, convention, or runtime luck.

## Source of truth and toolchain

- Honor `edition`, `rust-version`, `rust-toolchain*`, the Cargo resolver, workspace inheritance,
  target configuration, features, lint configuration, and continuous integration.
- The repository's minimum supported Rust version is a contract. Do not emit newer syntax,
  standard-library APIs, or dependency versions merely because the local compiler supports them.
- Reuse existing crates, types, traits, error layers, runtime, logging, serialization, and test
  infrastructure. Never weaken compiler flags, lints, tests, or safety policy to make code pass.
- Keep `Cargo.lock` changes intentional. Do not perform a broad dependency update as a side effect.
- Add a dependency only when the standard library and existing graph do not solve the requirement
  clearly. Check its features, minimum Rust version, license, target support, and maintenance fit.
- Do not enable a dependency's broad feature set by habit. Select the features the actual code
  needs, while preserving the repository's workspace policy.

## Correctness-first design

Design from domain constraints to language mechanics:

1. Name valid states, transitions, identities, units, and resource limits.
2. Choose the owner and lifetime of each value and resource.
3. Encode stable invariants in types and constructors.
4. Define recoverable failures and the boundary that translates them.
5. Choose concurrency only after the workload and sharing model are known.

- Validate untrusted data at the boundary, construct a trusted type, and keep internal code precise.
- Use newtypes for semantically distinct identifiers, units, validated values, and sensitive
  values when mixing the primitive forms would be a real defect.
- Use enums and exhaustive matching for closed states. Avoid boolean combinations that permit
  impossible states.
- Keep fields private when construction or mutation must preserve an invariant. Expose validated
  constructors and domain operations rather than setters that can break it.
- Use typestate only when the state graph is stable, compile-time enforcement materially helps
  callers, and generic complexity remains smaller than the runtime checks it removes.
- Use a builder only when construction has genuinely staged, optional, or cross-field validation;
  do not replace a clear constructor with ceremony.
- Prefer explicit runtime validation when a condition is inherently dynamic or type-level encoding
  would make the API harder to understand and change.

## Ownership, borrowing, and resources

- Decide ownership from the data flow before editing lifetimes. The borrow checker is reporting a
  mismatch in the model until evidence shows otherwise.
- Borrow transient read-only inputs as `&str`, `&Path`, slices, or references. Own `String`,
  `PathBuf`, collections, and domain values when they are stored, queued, returned independently,
  or moved into a task.
- Do not `clone` merely to escape a borrow error. A clone is correct when duplication is the domain
  operation or the value is intentionally cheap and independently owned; make that intent obvious.
- Do not add `Rc`, `Arc`, `Box`, `Cow`, `Cell`, `RefCell`, `Mutex`, or `RwLock` as a compiler escape
  hatch. Each must correspond to a real ownership, indirection, mutation, or sharing requirement.
- Prefer one clear owner and ownership transfer over shared mutable state. Use `Rc` only for real
  single-thread shared ownership and `Arc` only for real cross-thread shared ownership.
- Keep lifetimes local and inferable. Avoid self-referential structures, unnecessary lifetime
  parameters, and clever variance or pinning unless the API truly requires them.
- Use RAII guards for files, locks, transactions, temporary state, subscriptions, and other
  resources. Cleanup must occur on success, error, early return, cancellation, and panic unwind.
- `Drop` implementations must preserve invariants and must not panic. Avoid hidden blocking or
  fallible business operations in destructors.

## Errors, absence, and panics

- Use `Option<T>` when absence is normal and carries no error detail. Use `Result<T, E>` when a
  caller needs failure information or recovery.
- Libraries expose stable, meaningful typed errors when callers branch on failure. Applications
  may use contextual aggregate errors at executable boundaries when the repository already does.
- Preserve the source chain and add context that identifies the operation and safe identifiers,
  not secrets. Do not stringify errors early or collapse recoverable cases into one opaque message.
- Translate domain errors to exit codes, protocol responses, or user-facing text once, at the
  boundary that owns that contract.
- Use `?`, precise matching, `From` or `TryFrom`, and narrow `map_err` transformations. Do not ignore
  a `Result` or turn a failure into a silent default.
- `unwrap` and `expect` are acceptable in tests, examples, compile-time/static initialization, or
  a locally proven programmer invariant. In production, `expect` must state the invariant that
  would be broken, not merely repeat the operation.
- Panic only for programmer bugs or violated internal invariants, never for user input, network or
  filesystem failure, ordinary exhaustion, or another recoverable runtime condition.
- Do not ship `todo!`, `unimplemented!`, placeholder success, or an unreachable branch without a
  proof that makes it unreachable.

## Public APIs, traits, and abstractions

- Keep the public surface smaller than the implementation. Avoid accidental `pub` items and
  leaking dependency types when a stable domain type should own the contract.
- Follow standard naming and conversion conventions. Implement common traits when their semantics
  are natural; do not derive `Copy`, ordering, hashing, serialization, or defaults without checking
  that the behavior is correct for the domain.
- Prefer `From` for infallible conversion and `TryFrom` for validation. Use `AsRef` or `Borrow` only
  when their standard semantic contract fits, not to make every call site generic.
- Introduce a trait for a real capability boundary, multiple implementations, caller extensibility,
  or testable external dependency. Do not create a trait and generic parameter for one local type.
- Prefer static dispatch for closed homogeneous behavior and `dyn Trait` for genuine runtime
  heterogeneity or plugin boundaries. Do not box a value when an enum or concrete type is clearer.
- Keep generic bounds at the narrowest useful public boundary. Avoid bound duplication and trait
  aliases or marker traits that do not enforce a real capability.
- Use macros only when syntax or repetition cannot be expressed clearly with functions and types.
  Prefer transparent, debuggable code over macro-generated control flow.
- Public functions document meaningful errors, panics, cancellation, and safety requirements.
  Rustdoc examples demonstrate why and how the API is used and compile as tests when practical.

## Async and concurrency

- Follow the runtime already selected by the repository. Do not make a synchronous CLI or library
  async without a concurrency requirement, and do not introduce a second async runtime.
- Use async for concurrent I/O, threads or a configured parallelism library for measured CPU work,
  and a bounded bridge for blocking work inside an async runtime.
- Prefer ownership transfer and bounded channels when one task can own mutable state. Use shared
  locks only when multiple tasks truly require shared access.
- Never hold a lock guard across `.await`, network I/O, disk I/O, callbacks, or other unbounded
  work. Keep critical sections explicit and small.
- Do not call blocking I/O in an async task. Use the runtime's blocking bridge only when it is
  configured, bounded, cancellable at the application level, and necessary.
- Every spawned task has an owner, completion path, error path, and cancellation policy. Avoid
  detached tasks and leaked work during shutdown or early return.
- Bound queues, retries, fan-out, and parallel requests. Define backpressure, timeouts, ordering,
  partial-failure behavior, and cleanup from the contract rather than library defaults.
- Treat `Send` and `Sync` errors as questions about whether a value should cross a thread boundary.
  Do not add bounds, locks, `spawn_local`, or manual unsafe implementations before answering that.
- Use atomics only for state that is genuinely atomic. Choose and document the weakest correct
  ordering when it is not `SeqCst`; prefer locks or channels when multiple values form one invariant.
- For race-sensitive logic, use deterministic synchronization tests and Loom when the repository
  already supports it or the risk justifies adding a dedicated test strategy.

## Unsafe Rust and FFI

- Prefer Safe Rust. `unsafe` is valid only for an unavoidable FFI or low-level boundary, a safe
  abstraction unavailable elsewhere, or a measured hot path whose safe alternative is inadequate.
  It is never a borrow-checker escape hatch.
- Keep each unsafe block as small as possible. An `unsafe fn` still uses explicit unsafe blocks for
  unsafe operations so the audit surface remains visible.
- Put a `// SAFETY:` comment immediately at the boundary. State the concrete local proof for
  validity, initialization, alignment, bounds, aliasing, lifetime, provenance, layout, thread
  safety, and unwind behavior that applies; do not restate the operation.
- A public unsafe function or trait includes a `# Safety` section defining every caller obligation.
  A safe wrapper owns and enforces all conditions its callers cannot check.
- Audit raw pointers for nullability, provenance, alignment, initialized bytes, valid bit patterns,
  allocation origin, deallocation owner, aliasing, and lifetime. Avoid `transmute` when a checked
  conversion, pointer cast, byte API, or explicit construction expresses the intent.
- FFI declarations use the exact ABI and layout, `#[repr(C)]` where required, explicit ownership
  and allocator rules, correct `CString` or `CStr` lifetimes, and no unwinding across a foreign
  boundary. Validate foreign lengths, tags, and pointers before creating Rust references or slices.
- Manual `Send` or `Sync` implementations require a written invariant and dedicated concurrency
  review. They are not ordinary type-error fixes.
- Run Miri on the smallest relevant test surface when unsafe code, aliasing, initialization,
  pointer arithmetic, or lifetime-sensitive internals change. Miri supplements reasoning and
  target tests; it does not prove all layouts, FFI behavior, or platform assumptions.

## Performance and allocation

- Measure before optimizing. Fix algorithms, I/O shape, contention, and unnecessary work before
  applying micro-optimizations.
- Prefer iterators and slices when they improve clarity without hiding control flow. Avoid an
  intermediate `collect` when streaming or direct iteration is equally clear.
- Make allocation and copying visible on hot paths. Do not introduce `Cow`, small-vector types,
  arenas, custom allocators, SIMD, or unsafe code without representative measurement.
- Use release-profile, link-time optimization, panic strategy, and target CPU settings only from
  explicit product and deployment requirements. Do not apply one universal profile to libraries,
  servers, CLIs, and embedded targets.
- Benchmarks use representative inputs, compare equivalent conditions, and protect an observed
  budget or regression. A faster microbenchmark does not override correctness or maintainability.

## Boundaries, security, and persistence

- Validate input sizes, counts, indexes, paths, URLs, protocol values, and deserialized shapes at
  external boundaries. Bound memory, concurrency, retries, decompression, and response bodies.
- Choose `checked_*`, `saturating_*`, or `wrapping_*` arithmetic from domain semantics. Use checked
  arithmetic for user-influenced sizes, offsets, counts, and financial or persistence values.
- Treat Rust strings as UTF-8 bytes plus Unicode text. Never byte-slice untrusted text at arbitrary
  indexes; use validated boundaries, parsers, iterators, or domain-specific normalization.
- Execute subprocesses with `Command` and an argument list, never a shell-built string. Constrain
  executable selection when input can influence it, preserve required exit behavior, and avoid
  leaking secrets through arguments or diagnostics.
- Keep secrets out of source, logs, errors, debug output, fixtures, snapshots, environment dumps,
  archives, and generated diffs. Use the repository's secret storage and redaction policy.
- Use safe temporary files and explicit permissions. Defend sensitive path operations against
  traversal, symlink replacement, predictable names, partial writes, and unsafe cross-filesystem
  assumptions as the threat model requires.
- Durable file replacement uses the repository's lock, temporary-file, atomic-rename, permission,
  file-sync, and directory-sync contract. Database changes use real transactions and preserve
  rollback and concurrency invariants.
- Serde and wire types preserve field names, optionality, defaults, unknown-field behavior, and
  compatibility deliberately. Do not let a convenient derive silently redefine a published shape.
- CLI stdout, stderr, JSON, help text, exit codes, filesystem state, and child-process propagation
  are interfaces. Test them as contracts rather than implementation details.

## Cargo features, targets, and build behavior

- Features should be additive whenever possible. Do not make enabling one feature silently disable
  another or change an existing public API incompatibly.
- Test the combinations the crate promises: default features, no default features, all features,
  and meaningful pairs or target-specific sets. Do not assume `--all-features` covers mutually
  exclusive or target-gated behavior correctly.
- Inspect feature resolution with Cargo when behavior is surprising. Keep build, development, and
  target-specific dependency leakage in mind.
- Platform code lives behind the narrowest `cfg` boundary and preserves a common contract. A
  successful cross-compile proves compilation, not native runtime behavior.
- Build scripts and procedural macros are part of the trusted build surface. Keep them
  deterministic, minimal, offline-capable when the repository requires it, and free of secret or
  network side effects.
- Preserve reproducibility: do not depend on local paths, undeclared tools, timestamps, host-only
  state, or generated files omitted from the package unless the repository explicitly owns them.

## Testing and delivery

- For a defect, first write the smallest test that fails for the real reason, then fix it. For new
  behavior, test public outcomes and failure paths rather than private line structure.
- Use unit tests for pure invariants and integration tests through the public crate, binary, or
  protocol boundary. Prefer real temporary files, SQLite or configured stores, child processes,
  and loopback services over mocks of repository-owned code.
- Use table tests for finite cases, property tests for broad invariants, compile-fail tests for
  type-level API guarantees, documentation tests for public examples, fuzzing for parsers and
  hostile inputs, and Miri for relevant unsafe internals.
- Make concurrency tests deterministic with barriers, channels, controlled clocks, or dedicated
  model checking. Do not use arbitrary sleeps as proof of ordering or race freedom.
- Do not game tests with special production branches, weakened assertions, snapshots that merely
  approve the new output, or mocks that bypass the behavior under test.
- Run the smallest relevant gate first, then expand according to impact. A normal delivery proves
  formatting, compilation, focused behavior, and configured Clippy. Public libraries also prove
  docs, promised features, minimum Rust version, and consumers. Unsafe or concurrent changes add
  their dedicated gates.
- For a published crate, inspect exact package contents and run the repository's package or publish
  dry-run before asking to publish. For binary releases, execute the actual packaged artifact on
  every claimed native platform before declaring support. Publishing is irreversible and always
  remains a separate authorized action.
- Review the final diff for compiler escape hatches: unexplained clones, unnecessary smart
  pointers, broad trait bounds, lifetime proliferation, opaque boxed errors, production panics,
  lint suppressions, unsafe expansion, unbounded work, and accidental public API growth.

## Authoritative references

Use current official documentation when a rule is version-sensitive or the repository does not
settle it:

- Rust API Guidelines: <https://rust-lang.github.io/api-guidelines/>
- Cargo Book: <https://doc.rust-lang.org/cargo/reference/>
- Clippy documentation: <https://doc.rust-lang.org/clippy/>
- Rustonomicon: <https://doc.rust-lang.org/nomicon/>
- Miri: <https://github.com/rust-lang/miri>

Official references inform the decision; repository contracts still determine the edition, minimum
Rust version, enabled features, runtime, compatibility promise, and exact delivery gates.
