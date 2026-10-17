---
name: design-fix
description: "Compare one already-implemented screen or component against its Figma source and fix the deviations you pick -- reads the node live through the figma-bridge MCP, or from the Node Specs of an existing /design plan, then diffs box, layout, typography, fill, stroke, radius, effects, and content against the code that renders it. Reports first, fixes only what you select, and never touches Figma."
argument-hint: "<node id, component path, or a short description of the broken UI> [anything extra you want checked]"
when-to-use: "user has a UI that is built but does not match the design -- '/design-fix', 'this screen does not match Figma', 'the spacing is off compared to the design', 'why does this button look wrong', 'compare this component to the design and fix it', 'the card is not pixel perfect'"
---

# Instructions

You compare one built thing against one design, and you fix what the user
picks. The design is the source of truth for values; the code is the source of
truth for what exists. You never guess at either -- every number you report was
read from a Figma node or from a line of code you opened.

This skill has one target per run. It reports before it changes anything, and
it changes nothing the user did not select.

**Never call a figma-bridge write tool** (`create_*`, `set_*`, `delete_nodes`,
`duplicate_nodes`, `reparent_nodes`, `group_nodes`, `ungroup_node`). This skill
is read-only against Figma. A design that does not match the code is a code
finding, never a reason to edit the design.

## Step 0 -- Arguments

Read `$ARGUMENTS` and split it into four things. Any of them may be absent.

1. **A Figma node ID** -- `4029:12345`, or the instance-child form
   `I12740:17806;12740:17793`. Figma share URLs write IDs with a hyphen
   (`4029-12345`); the bridge rejects hyphens, so normalize every hyphen
   between two digit runs into a colon before calling any tool.
2. **A plan path** -- a `.md` path under a `plans/` directory, or any `.md`
   path whose file carries a `### Node Specs` block. A plan path is the design
   side, never a code target; read the file before deciding which of the two a
   path is.
3. **A code target** -- a path, a file name, or a component or class name.
4. **Extra checks** -- anything else the user wrote in plain words
   ("also check the icon size", "the shadow looks too strong"). Add these to
   the field list in Step 3 for this run only.

Nothing in the arguments is required. An empty invocation is not an error --
Step 1 falls through to whatever is selected on the Figma canvas.

## Step 1 -- Resolve the Design Side

Resolve the design in this order and stop at the first that answers.

**1. A plan path in the arguments.** Read the `### Node Specs` block of the
plan and use the recorded values. Say which plan was used and when it was
written -- a plan is a snapshot, and a design that moved since is a deviation
this run cannot see. The bridge is not needed on this path; do not load its
schemas.

**2. A node ID in the arguments, or no plan path given.** Both need the
bridge. Load the read-side schemas:

`ToolSearch` with query
`"select:mcp__figma-bridge__list_files,mcp__figma-bridge__get_selection,mcp__figma-bridge__get_node,mcp__figma-bridge__get_design_context,mcp__figma-bridge__get_variable_defs,mcp__figma-bridge__get_styles"`

If `ToolSearch` returns no figma-bridge tools, the MCP server is not
configured. Print exactly:

```
> figma-bridge MCP is not available. Setup is two pieces -- the MCP server and
> a Figma plugin imported by hand -- and the steps are in the README's
> External Dependencies section. Leave the plugin running inside the Figma file
> you want to read, then retry /design-fix.
> You can also point this skill at an existing plan, which needs no bridge:
>   /design-fix .claude/plans/<slug>-design-plan.md
```

**Stop here.**

With the tools loaded, call `list_files`. An empty result means no Figma file
is connected -- print the same kind of note, naming the plugin, and stop. One
file: use its `fileKey` for every later call. More than one: `AskUserQuestion`
with one button per `fileName`, and carry the chosen `fileKey` into every call,
because the bridge requires it once more than one file is connected.

Then resolve the node: the ID from the arguments, otherwise `get_selection`.

**3. Nothing resolves.** Print:

```
> Nothing to compare against. Select the frame or component in Figma, or pass
> a node ID or a plan path:
>   /design-fix 4029:12345
>   /design-fix .claude/plans/<slug>-design-plan.md
```

**Stop here.**

On the live path, read the node with `get_node` and `get_design_context`, and
resolve every variable and style reference with `get_variable_defs` and
`get_styles` -- a raw hex in a report the project expresses as a token is a
finding the user cannot act on.

Print one line: `> Design side: {node name} ({node id})` or
`> Design side: {plan path}, written {date}`.

When more than one node resolves -- a selection of several frames, or a plan
with several specs -- this skill compares **one**. Use `AskUserQuestion` with
one button per node (up to 4, largest first) to pick the target. Batch scanning
is deliberately not a mode: a run that reports on six screens at once produces
a list nobody acts on.

## Step 2 -- Resolve the Code Side

Find the code that renders the resolved node. This is the only step that
searches the codebase: resolve `codegraph_available` and `lsp_available` with
the detection flows in `skills/code-navigation/SKILL.md`, then search under its
Code Navigation Strategy. Search, in order, for: the code target named in the
arguments, the node's name as a component or class name, the literal strings in
its text children, and the route named in the plan's `Route:` line when a plan
was used.

Print the files you resolved: `> Code side: {path}:{line range}`.

**When no implementation is found, print this and stop:**

```
> No implementation found for {node name}. There is nothing to compare yet.
>
> Build it first:
>   /quiver:design {node id}        writes an implementation plan
>   /design-build            builds the plan
```

**Stop here. Do not ask whether to fix, build, or scaffold anything.** This is
the whole reason the gate exists: offering a fix pass for a screen that was
never built is a question with no correct answer, and it is the defect this
skill was written to avoid. A missing implementation is a report, not a prompt.

When the search finds several candidates and none is clearly the renderer, ask
with `AskUserQuestion` -- one button per candidate path. Do not guess between
two files that both look plausible; a comparison against the wrong file
produces findings that are all false.

## Step 3 -- Compare

Compare these fields, plus anything the user named in the arguments. Omit a row
for any property the Figma node does not set -- an unset property is not a
deviation.

| Field | What is compared |
|-------|------------------|
| Box | Width and height, subject to the Fit rule below |
| Layout | Direction, gap, padding (all four sides), main-axis and cross-axis alignment |
| Typography | Family, weight, size, line height, letter spacing |
| Fill | Background color, expressed as the project's token when one maps |
| Stroke | Width, position (inside, center, outside), color |
| Radius | All four corners |
| Effects | Shadows and blurs: offset, blur, spread, color, opacity |
| Content | The literal text of every text node, or its i18n key when the project has a translation layer |

**The Fit rule.** A Figma axis whose auto-layout sizing mode is `fill` must
never be compared against its measured literal. The measured number is what
that axis happened to be inside one frame width; code expressing the axis as
fill (`double.infinity`, `width: 100%`, `flex: 1`, a stretched cross axis) is
**correct**, and the mismatch is not a finding. The finding on a `fill` axis is
the opposite case: a hardcoded literal in the code where the design says fill.
A comparison that misses this reports a false deviation on every responsive
component in the project, which is worse than reporting nothing.

**Three things are never a deviation:**

- A difference the Fit rule explains.
- A property Figma does not set on the node.
- A value the code reads correctly from a theme token whose *definition* is
  what differs. That belongs in the Tokens section of Step 4 -- the code is
  right, the token is wrong, and fixing it changes every screen that uses it.

**Severity is earned, not assigned:**

- **High** -- visible without measuring: a text string that differs, an element
  present in the design and absent in the code, an element on the wrong axis or
  in the wrong order, a color from a different token family, a hardcoded
  literal on an axis the design fills.
- **Medium** -- right family, wrong step: `12` where the design says `16`,
  `radii.sm` where the design says `radii.md`, a font weight one step off.
- **Low** -- a difference at or below one logical pixel, or a property the
  platform rounds on its own.

## Step 4 -- Report

Print the deviations, highest severity first:

```
| # | Field | Figma | Code | Where | Severity |
|---|-------|-------|------|-------|----------|
| 1 | Content | "Continue" | "Devam" | lib/widgets/pay_button.dart:31 | High |
| 2 | Padding left | 16 | 12 | lib/widgets/pay_button.dart:42 | Medium |
```

Then, only when they have entries:

- **Missing** -- nodes in the design with no counterpart in the code. One line
  each: node name, what it is, where it belongs. This skill does not build
  them; `/quiver:design` and `/design-build` do.
- **Tokens** -- deviations that trace to a token definition rather than to the
  component. One line each: the token, its value, the design's value, the file
  that defines it. This skill does not edit token files -- a token is shared by
  every screen, and changing it to fix one component is a change nobody
  reviewed.

**Zero deviations is a valid and expected result.** Print
`> {node name} matches the design on every compared field.` and stop. Do not
manufacture a Low finding to show the run did something.

## Step 5 -- Fix What the User Picks

Only reachable when Step 4 listed at least one deviation in the main table.

Ask with `AskUserQuestion`. With three or fewer deviations, give one button per
deviation. With more, group by severity:

Buttons: `["Fix the High ones", "Fix High and Medium", "Fix all {N}", "None -- keep the report"]`

The user can name specific numbers instead of taking a button. Apply exactly
what was selected, nothing adjacent, and follow the surrounding code's own
idiom -- a project that reads spacing from a token gets the token, not the
literal the design measured.

After applying:

1. Read every modified file back and confirm the change landed.
2. Print one line per applied fix: the deviation number, the file, and the new
   value.
3. Print `> {N} fix(es) applied, uncommitted. Run /commit when you are ready.`

This skill writes no commit and creates no branch, the same default
`/design-build` runs under. It also runs no build and no test gate: the changes
are layout and style values, the check that matters is looking at the screen,
and a test suite run after a padding change is noise standing in for a check
nobody made. When a fix touched logic rather than a value, say so in the
summary line -- that is the case worth a test run, and it is the user's call.

---

## Anti-Patterns

- Don't compare a `fill` axis against the measured literal -- read the Fit rule
  in Step 3. This is the single most common false finding in design comparison,
  because the measured number is right there in the node and looks authoritative.
- Don't offer to fix, build, or scaffold when Step 2 found no implementation.
  Print the message and stop. The pull toward a helpful "shall I build it?" is
  exactly the defect this gate exists to close.
- Don't build a component that only exists in the design -- report it as
  missing and name `/quiver:design`.
- Don't edit a theme token definition to fix one component's deviation.
- Don't call a figma-bridge write tool. The design is never the thing that is
  wrong here.
- Don't compare more than one node per run. A six-screen report is a list
  nobody acts on.
- Don't report a property Figma never set as a deviation from zero.
- Don't show raw node JSON, raw variable dumps, or tool output to the user --
  every number in the report is one you already resolved.
- Don't apply a fix the user did not select, however obvious the adjacent one
  looks.
- Don't commit.
