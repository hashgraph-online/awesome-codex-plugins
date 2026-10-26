# gate checks

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

### Check 0: Live connection to Figma

Two paths pass this check. Only an MCP call proves the connection: a shell command NEVER does.

- **Path A, figma-console (the path this repo validates).** AUTHORITY: `figma_get_status` with
  `probe:true`, returning `setup.valid=true` plus the correct `connectedFile`. A shell command
  cannot attest that the plugin is paired: ports 9223 to 9232 are a pure WebSocket with no HTTP
  endpoint (field note, 2026-08). Write path: `figma_execute` through the Desktop Bridge.
- **Path B, official Figma MCP server only.** When the official server is the only live connection
  (figma-console is not installed, or its Bridge is down): a successful `whoami` plus a successful
  `get_metadata` on the target (that call also satisfies Check 2). Write path: `use_figma`. Path B
  is not validated by this repo: keep writes small, read back every change. Follow the official
  server's own instructions for `use_figma`.
- [`figma-bridge-doctor/scripts/figma-status.sh`](../../figma-bridge-doctor/scripts/figma-status.sh) (in the `figma-bridge-doctor` skill's `scripts/`
  directory, macOS only; in Claude Code run it as
  `bash "${CLAUDE_SKILL_DIR}/../figma-bridge-doctor/scripts/figma-status.sh"`, which needs that skill
  installed next to this one) is LOCAL evidence only: Figma is running, servers are listening. By
  design it does not report pairing (it prints `current_file_pairing=ask_figma_get_status`). Use
  it for diagnosis, not as a verdict.
- If neither path confirms the connection, the write MUST be blocked. Bridge recovery goes through
  the `figma-bridge-doctor` skill: when figma-console is installed, try it before you fall back to
  path B.

> **Advisory pre-check A0 (optional, path A; path B already runs it):** Call `whoami` (official
> Figma MCP server) once per session if you do not know which seat the connected account holds OR
> you are writing to a file you do not own. A seat mismatch (for example a Dev seat writing to a published library) fails loudly
> with a permission error, so this is an *early feedback* convenience, not a silent
> failure preventer. **Skip for:** a solo developer on personal drafts, sessions where you already
> know the seat, or when you are on the Starter plan's MCP tool call budget. The 7 hard checks
> below cover the silent failures.

### Check 1: Target node-id confirmed

- Has the user provided a specific node-id OR is there an active Figma selection?
- "The header frame" is NOT confirmed. You need an explicit node-id.
- If ambiguous: run `get_metadata` and ask the user to disambiguate.

### Check 2: get_metadata run this session

- Has `get_metadata` been called on the target page or frame in this session?
- If NO: run `get_metadata` now and parse the structure.
- If YES: reuse the earlier result from this session.

### Check 3: get_variable_defs (if the write touches styled properties)

- Will the write set fills, strokes, spacing, typography or radii?
- If YES: `get_variable_defs` MUST have been called on the relevant scope.
- If NOT called: run it now.
- Required for token-bound writes.

### Check 4: search_design_system (if the write creates new UI)

- Will the write create a frame or component that COULD be an existing component?
- If YES: `search_design_system` MUST have been run with a relevant query.
- Block "new Button" / "new Card" / "new Input" writes if the search was not run.
- **ICONS / ILLUSTRATIONS (anti-hallucination, field note, 2026-06):** NEVER hand-draw an icon
  (`createNodeFromSvg` with invented geometry) before checking what the design ALREADY has. Two
  sources to scan FIRST:
  1. The file's icon component pages (for example an "Icons" page, whatever language it is named
     in). Instantiate those brand components. Do not redraw.
  2. The codebase's real assets. Grep the screen or component source for the actual icon: the
     `lucide-react-native` import name, a `require('../assets/icons/calendar.png')` asset, or an
     SVG file.

  Match the app's REAL icon. A tab bar that uses brand PNG icons must use those assets or their
  componentized equivalents, never a generic geometric calendar, trophy or user that you drew. If
  a needed icon has no component, use the real asset (image fill) and FLAG the library gap. Never
  substitute a look-alike you invented. Block any icon-bearing write where neither the icon
  library nor the app asset was checked.

**The WHOLE feature, not only the node you are about to write (field note, 2026-08).** The check
above is per write, and that is how one feature accumulated **dozens of hand-drawn icons under
many different names** across several sessions: each individual write looked innocent. When you enter a
feature that ALREADY EXISTS, run an adherence sweep before you start: count the nodes with an icon
name (`icon-*` or its equivalent in the file's language, for example `icone-*` in Portuguese;
`spinner-*`; a glyph in a TEXT node) that are NOT a library instance. If the number is not zero,
that is debt to report at the start, not to discover when the designer points at it. The scoped sweep closes the work: report remaining debt in the approved feature, without silently expanding a local fix to the whole file.

### Check 5: applicable canon

Use `figma-canon` to select the references required by this operation and current knowledge. Reuse valid context, and load the specific API/layout/data/recovery section when needed. Do not load three complete manuals for every tiny write.

### Check 6: State coverage planned (if creating a screen)

- For new screen creation: which states are required (for example Empty / Loading / Error /
  Success / Edge; the decision table gives the full set per screen class)?
- Use the decision table in [`figma-canon/references/state-coverage.md`](../../figma-canon/references/state-coverage.md).
- Derive routine states from the applicable product contract; ask only when a real product choice remains unresolved. Explicit out-of-scope states are reported, not invented.
