# Test Plan -- /design-fix

**Trigger:** `/design-fix` and `/quiver:design-fix`

**Setup:**
- A project with an implemented screen or component that differs from its Figma
  design in at least one padding value and one text string.
- The figma-bridge MCP server configured and its Figma plugin running inside the
  file, with the target node selected. For the plan path, a
  `.claude/plans/<slug>-design-plan.md` carrying a `### Node Specs` block.

**Expected behavior:**
1. `/design-fix` with a node selected in Figma and no arguments resolves the
   design side from `get_selection` and prints the node name and ID.
2. `/design-fix 4029-12345` normalizes the hyphen to a colon before any bridge
   call and resolves that node.
3. With no figma-bridge tools available and no plan path given, the skill
   points at the README's setup section, names the plan path alternative, and
   stops -- no comparison is attempted.
4. `/design-fix .claude/plans/<slug>-design-plan.md` runs with the bridge
   absent, loads no bridge schema, reads the Node Specs block, and says when
   the plan was written.
5. With several nodes selected, the skill asks which one and compares exactly
   one.
6. When no implementation of the node is found, the skill prints the
   "nothing to compare yet" message naming `/quiver:design` and `/design-build`, and
   stops without any `AskUserQuestion`.
7. The report table lists deviations highest severity first, with a `file:line`
   for every code value.
8. A node whose axis is `fill` in Figma and `double.infinity` in code produces
   no Box finding on that axis; the reverse case produces a High finding.
9. A deviation traced to a token definition appears under Tokens, not in the
   main table, and no token file is modified.
10. A node matching on every field prints the "matches the design" line and
    stops before Step 5.
11. The fix question offers per-deviation buttons at three or fewer deviations
    and severity groups above that.
12. Selected fixes are applied, every modified file is read back, and the run
    ends with the uncommitted-changes line. No commit and no branch are created.

**Verification checklist:**
- [ ] `/design-fix` appears in the slash menu after a plugin reload.
- [ ] No figma-bridge write tool is named anywhere except in the sentence
      forbidding them.
- [ ] The no-implementation path reaches no `AskUserQuestion` at all.
- [ ] Every user decision uses `AskUserQuestion`, never plain text (R5).
- [ ] `when-to-use:` is a single-line double-quoted string carrying `/design-fix`
      and a quoted user utterance (R10).
- [ ] No `CLAUDE_PLUGIN_ROOT` reference (R4).
- [ ] ASCII only, no emoji (R8).
- [ ] No commit, no branch, no AI attribution anywhere in the flow (R9).
- [ ] Modified files are read back after every write (L3).
- [ ] The Fit rule is stated in Step 3 and repeated in Anti-Patterns.
- [ ] Zero deviations is stated as a valid outcome, not a failure.

**Known gotchas:**
- This skill carries no `!` shell blocks on purpose. It creates no
  branch and no commit, so it needs no git state, and the blocks would add an
  R2/R3/L1 failure surface for data nothing reads. A reviewer looking for the
  usual `NO_GIT` pair is looking at a deliberate absence.
- It also runs no build and no test gate, and so is not a consumer of
  `skills/verification/SKILL.md`. That is the same default `/design-build`
  ships with (`verify_gate: none`), for the same reason: a value-level UI fix
  is checked by looking at it.
- The field list in Step 3 is this skill's own. It deliberately does not
  hand-sync with the `### Node Specs` list in `skills/design/SKILL.md`, so
  there is no contract test binding the two and no drift to catch. Adding a
  field here does not require touching `/quiver:design`.
- A plan read in Step 1 path 1 is a snapshot. When the Figma file moved after
  the plan was written, this skill compares against the old design and cannot
  tell. Re-run `/quiver:design` when the report disagrees with what you see in Figma.
- Figma reports a `fill` axis with a concrete measured number, which is why the
  Fit rule needs to be stated rather than inferred. The node data alone looks
  like a fixed width.
