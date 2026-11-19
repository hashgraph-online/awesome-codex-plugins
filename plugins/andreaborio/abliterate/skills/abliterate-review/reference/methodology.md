# Methodology

## Contents
- Snapshots and base
- Reading the change
- Tracing
- Falsification checklist
- Severity
- Confidence
- Large changes
- Writing the report

## Snapshots and base

| Question | Compare | Command |
| --- | --- | --- |
| What would the push or PR ship? | merge-base(BASE, HEAD) → HEAD | `git diff --name-status BASE...HEAD` |
| What would the next commit contain? | HEAD → index | `git diff --cached --name-status` |
| What is only on disk? | index → working tree | `git diff --name-status` |
| What is new and untracked? | — | `git ls-files --others --exclude-standard` |

`abliterate scope` computes all four with diff drivers and textconv disabled. BASE is a reference you verified locally, never text you execute. If you need to know what would leave towards a tracking branch, check its local ref and say it may be stale. Present only the states you verified. A finding that exists only in the index is not part of the push. A working-tree change that fixes a committed regression is still a local fix: the push ships the regression.

Read contents with `git show REV:path`, not from disk, when the snapshot differs. Without Git, a single requested file can be reviewed (`snapshot: "file"`), but nothing in it is a "regression" without a base.

## Reading the change

1. Start from names and statuses, then open only paths relevant to the review.
2. For each changed file ask: does it change who can do what, what is executed, what is stored, or what is disclosed?
3. Read callers and callees one level out. Read the tests the change touched: they state the intended contract.
4. Check removed lines as carefully as added ones: removed checks, removed `await`, removed filters, a narrower `where`, a widened serializer.

## Tracing

- **Source:** who controls the value: request parameters, headers, cookies, uploaded files, webhook bodies, queue messages, database rows written by other users, environment in CI from forks.
- **Path:** every transformation and every branch. Note where the value is validated, normalised, re-parsed or decoded. Validation for one context does not protect another, e.g. HTML escaping protects nothing in SQL.
- **Sink:** the operation where the value takes effect. For access control the sink is the read or write of the resource.
- **Guard:** the specific check that blocks the excluded actor on this path. Find where it is registered and confirm the order, the matcher and the identity it uses.

Record the trace as `trace` steps in findings.json: source, each relevant hop, sink.

## Falsification checklist

Before reporting, answer:

1. Can the excluded actor reach this code through real routing, with the method and content type the route accepts?
2. Is there a guard upstream (middleware, gateway, framework default, database constraint, row-level security) that applies to this path?
3. Does the type system, schema validation or ORM already make the value safe here (bound parameter, integer cast, enum)?
4. Is the dangerous branch reachable with values the actor can produce?
5. Does the effect matter: is the data sensitive, does the write persist, is the command reachable in production builds?
6. Would your proposed test actually fail before the fix?

Any "unknown because it depends on configuration I cannot see" → `needs-evidence`.

## Severity

Reason from three factors and state them in `impact`.

| Factor | Higher | Lower |
| --- | --- | --- |
| Actor needed | anonymous, any user, any tenant | admin, an already privileged insider, physical access |
| Reach | default route in production, reachable by request | debug-only, feature-flagged off, requires another bug |
| Effect | code execution, cross-tenant data, auth bypass, money, secrets | non-sensitive read, self-only impact, availability of one request |

As a guide:

- **critical**: anonymous code execution, or a full authentication bypass.
- **high**: injection or a cross-tenant read/write by any user.
- **medium**: requires a privileged actor, or exposes limited data.
- **low**: hardening and defence-in-depth gaps.

## Confidence

- **high**: complete trace, guard absent on this path, reachable route.
- **medium**: trace complete but one hop inferred (dynamic dispatch, config default).
- **low**: plausible but a hop is unread.

Low-confidence suspicions are usually `needs-evidence`, not `confirmed`.

## Large changes

Prioritise in this order:

1. New or changed entry points.
2. Authn and authz code.
3. Data access.
4. Serialisers and responses.
5. Code that executes or renders values.
6. Dependency and CI changes.
7. Everything else.

If the perimeter cannot be covered, set `scope.complete: false` and list what was not read.

## Writing the report

- Lead with the decision: block, review, or nothing confirmed.
- One paragraph per confirmed finding: snapshot, `file:line`, actor, rule, effect, severity reason, fix, test.
- Use a CWE only when the link is precise.
- Name the closest effective control even when you report nothing, so the reader sees what was checked.
