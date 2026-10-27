# Launch and isolation

Conditional detail for [Agent Native](../SKILL.md): what a refused dispatch
means, where a worker's isolation comes from, what disjoint files leave shared,
how a worker confirms its starting content, how to read an
authentication-shaped launch error, and what a worker does with a choice its
packet leaves open. Each rule changes what is launched, waited for or reported;
none adds a queue, retry loop or record.

## Refused launches

Classify a rejected dispatch by whether a worker started. When the runtime
refuses the call itself, nothing ran:

- A malformed invocation, such as a bad argument, may be corrected once. That
  is not a worker retry.
- An active-agent, concurrency or capacity limit is backpressure. Hold the
  packet in a native wait until a slot frees, and launch the validated batch in
  waves no larger than the limit; what each freed slot runs first stays the
  caller's decision ([Orchestrate](../../orchestrate/SKILL.md#before-any-dispatch)).
  Waves under a limit are not a partial launch, a failed worker or a reason to
  reroute, and holding a packet inside the caller's window is a wait, not an
  AgentOps queue.
- A packet still unstarted when the caller's window ends is reported as
  `not launched`, never as failed. A required judgment leg becomes unavailable
  only then, not because a slot was busy.
- Any other failure to start is `launch failed`. Running that packet inline or
  on another executor or model is the caller's decision, disclosed in its
  result, and a substitute from another family never satisfies a required one
  ([model dispatch](model-dispatch.md#selected-adapters)); running inline in a
  context that is not fresh never counts as a fresh judgment leg.

A worker has failed only when it launched and then failed.

## Workspace isolation

Create a writer's workspace through the selected runtime's own isolation option
where it has one. A worktree made by hand is invisible to the runtime's tracking
and cleanup; it stays the caller's to remove, under the integration proof in
[the removal rule](../SKILL.md#before-launch-and-while-running).

Before creating one, detect isolation that already exists. Resolve the git
directory and the common git directory to absolute paths and compare them: when
they differ, the session is in a linked worktree, unless its git directory
belongs to a submodule, which a superproject check tells apart. A session
already in a linked worktree works there and never nests another worktree inside
it. Workers it launches still need their own isolation, as peers of that
worktree rather than inside it.

## Shared runtime

Disjoint write scopes do not make workers independent. Concurrent workers,
read-only ones included, contend when they or their checks and services write,
install into or hold exclusively the same:

- port or dev server;
- local database, cache or global config;
- browser profile, browser session or device;
- package install;
- an external API quota their checks call.

A shared model-provider limit is not one of these: it is backpressure under
[refused launches](#refused-launches), launched in waves, not serialized.

Name such resources among the packet's effects. Give each worker its own
instance, such as a port or path taken from its environment or a copied
database, or serialize only the packets that contend. A resource only one
process can hold serializes every packet that needs it.

## Starting content

A runtime-made workspace may be cut from another base than the caller's
checkout, such as the primary checkout's branch or the default branch, and
uncommitted changes never cross into it. Pass the intended starting commit with
the packet. Before its first edit the worker compares its HEAD with that commit
and stops on a mismatch; the result is a launch failure, never a candidate.
Resetting or rebasing the workspace to repair it is outside the packet's
authority.

## Authentication-shaped errors

From a sandboxed or network-restricted launch, an authentication-shaped error
does not show that the account is logged out: blocked egress can produce the
same text. Report the error verbatim. Attribute it to credentials, or suggest a
login, only once the launch is known to have reached the provider.

## Open choices

A headless worker cannot ask. When its packet leaves a choice open, it takes no
irreversible or out-of-scope step on a guess: it finishes the independent parts,
leaves existing content in place and returns the choice under `gaps` with its
recommendation. The caller answers a choice that accepted intent already
settles through the runtime's follow-up turn on that worker, and escalates only
a choice nothing settles. When a choice can be framed only after a scan,
dispatch the scan, settle the choice, then dispatch the action with the scan
result passed by reference.
