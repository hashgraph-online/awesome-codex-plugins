# VEF Capability Discovery

Do not assume limitations from prior knowledge. Probe the SDK and the
running server.

**Confirm negatives before recording them.** A syntax error on a guessed
statement form proves only that the guess was wrong, not that the
capability is missing. Before recording "X does not exist" as a
limitation, check the server grammar (`grep -i '<keyword>' sql/sql_yacc.yy`
in the server source) and search the server's open issues for the
capability name — an issue that presupposes the statement exists means
it does. When citing a server issue number in shipped docs, verify it is
still open first; a closed issue usually means the behavior it describes
has changed.

## Header-discoverable (Phase 2 bootstrap)

Assess all capabilities from the typed API headers (`vsql.h` and the
`vsql/` subdirectory).

- **Storage model.** Does the type builder expose only fixed-length
  storage, or also variable-length? For fixed-length, the persisted length
  sets the storage size and encode must write exactly that many bytes;
  returning 0 via the length output parameter signals an error.

  **If only fixed-length storage is available** and the type is
  inherently variable in size (e.g., hstore, JSON-like, packed lists),
  apply this workaround — only if the probe above confirms no
  variable-length API exists:
  1. Size `persisted_length` to your practical maximum (e.g., the largest
     valid value the type accepts).
  2. In encode: write the real data, then zero-pad to fill exactly
     `persisted_length` bytes. Encode must write exactly that count.
  3. Embed an in-band header at a fixed offset (e.g., a 2- or 4-byte
     byte count at the start) so decode knows where real data ends.
  4. In decode: read the in-band length, then process only that many
     bytes — ignore the zero padding.
  5. Document this constraint in README under Known Limitations, naming
     the VEF capability that would remove the need for it.

- **Parameterized types.** Does the SDK expose registration functions for
  types that accept `TYPE(N)` or `TYPE('key=value')` arguments? Look for
  two registration flavors (integer shorthand and key=value string) and
  the struct that carries parameter data from server to extension. Record
  exact names. The canonical example is
  `villagesql/examples/vsql-tvector/src/tvector.cc` in the server source
  tree.

- **Index registration.** Is an index registration API present? If not,
  custom type columns cannot be indexed — do not design around index-based
  lookup.

- **Max VDF parameters.** Read the max-parameter constant. Functions
  needing more inputs must use structured types or be split.

- **Preview capabilities.** Headers under a `preview/` subdirectory are
  preview capabilities — documented but unstable across server builds.
  Read what is actually present; do not assume specific APIs exist. If a
  preview API would meaningfully improve the implementation, present the
  trade-off to the user (see Phase 2 step 2f). Record any preview API use
  in `.claude/tracking/limitations.md` so it surfaces in the README.

## Behavior-discoverable (after first install in Phase 3)

These can't be probed in Phase 1 because no extension is installed yet.
Run them as part of Phase 3 once the extension is built and installed for
the first time, and record results in `.claude/tracking/limitations.md`.

- **Aggregate functions.** Create a custom type column and test `SUM` or
  `AVG`. If they fail, only `COUNT(DISTINCT)`, `MIN`, `MAX`, and
  `GROUP_CONCAT` are safe — document this constraint.

- **Extension upgrade path.** The in-place upgrade statement is
  `ALTER EXTENSION <name> VERSION '<version>' AT RESTART` — the `VERSION`
  and `AT RESTART` clauses are required, so a bare `ALTER EXTENSION <name>`
  is a syntax error and proves nothing. Test the full form, with populated
  custom-type columns present. Only if it fails should you document
  `UNINSTALL` + `INSTALL` as the upgrade path.

- **REAL-returning functions with integer input.** If the extension includes
  a `.returns(REAL)` function, call it on an INT column (and, if it takes
  no arguments, with none) in `CREATE TABLE t AS SELECT ...`, then run
  `SHOW CREATE TABLE t`. VillageSQL 0.0.7 and earlier declare the column
  `double(22,0)` and round away the fraction. Nightly builds from
  2026-10-13 and releases after 0.0.7 declare `double`
  ([villagesql-server#1327](https://github.com/villagesql/villagesql-server/pull/1327)).
  If the probe shows `double(22,0)`, document
  the `CAST(col AS DOUBLE)` or `col * 1.0` workaround, record the
  limitation, and name the server version that fixes it.

- **STRING return size and charset.** Three behaviors affect any function
  returning text; the third also affects BINARY returns. All three change
  across server versions — probe the running server rather than trusting
  this file:
  1. **Size is bounded by the declared buffer size.** STRING returns are
     capped at the `.buffer_size()` the function declares at
     registration, not at a server-wide constant. (Older servers
     silently truncated all STRING returns at 255 bytes; that is fixed.)
     If the extension returns large payloads, size the buffer to match
     and test with a result longer than 255 bytes to confirm the running
     server does not truncate.
  2. **JSON functions reject the result without CONVERT, on VillageSQL 0.0.6
     and earlier.** There, even where `CHARSET(<func>(...))` reports
     `utf8mb4`, MySQL JSON functions (`JSON_EXTRACT`, `JSON_TABLE`, etc.)
     reject a VDF STRING result with `ERROR 3144: Cannot create a JSON
     value from a string with CHARACTER SET 'binary'`. Wrap the argument in
     `CONVERT(... USING utf8mb4)` and document that step in the README
     if users will consume the output as JSON. Fixed in VillageSQL 0.0.7 —
     check `SELECT VERSION()` against the target server rather than
     assuming either behavior.
  3. **A materialized column is sized from the argument, not the output,
     unless told otherwise.** `CREATE TABLE t AS SELECT func(args...)`, a
     derived table, or any other materialization (a live `SELECT` is
     unaffected) infers the result column's width from the widest
     *argument*, not from what the function can actually return. A
     function whose output can exceed its arguments' width — fixed
     overhead, no arguments at all, or real expansion in the algorithm —
     then fails with `ERROR 1406 (Data too long for column ...)` the first
     time it is materialized, even though a bare `SELECT` of the same call
     looked fine. Grep the SDK header for `max_result_length` on
     `FuncBuilder`/`AggFuncBuilder` (`vsql/func_builder.h`); where present,
     declare it (after `.returns(...)`) on each STRING- or BINARY-returning
     function whose output can exceed its arguments' width, sized to the
     true maximum output in characters for STRING or bytes for BINARY; the
     declaration needs protocol 5, so VillageSQL 0.0.8 or newer. Test
     the fix with `CREATE TABLE t AS SELECT func(...)` specifically — a
     bare `SELECT` does not exercise this path and passes either way.
