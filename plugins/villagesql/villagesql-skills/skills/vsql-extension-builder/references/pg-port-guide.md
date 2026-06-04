# PostgreSQL Port Guide

Load this file at the start of Phase 1 when `pg_port: true` is recorded in
`architecture.md`. Read it before researching the source extension.

## Pre-Port Analysis (do this before architecture.md)

**Source research — best-effort, two lookups max. Do not block or retry.**

1. **Official docs.** Check postgresql.org for the extension (e.g.
   `https://www.postgresql.org/docs/current/<name>.html`). If it's a
   contrib extension it will be there; third-party extensions won't be.

2. **Source repo.** Search for the extension's GitHub repo
   (`<name> postgresql extension site:github.com`). If found, fetch:
   - The README for function signatures, NULL semantics, and operator
     mappings.
   - The regression test file (`sql/<name>.sql` or similar) — concrete
     input/output pairs to adapt directly into acceptance criteria.
     These are higher-value than prose docs for implementation.

If either lookup fails or returns nothing useful, proceed from the user's
description and your own knowledge of the extension. Record what was found
(or "not found") in `architecture.md` under `## Source Research` before
continuing.

Enumerate the source extension's full function list and categorize each:

| Category | Meaning |
|---|---|
| **Full** | Implementable with exact semantics under current VEF |
| **Workaround** | Implementable with a meaningful behavioral difference (e.g. JSON array instead of row set) |
| **Blocked** | Not implementable under current VEF — document in `limitations.md` immediately |

Record this table in `.claude/tracking/architecture.md` under
`## PostgreSQL Function Map`. Never start writing C++ until the map is
complete — missing functions discovered in Phase 3 cause expensive rework.

**Run this checklist before categorizing. Each "yes" requires special
handling — see the relevant section below:**

- [ ] Set-returning functions (SRFs like `skeys`, `svals`, `each`, `unnest`)?
- [ ] Catalog or system table access?
- [ ] Aggregate functions?
- [ ] `CHECK` constraint validators or trigger functions?
- [ ] `DEFAULT` expressions that call functions?
- [ ] Per-connection or per-session state?
- [ ] Functions marked `IMMUTABLE` for index optimization?
- [ ] Large data structures (could exceed `max_allowed_packet`)?

**Blocked by default:**
- SRFs — VEF has no row-set return; use JSON array workaround (see below)
- Catalog/system table access — not available to VEF extensions
- Aggregate functions — probe in Phase 3 step 3; treat as tentative-blocked
- Trigger functions — MySQL triggers are SQL-only; cannot delegate to UDFs
- CHECK constraint validators — MySQL 8.0.16+ enforces CHECK but cannot call UDFs

## Type Mapping

| PostgreSQL type | MySQL/VEF type | Notes |
|---|---|---|
| `text`, `varchar` | VEF `STRING` | Use `VARCHAR(N)` in DDL; pick N from domain |
| `bytea` | `VARBINARY` | Binary-safe; never use `VARCHAR` for binary data — MySQL will corrupt it with charset conversion |
| `boolean` | `TINYINT(1)` | MySQL won't enforce 0/1 at storage — **do it in C++** |
| `integer`, `int4` | `INT` | |
| `bigint`, `int8` | `BIGINT` | Signed max 2^63−1; same as PG `bigint` but not `numeric` |
| `real`, `float4` | `DOUBLE` | Use `DOUBLE` not `FLOAT` — MySQL `FLOAT` is 32-bit (~7 sig digits) and lossy |
| `double precision`, `float8` | `DOUBLE` | |
| `numeric`, `decimal` | `DECIMAL(M,D)` | MySQL max M=65, D=30; PG `numeric` is arbitrary-precision — document overflow if the domain exceeds this |
| `uuid` | vsql-uuid `uuid` type if available; else `BINARY(16)` | `BINARY(16)` sorts lexicographically, not RFC 4122 order — document if ordering matters |
| `json`, `jsonb` | MySQL `JSON` | Always UTF-8 internally; no charset handling needed in C++ |
| `timestamp` | `DATETIME` | No timezone field |
| `timestamptz` | `DATETIME` | The UTC offset is discarded entirely — document this; recommend callers normalize to UTC before storing |
| `interval` | `BIGINT` (milliseconds) | Milliseconds preserve sub-second precision; document the unit |
| Custom/opaque type | VEF custom type with binary storage | |

## Parse-time Normalization

PostgreSQL types often silently rewrite input into a canonical form before
storing it. The `from_string` (encode) function is not just a parser — it is
a normalizer. Normalization must be correct before any other behavior can be
tested, because equality checks, hash, compare, and round-trip tests all
implicitly depend on it.

**Check this before writing a single line of encode code.** Look at the
PostgreSQL source or regression tests and answer: does this type enforce a
canonical form at input time? Common cases:

| Type | Normalization |
|---|---|
| `hstore` | Deduplicates keys — last value wins; result is sorted by key |
| `tsvector` | Deduplicates and sorts lexemes; merges positions |
| `jsonb` | Deduplicates object keys (last wins); sorts object keys canonically |
| `inet` / `cidr` | `cidr` masks host bits to zero; both normalize leading zeros |
| `tsquery` | Flattens and normalizes operator tree |
| `ltree` | No dedup, but validates label syntax strictly |
| Arrays | No dedup, but element order is preserved and significant |

**What to do:**

1. Identify every normalization rule for the type from the PostgreSQL docs or
   source (`src/backend/utils/adt/<type>.c`, `from_string` / `input` function).
2. Add at least one acceptance criterion per normalization rule that exercises
   the non-trivial case — duplicate input that should collapse, out-of-order
   input that should sort, host bits that should be masked.
3. Verify the criterion against a live PostgreSQL instance if possible, not
   just against the docs. The docs sometimes underspecify edge cases.
4. Implement normalization in the encode function before writing any VDF.
   A VDF built on top of un-normalized storage will produce wrong results
   for any input that triggers the normalization case.

**The failure mode if you skip this:** tests pass because test inputs are
well-formed. Users encounter silent semantic differences only when they feed
the type data that PostgreSQL would have normalized — duplicate keys, unsorted
elements, masked host bits. These bugs are hard to diagnose because the
extension appears to work correctly on clean data.

## NULL Semantics

MySQL propagates NULL by default (matches PostgreSQL's `CALLED ON NULL INPUT`).

- Check `arg->is_null` first — return `IS_NULL` for any required NULL argument.
- Exception: functions explicitly NULL-safe in PostgreSQL (e.g. `COALESCE`-like) — preserve and document.
- Never silently coerce NULL to a default value. If the PG function does this, document it.
- Division by zero returns NULL + warning in MySQL (not an error) — follow this for analogous numeric edge cases.

## Error Handling

PostgreSQL raises exceptions. MySQL convention: return NULL for bad input;
use the VEF error/warning mechanism for hard failures.

**Verify during Phase 2 bootstrap what warning/error API VEF exposes.** The
decision table below assumes one exists — confirm before designing error behavior.

| Situation | MySQL idiom |
|---|---|
| Invalid input format | Return NULL; emit VEF warning if available; document |
| Out-of-range value | Return NULL; validate in C++ — MySQL won't catch it; document valid range |
| Type mismatch caught at build time | Compile error via VEF typed API — no runtime check needed |
| Internal invariant violation | VEF error mechanism with descriptive message |
| Output buffer truncation | Return NULL; never silently truncate; document the limit |

Don't assume callers run `SHOW WARNINGS` — many frameworks suppress warnings
silently. For errors callers must detect, return a documented sentinel value.

## Operator → Function Translation

Every PostgreSQL operator becomes a named function. Use `TYPE_VERB` or
`TYPE_PREDICATE` naming. Key patterns:

| PG operator | MySQL function |
|---|---|
| `->` / `->>` | `<type>_get(val, key)` / `<type>_get_text(val, key)` |
| `#>` / `#>>` | `<type>_get_path(val, path)` / `<type>_get_path_text(val, path)` |
| `?` / `?&` / `?\|` | `<type>_has_key` / `<type>_has_all_keys` / `<type>_has_any_key` |
| `@?` / `@@` | `<type>_path_exists` / `<type>_path_match` |
| `\|\|` | `<type>_concat` or `<type>_merge` |
| `-` (delete key/value) | `<type>_delete` / `<type>_delete_val` |
| `@>` / `<@` / `&&` | `<type>_contains` / `<type>_contained_by` / `<type>_overlaps` |

**Rules:** Type prefix is the type name, not the extension name. Boolean
predicates use adjective/verb form (`contains`, not `is_contained`). Avoid
reserved words: `keys`, `values`, `check`, `table`, `index`, `select`,
`delete`, `replace`, `insert`, `update` — use `<type>_keys`, `<type>_vals`
etc. Verify names don't conflict with MySQL 8.0.x built-ins for the target
version range.

## Set-Returning Functions

VEF has no row-set return. Every SRF becomes a scalar function returning a
JSON array. JSON is preferred over CSV because keys/values may contain
commas, and `JSON_TABLE()` lets callers unpack it into rows if needed.

Commit to a documented element order (insertion, sorted, or undefined) and
test it. Callers may depend on it.

Document in the function reference: element type, structure, ordering
guarantee, and that `JSON_TABLE()` is the unpivot path.

Add a `limitations.md` entry for every blocked SRF: function name,
workaround offered, and a note about `JSON_TABLE()`.

## MySQL Behavioral Differences

These diverge from PostgreSQL and will cause bugs if not handled explicitly.

**Unsupported mechanisms — mark all functions relying on these as Blocked:**
- **CHECK constraint validators:** MySQL 8.0.16+ enforces CHECK but cannot
  call UDFs. Validate in the parse/store function instead.
- **DEFAULT expressions:** MySQL 8.0.13+ supports `DEFAULT (expr)` but not
  with UDFs. Provide SQL trigger templates or application-level defaults.
- **Trigger functions:** MySQL triggers are SQL-only. If the source provides
  trigger functions, supply SQL trigger templates that call the extension.

**Thread safety:** VEF runs in the calling connection thread. PostgreSQL's
process-per-connection model makes global state implicitly safe; MySQL does
not. Audit the source for global/static variables — any shared state needs
a mutex or connection-local storage.

**Expression-based indexes:** `CREATE INDEX ON t ((my_func(col)))` requires
the function to be deterministic. If the source marks functions `IMMUTABLE`,
those qualify — document which do and which don't.

**Memory limits:** `max_allowed_packet` (default 64 MB) caps function inputs
and outputs. If the extension processes large inputs, test at realistic sizes
and document the effective limit.

**Strict mode + generated columns:** If the function is used in a
`GENERATED ALWAYS AS (my_func(...)) STORED` column, a NULL return in strict
mode will fail the INSERT. Test this explicitly.

**Connection-local state:** If the source maintains per-session state, verify
during Phase 2 bootstrap whether VEF exposes connection-handle APIs for it.
If not, document the gap in `limitations.md`.

## "Migrating from PostgreSQL" README Section

Write this section after Phase 5 UAT so all examples are verified. Include:

1. **Function name mapping table** — PG name → VillageSQL name, every rename.
2. **Operator equivalents table** — PG operator → VillageSQL function call,
   with a one-line SQL example for each.
3. **Before/after SQL examples** — for the most common use cases, show the
   PostgreSQL query and the VillageSQL equivalent side-by-side.
4. **Behavioral differences** — NULL handling, error behavior, type
   differences (especially BOOLEAN enforcement, TIMESTAMPTZ offset loss,
   interval units), SRF return format and ordering, case sensitivity.
5. **Missing functions** — every Blocked function: one line on why, and the
   closest workaround.
