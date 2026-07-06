# VEF Capability Discovery

Do not assume limitations from prior knowledge. Probe the SDK and the
running server.

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

- **Extension upgrade path.** Test `ALTER EXTENSION` or equivalent. If it
  doesn't exist, type changes require `UNINSTALL` + `INSTALL` — document
  for users.

- **REAL-returning functions with integer input.** If the extension includes
  a `.returns(REAL)` function, test it with an INT column and inspect the
  result type via `DESCRIBE`. If it shows INT rather than DOUBLE, document
  the `CAST(col AS DOUBLE)` or `col * 1.0` workaround, record the limitation,
  and link [villagesql-server#608](https://github.com/villagesql/villagesql-server/issues/608).

- **STRING return size and charset.** VDF STRING results are subject to two
  current behaviors that affect any function returning text:
  1. **256-byte cap.** The SDK truncates STRING returns to the server's
     `max_str_len` (currently 256 bytes). Test with a function that builds
     a string longer than 256 bytes and check whether the result is
     silently truncated. If the extension needs to return larger payloads
     (e.g. a JSON array of many values), design around the cap — chunked
     enumeration, prefix-filtered queries, or splitting across multiple
     calls. Track villagesql-server
     [#641](https://github.com/villagesql/villagesql-server/issues/641)
     and [#343](https://github.com/villagesql/villagesql-server/issues/343).
  2. **Binary charset.** STRING results are tagged `binary`, so MySQL
     JSON functions (`JSON_EXTRACT`, `JSON_TABLE`, etc.) reject them
     without an explicit `CONVERT(... USING utf8mb4)`. Test by piping a
     result through a JSON function and document the `CONVERT` step in
     the README if users will consume the output as JSON. Track
     villagesql-server
     [#612](https://github.com/villagesql/villagesql-server/issues/612).
