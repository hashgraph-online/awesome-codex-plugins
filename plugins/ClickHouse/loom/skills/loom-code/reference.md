# loom-code — full reference

The complete substitution table, result-reading rules and the verification gate. `SKILL.md` carries the short form; open this file only when a row below is what you need.


> When this plugin is installed, the `loom-code-shunt` PreToolUse hook enforces
> the substitutions below mechanically: a whole-file `Read` (> 350 lines), a
> tree-wide `Grep`, or a bulk `cat`/`rg` inside an indexed repo is denied with a
> reason naming the op to call. Targeted reads (`offset`/`limit`, a single file)
> and your own modified files always pass. `LOOM_CODE_SHUNT=off` disables it.

Ops below are named by their dotted name. A listed one is the MCP tool
`loom_<op>` with dots as underscores (`code.symbol` → `loom_code_symbol`);
one your tool list does not show (`code.test_gate`, `code.trace`,
`code.verify`, `code.history`) runs through `loom_op {op, arguments}`.

The index answers for the indexed commit (`as_of`): merged code. Your own
uncommitted edits are not in it — read or grep those files, and hand the
diff to `code.impact` / `code.test_gate`, which compute its reach against
the indexed graph.

## About to reach for a default? Substitute.

The expensive case is not a hard question — it is the reflexive Grep/Read
that needs no thought. Catch these:

| About to… | Use instead | Why |
|---|---|---|
| Grep a **symbol name** across the tree | `code.symbol` | definition + signature + doc in one call; grep hands you N call sites to eyeball |
| Grep a **concept** ("where do we retry s3 uploads") | `code.search` | ranked semantic+lexical; grep only matches the words you guessed |
| Answer "**who calls X**" by grepping the name | `code.callers` | compiler-exact (scip tier); grep cannot tell a call from a comment, string, or same-named overload |
| Judge "**is it safe to change X**" | `code.impact` | transitive radius + tests that reach it + files that usually co-change |
| Review your **own uncommitted diff** before finishing | `code.impact` with `files=[...]` and/or `diff=<your diff>` | the index can't see your working tree, but it computes what the diff touches against the base graph — blast radius, tests to run, and co-change partners your change did NOT touch |
| Say **"done"** on a change without naming its tests | `code.test_gate` with `files=[...]` and/or `diff=<your diff>` | the tests that reach your change in evidence order — a test you edited, the stem partner of a file you changed, the mined test map, call-graph hops — each with a `run` command when derivable (never guessed), plus `untested`: touched functions no test reaches. Run the tests and rely on green; write a test for the untested rows or say why not |
| Run **`gh pr create`** on a change | `code.pr_check` with the title, body, changed paths, symbols and the issues it closes | a verdict over loom's PR ledgers — `duplicate_of` when an open PR is already doing this or a merged one already did (check main before you push), `related` to read first, `none` to open it — each item with state and evidence lines (files shared, same issue closed, a backport of yours); a title alone never reads as a duplicate |
| Paste-and-eyeball a **stack trace** | `code.trace` | every frame resolved to its definition in one call, trace order preserved |
| Convince yourself a **claim about the code is true** ("nothing calls X", "A reaches B", "this file defines Y") before acting on it | `code.verify` | a three-valued verdict with evidence — and it will NOT say "refuted" from an absence (the graph is a floor); it says "not_established" and names what it couldn't see, so you don't act on a false negative |
| Read whole files to understand one function | `code.symbol`, then read only the returned span | the file is not the unit of an answer |
| Read a whole file to see **what is in it** | `code.outline` with `path="src/F.cpp"` | every declaration with its line span in source order, ~1.5K tokens for a 9,000-line file; then Read the one span (offset/limit) or `code.symbol` the name. A 200+ line class from `code.symbol` arrives the same way: skeleton + member outline, not a 12K-char join |
| Open a file to see the **function around a grep hit** (`path:line`) | `code.symbol` with `name="src/F.cpp:123"`, or `code.enclosing` with `include_body=true` for many hits | the innermost function containing that line, body included, in one call — no file read |
| Grep an **exact literal/error string** | `code.grep` | same exactness, but each hit arrives with its enclosing symbol, and unindexed fixture files don't pollute the list; `neighbours=true` on the same `code.grep` call adds callers / callees / tests / citing docs per enclosing function |
| Work in an **unindexed repo or branch** | plain grep/rg — loom cedes this | no index, no answer; the abstentions will tell you |

## Reading a result

- Every `code.search` result row carries risk annotations: `churn` (merged
  PRs touching the path — a FLOOR bounded by PR-history coverage), `amp`
  (1-hop caller count), `tested` (a mapped test reaches it), and `callees`
  (its immediate calls — you rarely need a follow-up `code.callees`).
- `abstain: true` is an answer — the index says "nothing relevant", and its
  precision on that call is measured. Do not retry with synonyms more than
  once; fall back to grep instead.
- `as_of` on every response names the branch/commit the index reflects. A
  "not found" for a symbol you *just wrote* is expected staleness, not a
  tool failure — the index trails the working tree by up to a few minutes.
- Caller/impact counts are floors, not totals: dynamic dispatch through
  function pointers is invisible to any static tier.
- An empty `code.impact` / `code.outline` names why in `verdict` (`code.verify`
  in `index_verdict`): `no_static_callers`, `no_indexed_paths` and
  `no_seeds_in_hunks` are **answers** (nothing calls it; the change touches no
  indexed function) — do not grep to double-check them. Only `not_covered` and
  `no_match` mean the index could not tell (`abstain: true`); grep then.

## The gate: a claim about the code needs a verdict, not a hunch

Before you state a structural fact — "nothing calls X", "A reaches B", "this
file defines Y", "removing this is safe" — run `code.verify` for it and act on
the verdict: `confirmed` / `refuted` carry evidence you can cite; `not_established`
means the graph could not see it (a floor, not a negative) and your sentence
must say so. `abstain: true` on a search is an answer, not a failure to retry.

When loom is unreachable, `as_of` is stale past a few minutes, or the path is
`not_covered`, do **not** present the claim as checked. Say it was **not
verified against the index**, fall back to grep for what grep can see, and
name what it cannot (dynamic dispatch, overloads). A degraded path is stated
out loud, never absorbed into a confident sentence.

## Stop rules

- One clear `code.search` hit plus one focused read of the returned span is
  enough — do not chain `code.callers` + `code.impact` + `code.history` as
  a ritual.
- If two loom calls in a row didn't move you forward, grep. Honestly ceding
  the queries loom loses keeps the wins trustworthy.
