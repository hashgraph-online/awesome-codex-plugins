# Test Plan -- /quiver:design

**Trigger:** `/quiver:design`, `/quiver:design 4029:12345`, `/quiver:design --auto`, `/quiver:design`

**Setup:**
- figma-bridge MCP server configured, plugin running inside a Figma file.
- A frame selected in Figma that sits inside a parent containing top and bottom chrome.
- A project with at least one token file.

**Expected behavior:**
1. Both shell blocks exit 0 in a git repo and in a non-git directory.
2. With the MCP absent, Step 1 prints the two-part install block and stops -- no partial plan is written.
3. With the MCP present but no file connected, `list_files` returns `[]` and Step 2 prints the plugin instruction and stops.
4. With more than one file connected, Step 2 asks which file via `AskUserQuestion` and passes `fileKey` to every later call.
5. A node ID passed as `4029-12345` is normalized to `4029:12345` before any tool call.
6. With nothing selected and no ID argument, Step 3 prints the selection instruction and stops.
7. Step 4 writes reference PNGs into `.claude/plans/assets/<slug>/` at scale 2, plus one file per icon and image leaf node (`.svg` for vectors, `.png` at scale 3 otherwise).
8. Re-running `/quiver:design` against a node whose asset already exists does not throw, and does not delete the existing file -- the new export takes a suffixed name and the previous plan's references still resolve.
9. A `save_screenshots` sandbox rejection prints the reported sandbox root and writes there, recording it as `screenshot_dir`.
10. Step 5 emits an Anchor line for every node, and a Reconciliation line for every node whose anchor references excluded chrome.
11. Step 6 resolves `codegraph_available` from a Glob on `.codegraph/*` and dispatches exactly one `quiver:code-navigator` agent, with literals in the prompt, and waits without polling.
12. Step 7 auto-maps every value-matched variable and asks exactly one approval question regardless of how many rows are unmapped.
13. Step 7's table carries a `Mode` column with one row per mode for any multi-mode variable, and alias values are resolved before matching.
14. Step 8 asks commit strategy and the after-task check in one grouped `AskUserQuestion`, each question carrying its own header and each option a one-line description.
14b. Step 8 asks the scope question only when Step 3 resolved exactly one top-level node with more than one extracted child, `$ARGUMENTS` carries no description beyond flags and node IDs, and no existing plan matched the slug. A described selection reaches no scope question, and Question 3 and Question 4 never appear in the same call.
14c. Answering "Only {child}" writes `Scope: reference only -- not built by this plan` on every node spec outside the chosen child's subtree, gives those nodes no task, and names the scope in the `### Goal` section. The chosen child and its own descendants stay in scope. Answering "The whole {node}" writes no `Scope:` line anywhere.
15. Step 8 finds an existing plan for the same slug, summarizes the differences, and carries the overwrite question in that same call; Step 9 writes on that answer without asking again.
16. Step 9 writes the plan with `design_source`, `figma_file_key`, `figma_node_ids`, `figma_frame_size`, `screenshot_dir`, `commit_strategy`, and `verify_gate` in frontmatter.
16b. Extracting a component that is not the whole screen still records the enclosing screen frame in `figma_frame_size`, not the component's own box.
17. Every applicable node spec carries `Fit:`, `Content:`, and `Route:` lines.
18. The plan carries an `### Assets` section naming every exported file.
19. Step 10 reads the plan back, verifies the assets exist, dispatches `quiver:plan-reviewer` exactly once, applies its findings, and offers the three-button handoff via `AskUserQuestion`.
20. `/quiver:design --auto` still asks every plan-time question -- file, nodes, unmapped tokens, build preferences, overwrite -- and the `--auto` token never reaches Step 3's node-ID resolution.
21. `/quiver:design --auto` skips Step 10's handoff question entirely, prints `> Building.`, and invokes `design-build` with the plan path and `--auto` in the same run.
22. Picking "Build it now" in the interactive handoff invokes `design-build` without `--auto`, so the build keeps its own prompts.
23. `/quiver:design --no-commit` asks Step 8's Question 2 only, writes `commit_strategy: none`, and says so once.
24. `/quiver:design --auto --no-commit` forwards both flags to `design-build`; `/quiver:design --auto` forwards only `--auto`.
25. `--no-commit` works without `--auto`, and `--auto` works without `--no-commit`.

**Verification checklist:**
- [ ] `/quiver:design` and `/quiver:design` both appear in the slash menu after plugin reload.
- [ ] Both `!` blocks exit 0 with `NO_GIT` output in a non-git directory.
- [ ] No figma-bridge write tool is ever called.
- [ ] The saved plan contains no raw `{...}` placeholder text.
- [ ] Every node spec block carries literal numbers, not references to Figma.
- [ ] Every path in the `### Assets` table exists on disk.
- [ ] All four contract frontmatter fields are present: `screenshot_dir`, `commit_strategy`, `verify_gate`, `figma_frame_size`.
- [ ] Thirty unmapped variables produce exactly one approval question.
- [ ] No node spec writes a `fill` axis as a literal width.
- [ ] The frontmatter fence appears in this file and in no other skill.
- [ ] `quiver:plan-reviewer` runs once, before the handoff question, never after.
- [ ] `--auto` is stripped before Step 3 resolves a node ID.
- [ ] In auto mode, Step 8 is the last `AskUserQuestion` the run reaches, and its preamble says what is being approved.
- [ ] The auto handoff passes the plan path and `--auto` to `design-build`; the interactive one passes the path only.
- [ ] `--no-commit` is stripped before Step 3 resolves a node ID, skips Step 8 Question 1, and lands as `commit_strategy: none` in the plan.
- [ ] Unmapped Figma variables produce an `AskUserQuestion`, never a silent raw value.
- [ ] Anchor lines name the excluded chrome and its measured size.
- [ ] `when-to-use:` is a single-line double-quoted string.
- [ ] No `CLAUDE_PLUGIN_ROOT` reference anywhere in this file.
- [ ] No Unicode characters or emoji in this file.
- [ ] No `$()`, variable assignment, or `if/else` inside any `!` block.

**Known gotchas:**
- `--auto` removes the handoff prompt, not the Q&A. A user expecting a fully silent run still answers Steps 2, 3, 7, 8, and 9 -- those answers are what the plan is made of.
- Figma share URLs use a hyphen in node IDs (`4029-12345`); the bridge tool schema rejects hyphens. Normalization in Step 3 is mandatory, not optional.
- When more than one Figma file is connected, every bridge tool requires `fileKey`. Omitting it fails at call time, not at plan time.
- `get_design_context` returns a summarized tree. It is not a substitute for `get_node` -- the summary drops most visual properties.
- Instance-child node IDs use the `I12740:17806;12740:17793` form. Passing only the leading segment returns the wrong node.
- `.claude/plans/assets/` holds binary PNGs. If the project gitignores `.claude/`, the screenshots are local-only, which is intended.
- The plugin must stay running in Figma for the whole extraction. Closing it mid-run drops the WebSocket and later calls fail.
- `save_screenshots` writes with flag `wx`. It throws on an existing file rather than overwriting, which is why a second run against the same node fails unless the directory is listed first. Suffixing rather than deleting matters because Step 4 runs before Step 8's overwrite question -- deleting would strip an existing plan's reference images no matter which way the user answered it.
- `save_screenshots` sandboxes `outputPath` to the MCP server's working directory, which is not always the project root. A rejection is a path problem, not a permissions problem.
- `save_screenshots` infers the format from the `outputPath` extension. Passing a `format` that disagrees with the extension throws, and `scale` is ignored entirely for SVG and PDF.
- `get_screenshot` returns base64 inside a JSON text blob rather than an inline image, so nothing in this skill can see it. Visual work goes through `save_screenshots` and a subsequent Read.
- `get_variable_defs` returns `valuesByMode` keyed by `modeId`, and variable aliases stay unresolved as `{type: "VARIABLE_ALIAS", id}`. Both have to be walked client-side; neither arrives flattened.
