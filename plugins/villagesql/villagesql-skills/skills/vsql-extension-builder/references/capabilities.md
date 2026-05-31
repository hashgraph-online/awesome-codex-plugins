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
  They may include column storage, index hooks, system variables, and
  background threads. If a preview API is needed, record it in
  `.claude/tracking/limitations.md` so it surfaces in the README.

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
