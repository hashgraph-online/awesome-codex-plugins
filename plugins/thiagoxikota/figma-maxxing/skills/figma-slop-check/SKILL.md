---
name: figma-slop-check
description: >-
  Quality gate that runs after a write to a Figma file and before figma-handoff-gate, before any
  frame is called done. Two lenses. Slop: does it look machine made (overlap, AI-stuffed cards,
  status emoji creep, hype copy, names and canvas notes that read as generated). Rigor: is it
  precise (values bound to variables and styles, sizes on the project's scales, components
  intact, auto layout sized right, one wording per concept, screenshot proof). It reads and
  reports: PASS, or a numbered punch list by node id. Use when the user asks "is this ready?", "final review", "audit this screen",
  "ship it", "tá pronto?", "pode fechar", "audita".
license: MIT
compatibility: >-
  Read-only. Checks are written for figma-console-mcp tools (figma_execute,
  figma_get_variables, figma_capture_screenshot) with the Desktop Bridge plugin running in Figma
  Desktop. The official Figma MCP server's use_figma also runs Plugin API JavaScript, but this
  skill was not validated there. Reads the figma-canon skill.
metadata:
  author: Thiago Xikota
  version: "1.2.0"
---

# figma-slop-check

The gate you run before calling any Figma frame done. It looks at the work through two lenses, in this order:

1. **Slop:** does it look machine made? The look and the structure of generated design.
2. **Rigor:** is it precise? Does the screen agree with itself and with the canon.

Nothing is declared ready while a check fails. This skill is a gate: it reads and reports. Fixes are a separate pass (see "On failure").

## Where it sits

`figma-preflight` approves the write, the write happens, then `figma-slop-check` runs, then `figma-handoff-gate`. Each gate fails closed. Slop runs first because it is faster: it judges the overall look, not the structure. Rigor runs second because it has to read structure and cross-reference. Never skip a downstream gate.

## When to run

- After creating or editing any frame, section or component in a Figma file.
- After writing interface copy for the file.
- Before any Figma screenshot is delivered as "final".
- Before any reply that closes a Figma task.
- Before committing specs or docs that describe the screens.
- When the user says "is it ready?", "finalize", "final review", "audit this", "ship it", "review with rigor", "are we good?", "can we close this?".

## The premise

You are not reviewing your own screen. You are reviewing the screen of another designer whom you want to catch lying. Go in with a magnifying glass on:

- every declared padding versus the rendered padding
- every radius versus the radius of its sibling
- every string versus the canonical string in the glossary
- every color versus the token that should be there
- every icon versus the size of the same icon on another screen

If it passes your eyes the first time without an objection, **look again**. The first pass is blind.

Why the gate exists: without it, a handoff ships with one capitalization on one screen and another on the next, with r=16 on a card and r=20 on an "identical" card, with a raw hex where a token belongs. The engineer opens the file, sees the inconsistency and loses trust in the design system. It is expensive to fix later and cheap to catch now.

## Load first

| Reference | What this gate takes from it |
| --- | --- |
| [`figma-canon/references/ai-slop-signatures.md`](../figma-canon/references/ai-slop-signatures.md) | The catalog of slop patterns and the severity table. This skill points at it and does not repeat it. |
| [`figma-canon/references/quality-rubric.md`](../figma-canon/references/quality-rubric.md) | The 5 auto-fail criteria and the 0-10 score (8/10 minimum). |
| [`figma-canon/references/naming-canon.md`](../figma-canon/references/naming-canon.md) | Naming rules, the banned list and the Human authorship section. |
| [`figma-canon/references/state-coverage.md`](../figma-canon/references/state-coverage.md) | Required states per screen class. |
| [`figma-canon/references/handoff-format.md`](../figma-canon/references/handoff-format.md) | Handoff-specific slop (amber captions, FILL-in-HUG overflow, `@user_NNN` placeholders), plus the handoff spacing and caption canon. |
| `references/checks.md` | The 11 rigor checks, plus the one read-only pass that feeds them. |
| `references/punch-list.md` | Severity, the swap, snap and ask actions, where expected values come from, what to leave out, and the decisions file. |

Also read the project map (`figma-map.md`, default `docs/figma-map.md`) for the project's scales, glossary and conventions. Project canon overrides the universal one.

## Lens 1: Slop (does it look machine made)

Run the checks that apply to what was made: design (S1 to S6), copy (S7), reply (S8).

### S1. Overlap and spacing integrity

- No frame, card or element overlaps another.
- Free-positioned frames stacked in a column leave room for the frame-name label that Figma draws above each frame: no label lands on the frame above it.
- A caption or annotation beside a frame sits at least 32px from it.
- The internal padding of a card is at least 16px.
- The section background is distinct from the frame background.

Detect: take a screenshot of the whole section at scale 0.4 and review it. In a handoff section built with right-side annotations, the stricter spacing constants of [`figma-canon/references/handoff-format.md`](../figma-canon/references/handoff-format.md) apply.

### S2. Information density (AI-stuffed cards)

- A spec or annotation card does not have 8 or more fields. A card with PURPOSE / ENTRY / EXIT / COMPONENTS / TOKENS / COPY / STATES / A11Y / ANALYTICS / EDGES / TBDs is a red flag.
- A spec or annotation card has at most 5 visible elements (number + title + 1 or 2 lines + optional status).
- No field is filled just to be filled. If there is no relevant edge case, do not write "n/a".
- No auto-generated footer card such as "Component additions" or "Token additions". That goes into the repo docs, not into Figma.

### S3. Status marker creep

- Status pills and status emoji (colored circles, check marks) do not appear on every card. Only where they communicate something: 1 pill on the cover, not 18 on the captions.
- No `[NEW]`, `[WIP]` or `[DRAFT]` glued to every surface.

### S4. Human authorship (names and canvas notes)

Delivered files are read by teammates and stakeholders. Nothing in them may carry a sign that it was made by AI. What gives it away:

- a status emoji in a name
- invented codenames (`V1`, `A2`, "OPTIONS", "BATCH")
- metadata packed into a name: a date, who approved it, the state of the process
- a canvas note structured like a spec: ALL-CAPS headers, bullets nested by taxonomy, meta words ("verbatim", "blueprint", "grouping rule"), structural bold on every line
- consistency that is too perfect between sibling names (one template repeated N times)
- a "read me" or "Start here" card with numbered sections for decisions, contents and pending items

What a human designer does: a short, plain name, sometimes lowercase and sometimes not, with no visible system. An annotation in running prose, 2 to 6 sentences, like a spoken comment. If something must be marked, one loose word ("approved", "old") and no more. Pending items go to chat, not onto the canvas.

The existing convention of the file is NOT an alibi. The sibling pattern may be exactly what the designer just rejected (field note, 2026-07: a new section copied the naming pattern of its older siblings hours after that pattern had been rejected). The rule also covers FigJam, comments and descriptions.

When options need comparing on the canvas, each option gets its own box, with pros on `+` lines and cons on lines that open with the minus sign U+2212 (never an em dash). The recommended option gets a visible marker and one final "because ..." line. A format that reads well: a white card with a border stroke per option, a bold green `+`, a bold red minus sign, and on the recommended one a 1.5 accent stroke, an accent pill and the "because ..." line in SemiBold. Label the recommendation in plain first-person words, with a qualifier when it is conditional, never an ALL-CAPS "RECOMMENDED". No caps headers, no governance numbering.

Detect: scan the top-level names of the page for emoji, codenames and dates. The expected count is zero. Before creating a section or a note, ask: would a designer in a hurry write this? Full rule: the Human authorship section of [`figma-canon/references/naming-canon.md`](../figma-canon/references/naming-canon.md).

### S5. Visual cocktail and decorative excess

- Apply "Visual cocktail signature" and "Decorative excess" from the catalog.
- Type hierarchy comes from weight and size, not from a loud color.
- No glass stacked on glass without separation, and no glass with nothing behind it to refract.
- When the project map or agent instructions declare a visual direction, a frame that breaks it fails here. Examples for an iOS-native direction: no flat drop shadow as the primary depth cue, no neon gradients.
- Before flagging a card as slop, apply the Sibling-check rule of the catalog: inspect at least 2 siblings of the same class first.

### S6. Mechanical repetition

- The same structure across all captions is fine (consistency). The content must be unique per surface.
- The same placeholder text ("Lorem...", "Default value...") does not appear in more than one place.

### S7. Copy slop

- **Hype words:** the "Hype copy ban" list of the catalog, plus "comprehensive", "crystal clear", "unleash", "delightful", "amazing", and their equivalents in the language of the copy. "Intuitive" is allowed only when it describes a real physical gesture.
- **SaaS boilerplate leads:** "Manage your X", "Get started in seconds", "Welcome to...", "Whether you're a...", "Designed to help you...", "Connect with friends and...".
- **Friendly emoji in error or empty states:** "Oops! Something went wrong..." followed by a nervous smile fails. "It did not work. Try again." passes.
- **A long sentence that says nothing:** if a sentence can be cut in half without losing meaning, cut it.
- **Sample data:** no realistic creator-style handle (a first name plus a vibe word, or a first name plus an initial). Two rules conflict on the replacement: the field slop rule offers neutral i18n handles such as `@user_001`, while [`figma-canon/references/handoff-format.md`](../figma-canon/references/handoff-format.md) bans `@user_NNN` placeholders and asks for realistic names in the file's language. The project map decides; if it is silent, ask the designer.
- **Locale:** currency and number format follow the locale of the screen (symbol, decimal separator). No hardcoded `$` that assumes USD.
- **Project terms:** compare against the project's glossary and voice guide, if it has them (the `wording` check).

Detect: dump the `characters` of every TEXT node and search for the lists above. Then read the copy aloud: if it sounds like a SaaS demo, it is slop.

### S8. The closing reply (it is part of the work)

- No preamble ("I'll start by...", "Let me first...", "I'll go ahead and...").
- No trailing summary ("Here's what I did: 1. ... 2. ...", "All done!", "Hope this helps!").
- Do not restate the request ("You asked me to fix the spacing, so I'll..."). Just do it.
- No defensive disclaimers unless safety needs them ("Just to clarify...", "If I understood correctly...", "Please let me know if...").
- No `## Summary`, `## Changes` or `## Next steps` headers in a normal reply. Headers belong in documents, not in chat.
- No status emoji unless the user explicitly wants them. No bullet list of 3 items when 1 sentence does it.
- Do not expose your own audit and fix process in a stakeholder report (see "Self-corrections in reports" in the catalog).

## Lens 2: Rigor (is it precise)

11 rigor checks in 5 groups, ordered by what a node stores. `references/checks.md` says what each one reads and when it fails. Run them on data you collected through the figma-console MCP server, not from memory.

| Group | Check | Fails when (short form) |
| --- | --- | --- |
| Bound or loose | `color` | A raw hex where the variable exists, a color with no variable, an invented variable or style name |
| | `text-style` | Text with no style where one fits, one role at two sizes or weights, a foreign font family |
| | `scale` | A padding, gap, radius or icon size off the project's scale, a decimal, siblings that disagree, an emoji as an icon |
| Components intact | `detached` | A frame detached from a component, a component-named layer that is not an instance, an instance with no main component |
| | `properties` | A variant value outside its options, an unknown property, a needed property unset |
| Auto layout sized right | `sizing` | Same-family screens at different widths, fixed where it should hug, hug where it should fill |
| | `collapse` | A content child under 70% of its vertical parent's width, a node 1px wide or 0px tall |
| | `fill-in-hug` | Text set to fill inside a horizontal frame that hugs, absolute text inside auto layout |
| Words | `wording` | A glossary term broken, one concept written two ways across screens |
| | `names` | Default Figma names, a component name without `/`, a root frame without `NN-name` |
| Pixels | `screenshot` | A capture shows overlap, collapse or a bad crop. Skipping the captures is itself critical |

### Catalog checks (apply them as the canon writes them)

- **Auto-fails:** the 5 criteria of [`figma-canon/references/quality-rubric.md`](../figma-canon/references/quality-rubric.md) (hardcoded colors, missing auto layout, default Figma names, detached components, layer overlap). Any one of them means that section is redone, not declared done. In the punch list each keeps the severity of the catalog's Severity scoring table (default names are Critical; hardcoded hex, missing auto layout and detached instances are High), and any one of them blocks a PASS.
- **Reuse, tokens and layout:** apply "Component reuse failures", "Token violations", "Layout & positioning" and "Card and state anti-patterns" from the catalog: a new `Button` drawn while `Button/Primary` exists, an icon recreated as vectors, inline effect styles while elevation tokens exist, a hardcoded font size or spacing, a top-level node at (0,0) colliding with content, `resize()` called after the sizing modes. Take the severity from the catalog's table; where it has no row, the catalog only says "flag": place it with the severity table in `references/punch-list.md`.
- **Contrast and targets:** "WCAG auto-fails" in the catalog (text and UI contrast, text size, color-only state, focus indicators). When judging contrast, compose the opacity chain of the node and of its groups (the opacity chain rule in the Hard rules of the `figma-canon` skill).
- **State coverage:** a screen with only the happy path loses a point in dimension D of the rubric. Check the required states for its screen class in [`figma-canon/references/state-coverage.md`](../figma-canon/references/state-coverage.md).
- **Score:** rate the frame with the rubric. Below 8/10, fix before declaring done. Cite the score in the report.

## Workflow

1. **Define the scope.** One screen, a set of sibling screens, or a whole section? Ask for the node id or the URL if it is not obvious. If the session has just written something, use the last selection: the node ids that write returned. Otherwise read the live selection with `figma_get_selection` and confirm the target with the user.
   - 1 screen: every check, with `wording` limited to its glossary half.
   - 2 to N sibling screens: every check, with the cross-screen comparisons on.
   - A whole section: every check, plus a summary table per screen.
2. **Refresh state.** Call `figma_search_components` (node ids are session specific and may be stale). If the Bridge is disconnected, run the `figma-bridge-doctor` skill and stop. If the file changed since the last session, run `figma-orient` first.
3. **Run the Slop lens** on what applies: design, copy, reply.
4. **Collect read-only data** with a short `figma_execute` read of your own, one screen per call. What to collect, and how to bring it back, is in "Read once, then judge" in `references/checks.md`.
5. **Run the Rigor checks** over the collected data, group by group, then the catalog checks.
6. **Prove it by screenshot, at the right scale:**
   - the whole section at scale 0.4, to see overlap and spacing (S1)
   - 3 to 5 representative frames, one per category: a form, a list, a dashboard, a multi-section screen, the dark outlier if there is one (the `screenshot` check)
   - every element that was fixed, captured on its own rather than as part of a sample
   - an overview is not proof of a fix at component level: the crop-scale rule (at least 1.2x) in the Hard rules of the `figma-canon` skill sets the scale for that crop
7. **Emit the output** (next section), ordered by severity, highest first.
8. **Pass again when asked.** A request such as "fix all" or "did you verify everything?" makes multiple passes mandatory: show the verification (grep plus a zero-residual report) and never claim done on a single pass (see "Multi-pass verification flag" in the catalog). Do this audit as a close read by a single agent, not as a parallel fan-out (see "Subagent fan-out caveat" in the catalog).

## Output

### Slop log (internal)

```text
SLOP CHECK - [design | copy | reply]
- S1 layout: PASS / FAIL (reason)
- S2 density: PASS / FAIL (reason)
- S3 markers: PASS / FAIL
- S4 authorship: PASS / FAIL (names found)
- S5 visual: PASS / FAIL
- S6 repetition: PASS / FAIL
- S7 copy: PASS / FAIL (words detected)
- S8 reply: PASS / FAIL
```

This log is an internal gate. Do not paste it into the reply to the user.

### PASS

```text
PASS figma-slop-check: <N> checks run, 0 findings. The screen agrees with itself and with the canon.

- Target: <node-id> (<screen name>)
- Rubric: <score>/10
- Proof: section overview at scale 0.4, <N> frame screenshots
- Next gate: figma-handoff-gate
```

`<N>` is the number of checks that step 1 selected. Never hardcode it in the text. After a PASS, run the `figma-handoff-gate` skill as the next lens before declaring the work done.

### FAIL

```text
FAIL figma-slop-check: punch list
Target: <node-id or node-ids> · <screen names>
Checks: <N> run · <N> findings

----------------------------------
1. [COLOR] card raw hex
   Where: 123:789 · card
   Found: fill #16181D raw
   Canon: variable color/surface/card -> #16181D
   Action: swap · distance 0
   Severity: high (the variable exists, it should be bound)

2. [SCALE] list row padding mismatch
   Where: 123:456 · row · Name (row 3 of 11)
   Found: T12 R16 B14 L16
   Canon: T12 R16 B12 L16 (every other row in the list)
   Action: snap · distance +2 (bottom)
   Severity: medium

3. [SCALE] two card radii, no rule yet
   Where: 124:101 · card · Plan; 124:230 · card · Billing
   Found: r=12 on one, r=16 on the other
   Canon: not covered. The radius scale has both steps and no rule for cards
   Action: ask
   Severity: medium
   Question for the designer: which radius do cards use?

...
----------------------------------
Summary: N findings · X high · Y medium · Z low
Actions: A swap · B snap (largest distance: +/-N) · C ask
Apply fix? Say the number (or "all swaps", "all high", "skip"). Read-only until approved.
Asks never enter "all": each one needs your answer.
```

Every finding carries a severity (how much it hurts) and an action (what happens to it): **swap**, **snap** with its signed distance, or **ask**. Definitions, the distance rule and the footer lines for left-out findings and variable modes are in `references/punch-list.md` and `references/checks.md`.

## On failure

- **A failed slop check on work you just made:** fix it before you answer. Never pass it forward as "I will fix it later". Then re-run the check.
- **Rigor findings:** read-only until the user approves. The user answers "fix 2", "fix all high", "apply 1, 3, 5", and you apply ONLY the approved items. Never apply a batch without approval. Each fix gets a validation screenshot (`figma_take_screenshot` of the section afterwards). As of figma-console-mcp v1.40.8, `figma_take_screenshot` falls back to the REST API when the Bridge is not connected, and REST can render stale state after plugin edits ([`figma-canon/references/plugin-api-anomalies.md`](../figma-canon/references/plugin-api-anomalies.md)); `figma_capture_screenshot` always uses the plugin runtime, so prefer it for this proof. Every fix is a write: it goes through `figma-preflight` like any other.
- **By action:** an approved **swap** is applied and nothing is recorded. An approved **snap** is applied and its distance goes into the `fixes` list of the run file, so the change leaves a trail. An **ask** never enters "all": with no answer from the designer, apply nothing and keep it open for the next run.
- **The user accepts a finding as intentional:** record it as `intentional` in `.figma-slop-check/decisions.json`, with a reason and a scope. "Later" on a finding records it as `debt`, and it comes back with its distance until it is fixed (`references/punch-list.md`).
- **"skip" or "leave it as it is":** stop. Do not force the fix.

Stop conditions:

- 3 cycles of fix and re-check and the same check, or the same class of finding, still fails: stop and surface it to the user. No infinite loop.
- At least 1 high finding is not fixed and the user says "ship it": surface the blocker and let the user decide the override. State the override in your reply so it stays in the transcript.
- The Bridge is disconnected: stop and run the `figma-bridge-doctor` skill.

## Not this gate's job

If a finding belongs to one of these, note it and do not act on it.

- Accessibility compliance beyond the catalog's auto-fails is a parallel track. This gate does not replace an accessibility audit (figma-console-mcp v1.40.8 ships `figma_audit_component_accessibility` for an audit at component level).
- Layout strategy and hierarchy belong to a design critique.
- Auto-fix without approval: never.

## Composes with

- `figma-canon`: the catalog, the rubric and the naming, state and handoff canon this gate applies.
- `figma-preflight`: runs before the write, and again before any fix this gate leads to.
- `figma-bridge-doctor`: prerequisite when the Bridge is off.
- `figma-orient`: orient first when the file changed since the last session.
- `figma-handoff-gate`: the next gate. Slop and rigor come first, handoff comes after.
