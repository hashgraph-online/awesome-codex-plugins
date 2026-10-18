# figma_execute atomicity

Load before any write. Write-call discipline for `figma_execute` (figma-console MCP, through its Desktop Bridge plugin): atomicity, output cap, ID return, async discipline and multi-call workflow patterns.

## Single-call discipline

- Each call = one atomic transaction *in intent*.
- On error, the call reports failure. Read the error.
- **EMPIRICAL CAVEAT: atomicity is NOT guaranteed (field note, 2026-06, a design system file).** A script that throws mid-execution CAN leave the canvas mutations it already applied before the throw point. Verified: a `txt()` helper that set `node.fontName = '<string placeholder>'` threw `"Expected object, received string"`, yet the frames and text it had already `createFrame()`+`appendChild()`'d before that line PERSISTED on the canvas (a half-built section). The rollback the docs imply did not happen. **So: after ANY failed `figma_execute`, do NOT just fix and retry. First scan the target parent for orphan or partial nodes from the aborted run and remove them, or the retry stacks a duplicate on top of the partial.** Treat "atomic" as best-effort, not a transaction guarantee.
- **A TIMEOUT also commits, and the next read LIES (field note, 2026-08).** The caveat above covers `throw`; hitting the 30 s timeout is worse. A `figma_execute` that returned `Execution timed out after 30000ms` **had created the entire SECTION with two clones inside**, and `page.children` read in the immediately following call came back `[]`. The agent trusted the `[]`, rebuilt from scratch, and ended up with a duplicate ghost section underneath the real one. It only surfaced about 40 calls later, in a contrast audit, because the old name showed up as the "background" of a text node.
  **Rule:** after a timeout, do NOT accept the first read as truth. Let one more call go by, then re-read and compare by `id` (not by name, which repeats). Before deleting any ghost, prove that it is a subset of the good one (`children.length` + names), never by position.
- A timeout is a sign that the call is too big: cloning one device-size frame (390x844) alone already gets close to the ceiling. Give each clone its own call. (30000 ms is the maximum timeout `figma_execute` accepts; the default is 5000 ms.)
- Output cap: about 20 KB. Exceed it and the call fails silently or truncates. The same number is the documented per-call output limit of `use_figma` (official Figma MCP server) as of 2026-10.
- Operations per call: target at most 10 logical operations (create-node + set-props + parent = 1 logical op).

## Output protocol

- Use `return` for output, NOT `console.log` (silently dropped).
- Return value must be JSON-serializable (no functions, no symbols, no circular refs).
- Include actionable IDs:

```javascript
return {
  createdNodeIds: ['123:456', '123:789'],
  variableIds: ['VariableID:abc/xyz'],
  collectionIds: ['VariableCollectionId:def'],
  framesByName: { 'Header': '123:456', 'Body': '123:789' },
  // ... any custom keys callers need
};
```

- Keep the payload under the output cap (about 20 KB, see Single-call discipline above). The optional precheck hook (`hooks/figma-canon-precheck.py` at the root of this repository, opt-in, see the repository README) warns when the script itself is over 20,000 characters and points here: split the work across several calls.

## Async discipline

Every async call MUST be awaited:

- `await figma.loadFontAsync({family, style})`
- `await figma.setCurrentPageAsync(page)`
- `await figma.importComponentByKeyAsync(key)`
- `await node.exportAsync({format})`
- `await figma.getNodeByIdAsync(id)` (newer API)
- `await figma.variables.getVariableByIdAsync(id)`

Missing await means JS proceeds before the resource is ready, which leaves silent broken state.

Pattern to scan for: `\b(loadFontAsync|setCurrentPageAsync|importComponentByKeyAsync|exportAsync)\(` NOT preceded by `await\s+`. The optional precheck hook flags the missing `await` on the first three; check `exportAsync` yourself.

## Multi-call workflow

JavaScript variables do NOT persist across `figma_execute` calls. Each call is a fresh JS context.

**Pattern: pass IDs as string literals between calls.**

Call 1: create skeleton, return IDs.

```javascript
const frame = figma.createFrame();
frame.name = "screen-root";
figma.currentPage.appendChild(frame);
return { rootId: frame.id };
```

Call 2: reference the ID literally.

```javascript
const root = await figma.getNodeByIdAsync('123:456'); // literal string from Call 1's return
const header = figma.createFrame();
header.name = "header";
root.appendChild(header);
return { headerId: header.id };
```

The getter is the async one because the document loads in dynamic-page mode (see Async getters for Variables: dynamic-page mode in `references/plugin-api-core.md`, and guard 4 below).

## Top-down-with-placeholders

For complex screens, multi-call build:

1. Call 1: create root + N placeholder section frames (named with `placeholder=true` shared plugin data).
2. Call 2..N: fill each section, replacing the placeholder.
3. Final call: take a screenshot (`figma_capture_screenshot` or `figma_take_screenshot`), verify visual integrity.

## Operation budget

| Pattern | Cost | Use when |
| --- | --- | --- |
| 1 node create + 5 props + parent | 1 op | Standard |
| 10 nodes batch-create + parent each | 10 ops | At cap; consider split |
| 50-node tree in one call | 50 ops | **DO NOT**: split across calls |
| Iterate findAll + mutate | Variable | Bound by findAll size |

## Error response protocol

1. Read the full error message.
2. Identify the failure point (line / API call).
3. **Scan the target parent for orphan or partial nodes the aborted run left behind** (see EMPIRICAL CAVEAT above: atomicity is best-effort, not guaranteed). Remove them before retrying, else the retry duplicates on top of the partial.
4. Check against `references/plugin-api-anomalies.md`.
5. Fix the JS at source.
6. Retry, but ONLY if the fix addresses the actual error. **Do not retry blindly.**
7. If the same error recurs after the fix: STOP, ask the user.

## Mandatory guards in batch writes

Field note, 2026-08: 4 crashes with partial commit on one project, all from the same defect (a batch mutation loop that ran without the guards below).

Every batch mutation loop carries THESE guards from the FIRST write, not after the crash:

1. **Type guard before `.findAll` / `.children`**: a leaf node (TEXT, VECTOR, RECTANGLE) has no `findAll`. An id taken from someone else's finding (an audit report, another agent's list) can point at the TEXT node instead of its row, and `.findAll` then fails with "not a function".
2. **Parent climb with a CEILING**: `while (p && p.id !== frame.id && p.type !== 'SECTION' && p.type !== 'PAGE')`. Without a ceiling the climb goes past the page and reaches the DocumentNode, which has no `findAll`.
3. **Instance sublayer: position is NOT an override** (writing `x` on an instance sublayer fails with an error that names `set_x: relative-transform`). Allowed: characters, fills, visible, resize, componentProperties. Caveat on `resize`: on a sublayer it can silently not apply, see Instance sublayers: width and constraints also belong to the master in `references/plugin-api-anomalies.md`. To move an element of an instance, hide the original (`visible=false`) and clone a substitute outside the instance.
4. **Sync getters are forbidden in dynamic-page mode**: `mainComponent` becomes `getMainComponentAsync()` (same family as `getVariableById`).
5. **`createFrame()` is born 100x100 FIXED**: a 120 px child is CLIPPED silently. Set `layoutSizingVertical/Horizontal` (or resize) BEFORE declaring it done, and check the `height` you read back.
6. A crash in the middle of a loop means the earlier items are COMMITTED: always re-run idempotently (guard `if (already in the target state) skip`), never re-apply blind.
7. **Target by exact NAME, never by a generic structural signature**: a signature such as "the frame that contains an avatar and name row" matched a LIST CARD instead of the target dialog and planted a button on 5 wrong screens (revert + re-apply). If the target container has a name (for example `edit-dialog`), aim at the name. Use a structural signature only as a fallback, with a check of the expected w/h before mutating.

## Reparenting between calls

- `appendChild` between calls CAN fail silently if the source node was created in a previous call.
- Build the structure in the call that creates it.
- Do not create section frames as children of the page and then try to move them under a wrapper in a subsequent call.
- See `references/plugin-api-anomalies.md`: SECTION.appendChild reflow + general reparenting risks.

## Anti-patterns

Each line is something NOT to do, followed by the fix or the reason.

- Wrapping in an `async function() { ... }()` IIFE: the tool auto-wraps.
- Using `figma.closePlugin()`: not supported.
- Calling `figma.notify()`: not implemented (observed in `use_figma`, see `references/plugin-api-data.md`). Never use it for output on any path; use `return`.
- Using `setPluginData`: use `setSharedPluginData` instead.
- Mutating `node.fills` in place: clone-mutate-reassign.
- Setting `figma.currentPage = page`: use the async setter.
- Async fire-and-forget without await.
- Building one giant tree in a single call (hits the output cap).

## What good looks like

- Self-contained: all inputs are passed as string literals or fetched fresh in the call
- Defensive: every async awaited, every mutation safe-clone-reassign
- Reportable: returns structured IDs for the next call
- Recoverable: on error, diagnose and retry, but first scan for partial nodes the aborted run may have left (atomicity is best-effort; see EMPIRICAL CAVEAT under Single-call discipline)
