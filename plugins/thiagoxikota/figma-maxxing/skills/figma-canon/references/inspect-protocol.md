# Inspect-before-edit protocol

Load when inspecting or orienting on a file. Inspection sequence to run before any Figma write, in order of cost: `whoami` (seat check), `get_metadata`, `get_variable_defs`, `search_design_system`, `get_code_connect_map`, `get_design_context`, `get_screenshot`. Inspection is mandatory before a write. How far down the sequence you go depends on the write (see "Inspection gate" at the end). Includes the tool surface table of the official Figma MCP server, token-cost calibration and bypass paths.

## Which server these tools belong to

Every tool in the sequence belongs to the official Figma MCP server (remote, OAuth). If only the figma-console MCP server is connected, read the same kind of data with its own tools. These are alternatives, not one-to-one equivalents: the output shapes differ.

| Step | Official Figma MCP tool | figma-console alternative |
| --- | --- | --- |
| 1 | `get_metadata` | `figma_get_file_data`, `figma_get_file_for_plugin`, `figma_get_selection` (for the active selection) |
| 2 | `get_variable_defs` | `figma_get_variables`, `figma_get_token_values`, `figma_get_styles`, `figma_get_text_styles` |
| 3 | `search_design_system` | `figma_search_components`, `figma_get_library_components`, `figma_get_design_system_summary` |
| 6 | `get_screenshot` | `figma_capture_screenshot` |

Rows 1 to 3 repeat the table of the `figma-preflight` skill (section "Which server each tool belongs to"). This canon lists no figma-console alternative for steps 0, 4 and 5.

## Tool surface (official Figma MCP server)

The tools below are the list as of 2026-05. Verify it against the tool list your client shows. Memorize which are READ-only and which are WRITE-capable: the wrong tool on the wrong server is a silent failure.

Tool names are written as base names. The prefix depends on the client.

| Tool | Read/Write | Server | Notes |
| --- | --- | --- | --- |
| `whoami` | R | Remote | Seat + plan check. Step 0. |
| `get_metadata` | R | Both | Sparse XML. Step 1 always. |
| `get_design_context` | R | Both | Heavy, 25k token cap. |
| `get_screenshot` | R | Both | Rate-limited; plugin export bypass. |
| `get_variable_defs` | R | Both | Variables + styles in scope. |
| `get_libraries` | R | Remote | List subscribed libraries. Easy to overlook. |
| `get_code_connect_map` | R | Both | nodeId to code mapping. |
| `get_code_connect_suggestions` | R | Both | Probable mappings. |
| `get_context_for_code_connect` | R | Both | Richer Code Connect read. Easy to overlook. |
| `search_design_system` | R | Remote | Component/var query. |
| `get_figjam` | R | Remote | FigJam board read. |
| `use_figma` | **W** | Remote | Plugin JS bridge. Full seat required. |
| `create_new_file` | **W** | Remote | New file. |
| `generate_figma_design` | **W** | Remote | Code to canvas. |
| `generate_diagram` | **W** | Remote | Mermaid to FigJam. |
| `upload_assets` | **W** | Remote | **Image bytes upload. Easy to overlook: a summary that says this server does not support images has missed this tool.** |
| `add_code_connect_map` | **W** | Remote | Add mapping. |
| `send_code_connect_mappings` | **W** | Remote | Bulk publish mappings. |
| `create_design_system_rules` | **W** | Remote | Generates rules file. Verify before relying on. |

**Server selection:**

- Desktop (`127.0.0.1:3845`): read-only, but auto-detects the current Figma selection (no URL parse needed).
- Remote (`mcp.figma.com`): full write surface, but **link-based only** (no auto-selection, you must pass fileKey + node-id explicitly).
- `figma-console` MCP (a separate server, not in this table): the Desktop Bridge plugin path, used for write operations (`figma_execute`). Different transport, different constraints. See the section "Research vs empirical evidence: log contradictions" in `references/plugin-api-anomalies.md`.

**Server-column caveat:** the `Server` column reflects Figma's docs as of 2026-05-12. The `Both` claims for the seven read tools (`get_metadata`, `get_design_context`, `get_screenshot`, `get_variable_defs`, `get_code_connect_map`, `get_code_connect_suggestions`, `get_context_for_code_connect`) are doc-stated, not all empirically dual-server-tested in this canon. The FigJam-specific tools (`get_figjam`, `generate_diagram`) and the full Remote-only write surface have not been re-tested on the Desktop server in this canon: assume Remote-only until a Desktop test contradicts it.

## The 6-step sequence

Six steps, 1 to 6, plus a step 0 that applies only to a write session. Run in this order. Stop at the level needed. Do not escalate unless required.

### Step 0: whoami (free, before any write session)

- Confirms the current user, the plan (Starter / Pro / Org / Enterprise) and the Full/Dev seat status.
- Run ONCE per session before any `use_figma` write call.
- Required for: catching "Dev seat tries to write to non-draft" failures EARLY (before the operation atomically rolls back).
- Skip when: pure-read session (audit, orient, extract).

### Step 1: get_metadata (cheap, always)

- Returns sparse XML: node IDs, names, types, positions, sizes.
- Use FIRST on any large selection or unfamiliar file.
- Token cost: ~500-2000 for a typical page.
- Required for: target node-id confirmation, structure understanding.

### Step 2: get_variable_defs (medium, before any styled write)

- Returns the variables + styles used in the selection.
- Use BEFORE applying any fill, stroke, spacing, typography, radius.
- Token cost: ~1000-5000 for a published library scope.
- Required for: token-bound writes, semantic color picks.
- Caveat: `getLocalVariableCollectionsAsync()` in `figma_execute` does NOT see published library variables: use this MCP tool OR `search_design_system` with a variable filter.

### Step 3: search_design_system (medium, before any UI creation)

- Searches the subscribed libraries for components, variables and styles matching a query.
- **REMOTE MCP only**: the desktop server does not support it.
- Use BEFORE creating new UI elements.
- Token cost: ~500-2000 per query.
- Required for: component reuse decisions (prevents recreation).

### Step 4: get_code_connect_map (light, when Code Connect configured)

- Returns a `{nodeId: { codeConnectSrc, codeConnectName }}` mapping.
- Use when generating code OR before creating new components that might already exist in code.
- Token cost: ~200-1000.
- Required for: code-component-aware workflows (for example Figma's own Code Connect skill, if your agent has it installed, or a React codebase with Code Connect configured).
- Not applicable to a project that has no code yet.

### Step 5: get_design_context (heavy, only on specific nodes)

- Returns the full React+Tailwind code representation + screenshot + tokens for a node.
- **Hits the 25k token limit on complex pages.** Use ONLY on specific child nodes after `get_metadata` identified them.
- Token cost: 2000-25000+.
- Required for: deep code generation, detailed token extraction.
- Override env: `MAX_MCP_OUTPUT_TOKENS` (a Claude Code environment variable). Set it to a value above 25000 to raise the cap: 25000 is the limit described above.

### Step 6: get_screenshot (light, for visual confirmation)

- Returns a PNG of the node.
- Use when text-based inspection is ambiguous OR for a visual sanity check after writes.
- Token cost: ~500 + image.
- Required for: visual confirmation before claiming done.
- Rate limit: hits 429 after ~6 batched calls (~30+ min lockout). See `references/rate-limit-recovery.md`.

## Token budget calibration

| Operation | Use when | Skip when |
| --- | --- | --- |
| `get_metadata` | Every new file/page | Already inspected this session |
| `get_variable_defs` | Any styled write | Read-only context extraction |
| `search_design_system` | Creating new UI | Editing existing instances |
| `get_code_connect_map` | Code generation OR new components | Pure design work in a code-less project |
| `get_design_context` | Deep dive on a specific node | Quick orientation (use metadata) |
| `get_screenshot` | Final QA OR ambiguous text | Mid-edit (waste of tokens + rate-limit risk) |

## When to wrap inspection in figma-orient

- New file you have not seen this session: run the `figma-orient` skill (it maps structure, variables and anchor screenshots through the Bridge and saves the map to the project's `figma-map.md`).
- Familiar file, specific node: call the individual MCP tools directly.
- Project that already has a `figma-map.md`: load it first. Orient again only if the file has shifted.

## Bypass paths

### REST 429: plugin export

When `get_screenshot` hits the rate limit, switch to the plugin runtime.

For a visual check, call `figma_capture_screenshot` (figma-console MCP server). It always uses the plugin runtime and needs the Bridge.

When you need the bytes themselves, export inside `figma_execute` and return base64:

```javascript
// In figma_execute (NOT a separate MCP call, runs in plugin context)
const node = await figma.getNodeByIdAsync('NODE_ID');
if (!node) return { error: 'node not found' };
const bytes = await node.exportAsync({format: "PNG"});
return figma.base64Encode(bytes);
```

Plugin export works during a REST lockout. See `references/rate-limit-recovery.md` for the size of the return and for the export-to-disk route.

### Large file token overflow

- `get_design_context` on a full page: likely 25k token overflow.
- Pattern: `get_metadata` first, identify the specific child node-id, then `get_design_context` only on that child.

## Read-only enough? Don't write

If inspection answers the user's question without a write, STOP there. Do not fall through to `figma_execute` just because you can.

- "What components exist?": `search_design_system` + report. No write.
- "What tokens?": `get_variable_defs` + report. No write.
- "Describe this screen": `get_metadata` + `get_screenshot` + report. No write.
- "Audit this file": all read steps + an ad hoc cleanup punch list. Write only on per-item approval.

## Inspection gate (figma-preflight skill)

The `figma-preflight` skill enforces this protocol before any `figma_execute` write. It runs 8 checks (Check 0 to Check 7), and the full text of each one lives in that skill. The six that come from this protocol:

1. Target node-id confirmed
2. `get_metadata` run this session
3. `get_variable_defs` run if the write touches styled properties
4. `search_design_system` run if the write creates new UI
5. Relevant canon references loaded
6. State coverage planned (if creating a screen)

The other two: Check 0 (live Bridge connection, attested by `figma_get_status`) runs before these six, and Check 7 (file lock claimed) runs after them.

Fails closed (blocks the write) until all checks pass OR the user explicitly overrides.
