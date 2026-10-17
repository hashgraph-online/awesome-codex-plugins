# Application Architecture Knowledge

## Boundary Model

- **Command adapter**: parse flags and operands, invoke one application action,
  render a result, and translate usage failures.
- **Application service**: coordinate a use case through domain logic and ports.
- **Core/domain**: types and invariants independent of Cobra, HTTP, files, and terminals.
- **Adapter**: implement a port using an API, filesystem, process, database, or clock.
- **Composition root**: load validated settings, construct concrete dependencies,
  build the command tree, and own lifecycle cleanup.

Dependencies point inward: outer adapters may import application/core packages;
core code must not import the CLI framework or concrete infrastructure.

## Interface Ownership

Define a narrow interface in or near the consuming package. This keeps the seam
shaped by the caller's need and lets concrete types satisfy it implicitly.
Concrete adapters need not declare or own every interface they may satisfy.

Discover interfaces from a concrete substitution need. Keep the provider
concrete and let separate consumers define narrow views. A standard-library
extension point such as `http.RoundTripper` can be an adapter seam without
becoming the application's domain port.

## Dependency Bundles and Lifecycles

A command runner may accept one dependency bundle at its construction boundary,
while internal helpers should receive only what they need. Do not pass a broad
service locator through every layer.

The composition root owns long-lived clients, transports, pools, listeners,
and cleanup. Record who constructs, shares, reloads, and closes each resource.
For SQL, the root owns `*sql.DB`; the use case owns transaction boundaries.

Classify each acquired value as an **owner**, **borrower**, or explicit
**transfer**. The owner defines cleanup on normal, error, cancellation, and
partial-startup paths. Close in reverse dependency order. Decide whether close,
flush, sync, or shutdown errors are material and how they combine with a
primary failure.

Reader-based cores should borrow `io.Reader`/`io.Writer` values and leave path
opening and ownership at adapters. A core must not close borrowed stdin,
stdout, or caller-provided streams.

CLI and HTTP are peer outer adapters around the same application service. An
HTTP executable owns listener and server lifecycle; detailed inbound semantics
belong to `go-http-server-applications`.

## Explicit Initialization

Keep fallible network, database, filesystem, and configuration work in an
explicit composition path. `init` cannot return an error and makes startup
order and test isolation harder to control. Reserve it for narrow,
side-effect-free registration only when package loading is the intended
contract; never depend on lexical filename order for correctness.

## Configuration vs State

Configuration describes how the process should run and is normally validated
once before use. Mutable state is application data with consistency, concurrency,
and persistence semantics. Treating both as a global map makes reloads unsafe and
obscures ownership.

## Proportional Structure

A small CLI may need only `main`, a command factory, and a runner. Introduce
application services or ports when there is reusable behavior, a difficult
effect boundary, or multiple adapters—not to imitate a generic architecture diagram.
