# Module depth: signals, evidence and seams

Supporting detail for [Architecture](../SKILL.md). Read the section the current
step needs; none of it is required on every run. The vocabulary lives in the
skill root.

## Gathering evidence from history

These reads are read-only. Pick a window that matches the pain and report it
with the result: `<window>` is `--since='3 months ago'` for a period, or
`<tag>..HEAD` for the last release (`--since` takes a date; given a tag it
filters nothing). Scope `<path>` to the area under suspicion when one is known.

```bash
# Churn: files changed most often in the window.
git log <window> --format= --name-only -- <path> | sort | uniq -c | sort -rn | head -20

# Co-change: file pairs that land in the same commit (pairs seen 3+ times).
# The pathspec selects commits; --full-diff keeps every file they touched,
# so partners outside <path> show up.
git log <window> --full-diff --format='@%h' --name-only -- <path> \
  | awk 'function flush(){for(i in f)for(j in f)if(i<j)p[i" "j]++; delete f}
         /^@/{flush(); next} NF{f[$0]=1}
         END{flush(); for(k in p)if(p[k]>2)print p[k], k}' | sort -rn | head -20

# Fix clusters: files touched by commits whose subject starts with fix.
git log <window> --format='@%s' --name-only -- <path> \
  | awk '/^@/{fix = tolower($0) ~ /^@fix/; next} fix && NF' | sort | uniq -c | sort -rn | head -20
```

Read the numbers as leads. Generated files, lockfiles, changelogs and mass
renames inflate churn and co-change; exclude them and say so. A pair that
co-changes because one is the test of the other is expected locality, not
leakage. A commit subject is a weak label for a fix; open the commits before
calling something a defect cluster.

## Signals, how to confirm them, and look-alikes

| Signal | Confirm by | Often a false positive when |
|---|---|---|
| Pass-through layer | Each method forwards its arguments to one callee with no rule of its own | The layer is an adapter translating between a domain type and a technology |
| Interface as complex as the implementation | Callers pass most internal choices as parameters | The module is a deliberate low-level primitive other modules build on |
| Required call order | Callers repeat the same setup and sequence; misuse yields wrong results, not errors | The order is part of the domain (a workflow whose steps people recognise) |
| Decision repeated across modules | One rule (a format, a threshold, a mapping) is edited in several files per change | The copies belong to different contexts and are meant to diverge |
| Option growth | Flags added one caller at a time; branches on the flag throughout | Options are independent and each is tested at the interface |
| Tests mocking internals | Tests construct collaborators the caller never sees, or assert call sequences | The mocked thing is an adapter at a real seam |
| Helper extracted to be testable | The helper has its own tests and one caller, yet fixes keep landing in that caller's wiring, which no test reaches | The helper holds a rule several callers share, or the caller is itself tested through its interface |

## Where a boundary belongs

A context boundary shows up as a change of language: the same word with
different rules on each side, or a translation function that converts one
shape to another. Put the boundary where the translation already happens, and
let each side keep its own model. [Domain](../../domain/SKILL.md) owns the term
work; this skill uses the result.

Dependency direction is checkable from imports. List what the domain-rule
files import; any storage driver, HTTP client, CLI library or serialization
format there is a direction problem. The usual repair is a port: an interface
named in domain terms, owned by the domain side, implemented by an adapter.

## Seams and how tests cross them

What sits behind a seam decides how the module is tested through its interface:

- **Pure computation or in-memory state.** No seam is needed. Test through the
  interface directly.
- **A dependency with a fast local substitute** (an in-memory store, a
  temporary directory). Keep the substitute inside the module's test setup;
  the interface does not need to expose a port for it.
- **A system you own across a process boundary.** Define a port in domain
  terms, a production adapter and an in-memory adapter for tests.
- **A third-party system.** Define a port and a fake adapter for tests, and
  check the real adapter separately against the provider's contract.

A seam with one implementation is a guess about future variation. Propose one
when a second implementation exists or is already required (a test double
counts), or when the port reverses a dependency that points the wrong way.

When a module deepens, tests that reached past the old interface usually
become redundant once equivalent tests exist at the new one. Name them in the
proposal so the executor removes them deliberately rather than leaving two
suites that describe the same behavior.

## Designing alternatives

Alternatives teach more when they differ on one axis at a time. Useful axes:

- **Where the decision lives:** the caller decides and passes it in, or the
  module decides from what it already knows.
- **How many entry points:** one general operation, or a few named for the
  cases callers actually have.
- **What crosses the interface:** the caller hands over raw inputs and gets an
  outcome, or gets back data or a plan to act on itself.

Write each alternative as the call site a real caller would write, using a
caller found in step 3. Count what that caller must know, prepare and handle.
"Leave it" is costed the same way: what the next change in the pain area will
cost if nothing moves.

## Migration that stays working

Expand, migrate, contract keeps every step shippable:

1. **Expand.** Add the new interface beside the old; the old may delegate to
   the new. Nothing breaks.
2. **Migrate.** Move callers in small slices, each with its checks green.
   Stopping here leaves two working paths.
3. **Contract.** Remove the old interface once no caller uses it. This is
   usually where reversal stops being cheap, especially for exported names,
   serialized fields and stored data.

Name the step where reversal stops being cheap in each proposal. Persisted or
published shapes need a compatibility plan before contract, not after.

Once callers sit on the new interface, the next change can import straight
past it again. When the friction was callers reaching into a module's
internals or importing against the dependency direction, say under Migration
whether an import rule that runs with the build should hold the new shape, or
why not; [Research](../../research/SKILL.md#evidence-rules) sets when a
blocking check is earned. State such a rule over the tree's layout rather than
per named package, so adding a package needs no edit to the rule.
