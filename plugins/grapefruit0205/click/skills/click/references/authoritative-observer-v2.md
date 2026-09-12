# Authoritative Observer v2 contract

Authoritative Observer v2 is Click's narrowly supported source of runtime input
authority for dependency-aware cross-revision reuse. It is separate from
Shadow Observer v1 and from static dependency discovery. The public control is:

```text
click-gate observer authoritative
```

The control is accepted in active Evidence or a separately approved, active
Guarded contract. It prepares candidate runtime state and grants no reuse by
itself. Execution permission comes from the host in Evidence and the approved
contract in Guarded. A dashboard, report, proposal, caller-provided JSON object,
or Shadow record cannot impersonate a signed observation.

New Evidence lifecycles select `click-gate observer auto`. For supported checks,
Click prepares the installed native profile once and retains its capability
candidate across completed Evidence turns. Preparation failure preserves normal
verification and is not retried until `click-gate observer auto` is explicitly
selected again. `off` and `shadow` remain available and their explicit selection
survives those turns. Guarded still defaults to `off`.

When there is no owner dependency manifest or declaration, the versioned
`runtime-observed-inputs-v1` provider binds the exact command to the built-in
capture rules. Only a complete, runner-signed observation can issue its receipt.
No project JSON, policy commit, dependency declaration or approval is fabricated.
Existing owner policy takes precedence. Automatic observation does not create
a shard map: use the existing init/status/refresh workflow for parent splitting.

When `evidence-reuse.json` already exists, auto leaves the owner-selected reuse
route in place without preparing a companion. The reuse engine still validates
that policy normally; its presence grants no authority. Explicit authoritative
selection is available if observation is wanted alongside owner policy.
Native collectors retain bounded stdout/stderr from the same admitted target.
Actionable diagnostics and bounded failure collection can also observe inputs;
their existing claim and continuation checks remain unchanged. Collector output
is kept separate, and an observation failure never triggers another test run.

## Implemented profiles and validation

| Profile | Native backend | Implementation and validation |
| --- | --- | --- |
| `linux-cpython3123-strace68-v1` | exact strace 6.8 and a successful ptrace capability probe | Implemented and validated on a real Linux host |
| `darwin-cpython3123-fsusage-v1` | privileged native `fs_usage` plus a DYLD native audit companion | Implemented and validated on a native macOS host |
| `windows-cpython3123-etw-v1` | inbox `logman.exe` and `tracerpt.exe` ETW sessions plus a native audit extension | Implemented and validated on a native Windows host |

The original v1 profiles retain their exact CPython 3.12.3 identity. Added
`linux-cpython312-strace68-v2`, `darwin-cpython312-fsusage-v2`, and
`windows-cpython312-etw-v2` profiles admit the bounded CPython 3.12.3–3.12.14
family. Actual interpreter, headers, SOABI, observer rules and build identities
bind each artifact. These profile additions do not certify every distribution;
unmodeled runtime inputs still make observation unavailable.

Each source contains one direct `python -m unittest ...` or supported
`python -m pytest ...` command, and a bound verification
environment with `PYTHONHASHSEED=0` and `PYTHONDONTWRITEBYTECODE=1`. Auto supplies
these defaults only after preparing a runtime and preserves explicit environment
values; incompatible values leave observation ineligible. Explicit authoritative
mode keeps its deterministic environment selection. A platform
profile is usable only when its exact runtime, privilege, compiler, headers,
backend identity, and capture capability pass their local probes. A missing or
changed input makes authoritative observation unavailable and preserves normal
verification.

Click uses already installed build inputs to build a small native audit
companion. It installs no package and requests no privilege. The companion
source, compiler, backend executables and versions, bootstrap where applicable,
and resulting artifact are content-identified. The artifact directory is
outside the repository and is revalidated before each use; POSIX directories
must also be owned by the current user with mode `0700`. Unsupported versions
or missing build inputs make authoritative mode unavailable.

## One execution and failure behavior

The one-use Click verification runner launches the original command under the
selected platform collector and native audit companion. The command is
executed exactly once.
If the backend cannot start before the target begins, Click falls back to the
same unobserved command once. If observation becomes incomplete after the
target starts, Click preserves that execution's PASS or FAIL result, records an
ineligible observation, and never reruns the target to obtain better telemetry.

The runner signs the observation envelope with its one-use token. Result
recording verifies that signature and all current bindings before storing a v2
receipt. Arbitrary observation JSON supplied through an internal API is ignored.

## Completeness boundary

A complete observation snapshots every modeled input consumed by the check,
including:

- file contents and metadata;
- directory membership and metadata;
- missing-path lookups;
- lexical symlinks and their resolved targets;
- the executable, interpreter, native companion, platform backend, compiler, and
  relevant Python runtime files;
- source, configuration, data, import-search, standard-library, distribution,
  site-package, loader, locale, and runtime support inputs.

Input records use role-based content, directory, missing, or symlink
fingerprints. An input's identity is what the check can consume: the file
type and permission bits, the content of a read or executed file, the size of
a metadata-only file, the sorted member names and types of a directory, or the
link text of a symlink. Inode numbers, link counts, ownership and timestamps
are runtime assumptions rather than modeled inputs, so an equal-content
rewrite, a checkout of identical content or a `touch` keeps the receipt.
Persisted project paths are repository-relative. Absolute runtime paths are
reduced to role and identity records; raw trace paths are transient. Reuse
re-fingerprints every record, so a content or permission change, directory
membership change, a missing path appearing, a symlink change, a new import
candidate, backend drift, or companion drift makes the prior observation
ineligible.

Every implemented profile deliberately refuses to mark an observation complete
when it sees a child process, concurrent thread execution, network or IPC
activity, project time or random input, inherited descriptor input, unsupported native or dynamic-runtime
access, observer introspection or tampering, an unresolved event, capture loss,
or an incomplete process stream. These conditions affect reuse eligibility
only; they never change the test result.

## Conditional native receipts

When the process tree was followed completely and every file input was
snapshotted, but the companion reported only a followed child process,
concurrent thread execution, or dynamic runtime introspection, the observation
is recorded with status `conditional` instead of `failed`. Such a receipt
permits explicitly conditional reuse: the check is skipped only while every
observed input, the runtime, backend and companion remain unchanged, the plan
reports the authority `conditional-python-observation` with the reason
`conditional-observed-inputs-current`, and host output, status and the
dashboard disclose that input completeness is unproven. Time or random input,
network or IPC activity, inherited descriptors, tampering, capture loss and
unresolved events never produce a conditional receipt.

## Binding and successor requalification

`runtime-dependency-observation-v2` binds the original execution to:

- evidence source and shard;
- normalized check digest and exact argv;
- working directory and Git workspace root;
- protected workspace tree and mutation revision;
- Guarded contract digest or Evidence intent digest;
- verification environment and executable identity;
- host Hook coverage;
- dependency policy or declaration digest;
- observer profile, backend, companion, and complete input snapshot.

A completed Guarded contract contributes only a candidate to a successor.
The successor needs its own contract id and later-turn approval, must explicitly
prepare a current authoritative runtime, and must request the same check. Click
then revalidates the current policy, environment, executable, host coverage,
shard identity, runtime identities, and every recorded input immediately before
reuse. Only eligible sources are skipped; all uncertain, changed, new, or
incomplete sources execute normally.

Completed Evidence lifecycles similarly contribute candidates in the same host
session and workspace, with a fresh intent lineage and host execution authority.
Every observed input is checked at the final reuse boundary, even when Git
reports an identical tree. An ignored file changing cannot slip through the
exact-receipt route. An incomplete worker observation affects only that source;
it does not disable a sibling's complete input receipt or invalidate the partition.

Automatic Evidence integration has a real Linux regression fixture covering
independent test children, ignored data, shared configuration, successive intent
lineages and a final parent run. The follow-up adds Linux pytest 8.4.2/9.1.1
fixtures and runtime-family checks. pytest's own bound timing functions are
recognized by code identity; project timing consumption, report hooks, foreign
profile removal, workers, capture-file inputs and cache mutations may still
invalidate completeness. Original options are preserved; Click does not turn
off capture, plugins, caches or worker pools to obtain a receipt.

Node, Vitest and Jest add bounded OS input/worker candidates in auto mode.
These records live in `framework_observations`, with `runtime_inputs_complete`
and `reuse_authorized` fixed to false. Process birth/exit completeness is not
JavaScript input completeness. Unsupported diagnostics are bounded per exact check across
the Evidence lineage; owner reuse policy and explicit off remain respected.
Candidate records never enter dependency receipts or Shadow prediction authority.
Default `auto` also runs Linux Node 22.23.2 V8 call/value diagnostics for workers, forks and VM contexts, with exact-binary native PRNG state and bounded shared-byte samples. `observer runtime` explicitly retries collection. Existing committed owner input policies and verified receipts permit automatic reuse independently; diagnostic records never become authority. Complete engine input coverage remains unavailable; see [default collection and reuse limits](../../../docs/architecture/node-runtime-observation.md).
See [rollout and validation scope](../../../docs/architecture/automatic-observation.md).

## Shadow separation

Shadow Observer v1 stays `"authoritative": false` and
`"reuse_authorized": false`. Its records are content-free lifecycle telemetry.
Changing a Shadow flag, copying a Shadow `complete` status, replaying a report,
or promoting static dependency analysis cannot produce an Authoritative
Observer v2 envelope. The paths may share low-level parsing code, but authority
comes only from the separate verified execution and runner-token signature
described above.

## Separate conditional JS confidence

`conditional-js-observation-v1` is not an Authoritative Observer v2 profile. It
can authorize reuse in default auto mode with explicitly unproven completeness,
using runner-attested before/after observed input snapshots and current command,
environment, executable, host and child bindings. The dashboard and host output
must label this conditional confidence. Known dynamic inputs or unsupported
coverage run normally; see [scope and runtime assumptions](../../../docs/architecture/node-runtime-observation.md).
