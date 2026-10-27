---
name: google-sheets-live-guard
description: Use together with Google Sheets work when editing an existing live spreadsheet, especially client-facing reports, row or tab insertion, tab moves, formula repairs, manually edited sheets, or any write that could duplicate rows/tabs or overwrite manual values.
---

# Google Sheets Live Guard

Use this skill as a local safety overlay whenever a task edits an existing Google Sheet. It supplements whatever Google Sheets tool or skill is installed (an API client, an MCP server or a separate `google-sheets` skill — none ships with this plugin). If one is installed, read its instructions first; if not, apply these guards to direct Sheets API calls.

## Live State Before Writes

- Treat old spreadsheet snapshots, prior row numbers, and earlier review notes as stale once the user, another agent, or the sheet itself may have changed.
- Immediately before a write, re-read spreadsheet metadata, target tabs, `sheetId` values, row labels, formulas, formats, validation, and nearby protected/manual cells that could be affected.
- For manually edited or cleaned sheets, prefer a rich read of current cells over displayed values only. Include formulas, effective values, user-entered values, formatting, validation, and chart or tab metadata when those surfaces affect the edit.
- A successful bounded CellData read can omit `rowData` or trailing `values` when every requested field is empty. Confirm the returned sheet and grid coordinates, then normalize omitted cells to empty objects; do not index `rowData[0]` unconditionally or mistake this valid empty-range response for an API failure. Non-success responses still require separate error handling.

## Idempotent Structure Changes

- Before inserting rows, creating tabs, duplicating report tabs, or moving tabs, check whether the requested row, section, or tab already exists in the live sheet.
- If the desired row/tab already exists, switch to verify-only. Do not insert a duplicate just because the original plan expected it to be absent.
- For tab moves, update only the target sheet properties, use the exact current `sheetId`, keep the field mask narrow, and re-read tab order afterward.
- After `insertDimension`, tab duplication, row movement, or any structural update, discard cached row numbers. Rebuild bindings from current labels, headers, formulas, and metadata before validating the result.

## Client-Facing Report Writes

After structural edits, also reconcile source coordinates inside existing notes
and explanations. Distinguish a historical snapshot locator, tied to its date
or digest, from a live cell address. Label the former as historical; rebind the
latter from current semantic headers. Verify the affected notes as well as cell
values. This does not require adding notes or methodology panels that the user
did not request.

- Before bulk formula writes, inspect the existing spreadsheet locale and a working formula from that book. Test one representative formula and read its effective result; Russian-locale books can require semicolon argument separators even when using English function names through the API. Never infer correctness from a successful write response.
- Before merging header/title cells, validate that no merge crosses a frozen-row or frozen-column boundary. For full-width merged titles, either leave columns unfrozen or place merges entirely on one side of the boundary; preserve the user's existing freeze settings on old tabs.

- Before writing a client-visible report, produce a compact pre-write contract that names exact tabs, ranges, cells, data sources, formulas, excluded cells, manual values to preserve, and unresolved assumptions.
- Get explicit permission for the live write when the change affects a shared/client-facing report or replaces human-entered values.
- Do not fill future plan cells from rough proxies when no approved plan source exists.
- If a source system lacks a metric such as spend for a channel, preserve the current/manual value or mark it unresolved; do not overwrite it with zero solely because the API returned no field.
- When source exports, report formulas, and visible totals disagree, bind each client-facing value to the raw source and channel scope before writing. Do not reconstruct a missing channel metric from an old formula, all-channel total, or plausible CRM-status logic and present it as source truth. Preserve the existing value or mark it unresolved until the raw source supports the exact metric and channel.
- If a client report source export is large enough that broad shell output, search output, or a worksheet/API dump becomes truncated, do not use that truncated view as proof for a cell value. Re-read the source through a bounded structured path that selects the exact file, tab, rows, fields, and channel/date scope needed for the write; only source values confirmed through that bounded read may enter the pre-write contract.
- If the user explicitly excludes a named source, campaign, or channel from a
  client-facing report, carry that exclusion through every dependent value:
  spend, leads, sales, revenue, formulas, subtotals, totals, charts, and
  writeback. Keep the excluded channel visible only as a separate excluded
  source when useful; do not let formulas silently add it back because it exists
  in the source export.
- When a metric is unresolved or intentionally excluded, preserve, blank, or
  guard dependent formula cells that would otherwise present a partial total as
  complete. Do not leave a subtotal, total, or percentage formula looking final
  while one of its required channel inputs is unknown or excluded.
- When manager-level counts are challenged, verify the row-level source history before confirming or rewriting the report. Distinguish current responsible manager, first responsible manager, transfer history, CRM repeat status, and source-system "new" status; state which layer the sheet currently counts, and do not relabel a transferred or repeat lead as a new manager lead without source proof.


- For copied, duplicated, or template-derived report tabs, exact visible value equality after write is not enough. Re-read and compare formulas, displayed values, user-entered values, formatting-sensitive cells, protected/manual cells, and the expected blank tail or hidden old rows. Old formulas or copied artifacts that survive under the new values can invalidate the report even when the target range values match.
- If a source-method repair changes aggregate totals, identity reconstruction, deleted-deal handling, or manager attribution, do not patch only the row the user challenged. Rerun the whole dependent report tab or dependent table range from the corrected source method, then verify totals, subtotals, formulas, and downstream percentages together.
- When the user names an existing tab, previous report, or template as the correct example, preserve that template's visible structure: block order, spacing, merges, row heights, labels, formulas, and intentionally absent explanatory sections. Do not add "how to read" blocks, method comments, appendices, or extra explanatory panels unless the user explicitly requested them.
- Verify after the write by current row labels and formulas, not by stale coordinates captured before insertion or cleanup.

## Visual And Chart Changes

- Treat charts, visual blocks, styled bands, title rows, images, merged cells, row heights, and report-panel formatting as user-visible changes, not as ordinary cell writes.
- Before adding or moving a visual layer in an existing client-facing workbook, verify the exact placement surface, existing style, chart/table overlap risk, and rollback path. Prefer a separate tab or an explicitly approved area when the visual layer is not already part of the sheet design.
- After the write, perform a visual/readability check in addition to API readback: foreground/background contrast, chart placement, text legibility, row height, merged-cell effects, and whether the result follows the workbook's existing style. If the visual layer makes the sheet harder to read, roll back that layer without disturbing the verified data layer.

## Completion

For native Google Sheets report verification, do not treat a narrow cell-value
read as proof of workbook-level state when the task depends on native table
properties, tab color, banding, freeze state, gridline visibility, row or
column dimensions, or `rowProperties`/`columnProperties`. If the current read
surface omits those properties, use an alternate current metadata or connector
readback that exposes them, or report the missing surface as a blocker; do not
close the task from value equality alone.

Before reporting completion, re-read the edited ranges and adjacent impacted rows/tabs, confirm no duplicate rows/tabs were created, confirm formulas and manual exclusions survived, and state any cells intentionally left unchanged because their source was not confirmed.
