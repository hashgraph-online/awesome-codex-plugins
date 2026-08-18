---
name: swarm
description: Dispatch explicit disjoint packets exactly
---
# Swarm

Swarm exposes one optional factory port:

```text
dispatch_once(explicit_disjoint_packets, executor)
  -> per-packet candidate | evidence | error
```

The caller supplies every complete packet, proves their write scopes disjoint,
and chooses the executor. Swarm dispatches each packet once, preserves packet and
context identities, collects results, and stops.

Write scopes must be **workspace-relative and canonical** — symlink-resolved and
already normalized. The disjointness check is lexical: it case-folds prefixes so
scopes differing only by case are treated as a collision (safe on
case-insensitive filesystems), but it cannot see a symlink that aliases two
scopes onto one target. Supplying non-canonical or symlinked scopes forfeits the
disjointness guarantee; a non-empty `write_scope.exclude` is rejected, not
silently ignored, because the proof cannot honor it.

Exactly-once dispatch over proven-disjoint scopes is why parallel failures stay
independent: no packet can observe, block, or corrupt another, so N packets
yield N verdicts about N experiments rather than one tangle.

Named failure mode — **partial-batch launch**: dispatching valid packets before
discovering an invalid one, leaving the batch half-run; validate the entire
batch before the first call.

Anti-pattern: re-dispatching a packet whose executor returned an error.
Corrective: return the error as that packet's factual result; retry is the
caller's decision, not the dispatcher's.

The reference implementation is [`scripts/dispatch_once.py`](scripts/dispatch_once.py).
It validates the entire explicit batch before the first call, invokes the supplied
executor exactly once for each packet, and returns executor exceptions as factual
per-packet errors.

Swarm's own effect is invoking the selected executor once per packet; the real
blast radius rides on the packets. Each packet's transitive effects — whatever
its executor writes, runs, or reaches — are the caller's to declare on the
packet, not Swarm's to bound.

Swarm does not select work, create packets, schedule from a backlog, persist a
queue, claim ownership, retry, validate, integrate, close, use Git, or deliver.
Executor failures remain executor evidence and cannot become core phase or
verdict state. The adapter cannot select AgentOps semantics, issue a binding verdict, or turn factory completion into delivery or validation proof.
