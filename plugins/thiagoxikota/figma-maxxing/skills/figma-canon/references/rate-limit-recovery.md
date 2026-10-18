# Rate-limit recovery

REST 429 lockout recovery via the plugin export bypass, token-limit overrides and the `get_metadata`-first strategy. Load on a tooling failure or before batch read-heavy operations.

Tools named here: `get_screenshot`, `get_metadata` and `get_design_context` belong to the official Figma MCP server. `figma_execute` and `figma_get_file_data` belong to the figma-console MCP server.

## REST 429 lockout

**Trigger:** ~6 batched `get_screenshot` calls in quick succession.

**Lockout duration:** ~30+ minutes.

**Symptom:** subsequent MCP calls return 429 or time out silently.

## Bypass: plugin export

Plugin export works during a REST lockout.

For a visual check, call `figma_capture_screenshot` (figma-console MCP server) first. It always uses the plugin runtime, never REST, and needs the Bridge. It captures the active file only (see `references/field-notes.md`).

When you need the bytes themselves, export one node per `figma_execute` call and return base64:

```javascript
// In figma_execute (runs in plugin context)
const node = await figma.getNodeByIdAsync('NODE_ID');
if (!node) return { error: 'node not found' };
const bytes = await node.exportAsync({format: "PNG"});
return figma.base64Encode(bytes);
```

- `exportAsync` runs in the plugin context, NOT through the REST API
- Works during a 429 lockout
- `exportAsync` returns a Uint8Array of PNG bytes. Do not return it raw: the return value of `figma_execute` must be JSON-serializable (see "Output protocol" in `references/figma-execute-atomicity.md`). Encode it with `figma.base64Encode`, then decode the string to a file on disk to look at it.
- Use `figma.getNodeByIdAsync`, not the sync `figma.getNodeById`: the document loads in dynamic-page mode, where sync getters throw (see `references/plugin-api-core.md`). Null-guard the result.
- Size of the return: `references/figma-execute-atomicity.md` gives an output cap of about 20 KB per call, and a 2x PNG returned as base64 has measured 628 KB through a direct stdio client (`references/field-notes.md`). Both observations stand. Keep to one node per call, and for many or large nodes use the export-to-disk pipeline in `references/plugin-api-anomalies.md` (section "Plugin export as REST 429 bypass"), which writes the files to disk instead of returning them.
- Slightly slower than `get_screenshot` but functional
- Field note, 2026-05

## Token limit handling

By default `get_design_context` returns up to ~25k tokens. Large pages overflow.

### Pattern 1: get_metadata first

```
1. get_metadata on page  -> ~500-2000 tokens, lists children
2. identify specific child node-id from metadata
3. get_design_context on that specific child only
```

### Pattern 2: env override

Set `MAX_MCP_OUTPUT_TOKENS` to a value above 25000 to raise the cap (25000 is the ~25k limit described above, so setting it to 25000 changes nothing). This is a Claude Code environment variable, set before the session starts. Trade-off: longer responses, higher cost.

### Pattern 3: structural reads

Prefer `figma_get_file_data` or `figma_execute` for bulk extraction over `get_design_context`. Structural reads return data, not React+Tailwind code, so they are more compact.

## Rate limits per plan

Limits depend on the seat and on the plan where the file lives. The numbers below are the ones this canon was calibrated on: verify them against the current docs at https://developers.figma.com/docs/rest-api/rate-limits/ .

| Plan | Daily | Per-minute |
| --- | --- | --- |
| Starter | Small monthly allowance (see the docs) | 10 |
| Pro | 200 | 15 |
| Organization | 200 | 20 |
| Enterprise | 600 | 20 |

## Tool-call budget strategies

### Batch reads when possible

```
WRONG: get_design_context on every frame in a list
RIGHT: get_metadata on parent, then targeted get_design_context only where needed
```

### Cache between operations

If you already extracted the variables this session, do not re-extract them for the next write. The `figma-orient` skill caches its output to the project's `figma-map.md`.

### Plugin export instead of REST screenshot

Specifically for batch screenshot needs:

```javascript
const nodeIds = ['1:2', '1:3', '1:4'];  // from get_metadata
const nodes = await Promise.all(nodeIds.map(id => figma.getNodeByIdAsync(id)));
const missing = nodeIds.filter((id, i) => !nodes[i]);
if (missing.length) return { error: 'nodes not found', missing };
const exports = await Promise.all(
  nodes.map(n => n.exportAsync({format: "PNG"}).then(b => figma.base64Encode(b)))
);
return { exports };
```

One `figma_execute` call, many node exports, NO REST 429 risk. Watch the size of the return (see "Bypass: plugin export" above): a batch of base64 PNGs passes the output cap of about 20 KB quickly. Batch only small nodes. For more or larger nodes, use one node per call or the export-to-disk pipeline in `references/plugin-api-anomalies.md`.

## When to wait vs bypass

| Situation | Action |
| --- | --- |
| Hit 429, work is read-only ad hoc | Wait ~30 min |
| Hit 429, urgent batch screenshot needed | Bypass via plugin export |
| Approaching the daily limit (180/200 Pro) | Switch to plugin export for non-urgent reads |
| Limit exceeded, no progress possible | Pause, escalate to the user (upgrade plan?) |

## Screenshot count threshold

More than 3 `get_screenshot` calls in a session means you are likely heading toward a 429. Switch to the plugin export pattern.

## Workflow when hitting limits mid-session

1. Detect the 429 in the MCP response
2. Switch the read strategy: `get_screenshot` to `figma_capture_screenshot` or plugin `exportAsync` (see "Bypass: plugin export")
3. Continue the work
4. Note in the handoff that some screenshots used plugin export (no quality difference, but useful for debugging if the visuals differ)
