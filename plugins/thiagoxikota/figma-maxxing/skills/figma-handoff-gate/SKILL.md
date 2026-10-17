---
name: figma-handoff-gate
description: >-
  Pre-ship gate for a Figma handoff. Runs 17 checks before a section is declared ready for
  developers: action completeness (every drawn action has a designed outcome, and inverse pairs
  such as add and remove both exist), annotation layout and contrast, dense spec cards with no AI
  stuffing, a hand-crafted surface with no trace of the process, and proof at the right scale.
  Run figma-slop-check first. Use when the user says "ready for handoff", "dev-tag", "release
  section", "spec card", "run the handoff gate", or in Portuguese "pronto pra handoff".
license: MIT
compatibility: >-
  Read-only until a fix is approved. Detector snippets are Plugin API JavaScript written for
  figma_execute (figma-console-mcp, Desktop Bridge plugin in Figma Desktop). The official Figma
  MCP server's use_figma also runs Plugin API JavaScript, but this gate was not validated there.
  Reads the figma-canon skill; approved fixes go through figma-preflight.
metadata:
  author: Thiago Xikota
  version: "1.2.0"
---

# figma-handoff-gate

Pre-ship gate for handoff sections. It catches handoff-specific bugs that a slop and precision pass misses: orphan actions, weak annotations, inflated screen counts, process residue on the canvas, proof taken at the wrong scale.

**Run `figma-slop-check` first.** This gate assumes the screens already passed it.

The detector snippets below are Plugin API JavaScript. Run them through `figma_execute` (figma-console MCP server, Desktop Bridge plugin running in Figma Desktop). The gate reports. It changes nothing on the canvas until the user approves a fix (see "Apply-fix commands").

## When to fire

- Before declaring any handoff, PR or dev-tag deliverable done (dev-tag: a section marked as ready for developers).
- After `figma-slop-check` passes on the same section.
- On request: "run handoff gate on this section".

## Validates against handoff-format.md canon

The canon is [`figma-canon/references/handoff-format.md`](../figma-canon/references/handoff-format.md). Its "Terms" section ([`figma-canon/references/handoff-format.md#terms`](../figma-canon/references/handoff-format.md#terms)) defines spec card, caption and note card, the three surfaces these checks name.

Required checks (all must pass). Report a broken requirement as `[BLOCKER]`. Report an item that a check only asks you to flag (for example a gap over 120px in check 1) as `[WARN]`. Any finding of either level puts the result in the FAIL template, which lists both as issues before ship.

### 1. Frame spacing

- Sections with a right-side annotation column:
  - `SCREEN_TO_ANNOTATION_GAP` = 80px (screen right edge to annotation column left edge)
  - `CLUSTER_TO_CLUSTER_GAP_H` = 160px (cluster to next cluster)
  - `ROW_GAP_V` = 200px (cluster row to next cluster row)
  - `SECTION_TITLE_CLEARANCE` = 48px
- Sections without per-screen annotations: uniform spacing of at least 80px between handoff frames, no tight clustering (under 60px = fail), no excess gaps (over 120px = flag)
- See [`figma-canon/references/handoff-format.md#spacing-canon`](../figma-canon/references/handoff-format.md#spacing-canon) for the full table

### 2. Frame-name clearance

- At least 24px gap above the first frame for label readability
- Frame name visible without zooming
- Section title not overlapping frame content

### 3. Caption layout

- Badge + title: HUG horizontal frame
- Body + triggers: AUTO + FILL vertical frame
- NOT all-FILL inside HUG (the caption FILL-in-HUG overflow bug)
- See [`figma-canon/references/handoff-format.md`](../figma-canon/references/handoff-format.md) for the diagram

### 4. Caption visual

- Subtle dashed border (1px, neutral color)
- NO amber/yellow slop
- NO heavy backgrounds
- These rules cover captions (the content of a spec card). Note cards (checks 13 and 14) follow their own dark visual spec, including a small accent on their `Why:` / `Edge:` prefixes. That accent is part of the note card spec, not amber slop.

### 5. Spec card content

- 3-5 bullets max per card
- Each bullet = `deliverable + value`
- NO internal jargon: ticket codes (`TICKET-123`), internal tool names ("the v2 validator"), registry or rule codes, and the like
- NO `@user_NNN` placeholders (use realistic names or strip)
- NO AI-stuffed verbose explanations. Check the copy against "Hype copy ban" in [`figma-canon/references/ai-slop-signatures.md`](../figma-canon/references/ai-slop-signatures.md)

### 6. Screen-count integrity

- Components / banners / sheets categorized SEPARATELY from screens
- Screens numbered NN-name; components, banners and sheets are not in the screen count
- No inflation: "12 screens" must be 12 actual screens

### 7. State variants in Component sets

- Hover / disabled / loading / error states live in Component variant sets
- NOT as raw frames in the delivered handoff
- See [`figma-canon/references/handoff-format.md#state-variants-live-in-component-sets`](../figma-canon/references/handoff-format.md#state-variants-live-in-component-sets), and your project's own build skill or workflow, if any

### 8. 4-lens critique stamped

- Has the work been viewed through the dev / designer / PM / CEO lenses?
- See [`figma-canon/references/handoff-format.md#4-lens-pre-ship-critique-mandatory`](../figma-canon/references/handoff-format.md#4-lens-pre-ship-critique-mandatory) for the questions of each lens
- Each lens catches a different gap class
- Stamped means written down. If the conversation holds no record of the critique, run the four lenses now and print one line per lens in the gate output: what it found, or "none". That printed block is the stamp.

### 9. Localization rule (applied per project)

- If the project has a localization rule, it is applied consistently across the whole handoff. For example, a project may keep the Figma source in one language and leave the others to app localization. Do not mix locales in one handoff.
- No placeholders such as `@user_123`: replace them with realistic names in the file's language.
- See [`figma-canon/references/handoff-format.md#project-locale-and-sample-names`](../figma-canon/references/handoff-format.md#project-locale-and-sample-names)

### 10. Self-correction in reports

- If the gate is for a stakeholder report deliverable: no bullets exposing your own audit/fix history
- See [`figma-canon/references/handoff-format.md#reports--comms`](../figma-canon/references/handoff-format.md#reports--comms) and "Self-corrections in reports" in [`figma-canon/references/ai-slop-signatures.md`](../figma-canon/references/ai-slop-signatures.md)
- Each bullet = deliverable + value, not internal jargon

### 11. Em dash + curly quote sweep (mandatory)

- Zero em dashes (U+2014) AND zero curly quotes or apostrophes (U+2019, U+2018, U+201C, U+201D) in any text node in the section
- Treat both as AI/typographic tells. Replace the em dash with a period, comma, parentheses or a sentence break. Replace curly quotes with the straight `'` and `"`
- Sweep (must return empty):

```js
findAll(section, n => n.type === "TEXT" && (n.characters.includes("\u2014") || /[\u2019\u2018\u201C\u201D]/.test(n.characters)))
```

- `findAll(section, fn)` above is shorthand. In the Plugin API it is `section.findAll(fn)`.
- That sweep reads only the characters of TEXT nodes. This check also covers frame names and descriptions, so run a second sweep for those (must also return empty):

```js
const re = /[\u2014\u2018\u2019\u201C\u201D]/;
const section = await figma.getNodeByIdAsync("123:456"); // the section's node id
const nodes = [section, ...section.findAll(() => true)];
return nodes
  .filter(n => re.test(n.name) || ("description" in n && re.test(n.description || "")))
  .map(n => ({ id: n.id, name: n.name }));
```

- Curly characters slip in when copy is typed directly (field note, 2026-05: two possessives in handoff copy arrived with a curly apostrophe, U+2019). The canon is the straight apostrophe. On that project it also matched the existing UI copy.
- Applies to: handoff annotations, captions, popup/sheet copy, panel text, descriptions, frame names

### 12. State coverage (all visible, not just happy path)

- For a feature with M triggers + N bypass/error paths, the handoff must have at least 1 frame per case
- Each distinct trigger condition gets its own frame, showing its own content and state. Field example: for a rule that detects and blocks certain input, one frame per detected input type, each with its own echoed content, its own highlight and its own status label
- Each bypass path gets its own frame (for example a user tier that is exempt, or an input type the rule skips)
- Each error/recovery state gets its own frame
- Happy path / control included for comparison
- Continuity states (post-success return with the draft preserved) included
- Linked destinations (for example a policy page behind a "Why this rule?" link) included as separate frames
- Group with section labels: "Main flow", "Variants" (on a detection feature, "Detection variants"), "Edge cases", "Continuity"
- Required states per screen class: [`figma-canon/references/state-coverage.md`](../figma-canon/references/state-coverage.md)

### 13. Annotation contrast (dark notes on light screens)

- When the handoff shows light/white mockups, note cards and panels must be dark themed
- This creates visual hierarchy between "the design" and "meta-content about the design"
- Use the project's own dark tokens. With none, use these neutral values: card background `#16181D`, stroke `#2A2E37`, title `#FFFFFF`, body `#C4C8D0`
- Accents: two accent colors from the project's tokens, one for the label and one for the `Why:` / `Edge:` prefixes (for example a green and an amber). With no project accent, use `#E5484D` (configurable) for the label. With no second accent, reuse the label accent for the prefixes, as [`figma-canon/references/handoff-format.md`](../figma-canon/references/handoff-format.md) specifies.

### 14. Annotation pattern (2026-05-25, cross-project canon)

- Annotations live in a **right-side column** per screen, top-aligned, 320px wide, 80px gap from the screen edge
- Each note card uses the `HandoffNote` component instance (NOT raw frames). No prebuilt component ships with these skills: if the file has no annotation component, build one once from the spec in [`figma-canon/references/handoff-format.md`](../figma-canon/references/handoff-format.md), then reuse instances
- Copy voice: `When [trigger], [outcome].` (a human sentence: subject + verb + condition)
- Schema: label + WHEN + WHAT (always) + WHY (only when non-obvious) + EDGE (only when the state varies)
- Card density 30-100 words. Over 100 = split. Under 20 while the developer needs more = add WHY/EDGE
- See [`figma-canon/references/handoff-format.md#annotation-pattern-cross-project-canon-2026-05-25`](../figma-canon/references/handoff-format.md#annotation-pattern-cross-project-canon-2026-05-25)

### 15. Action-completeness / flow closure (mandatory, the "no orphan actions" check)

The single most-repeated miss (field note, 2026-05: a developer saw an "add" action drawn and had to ask how removing would work). The developer builds exactly what is drawn: **every visual action needs its outcome drawn**, or the developer has to guess.

- **Enumerate, don't eyeball.** For each new or changed screen, `findAll` every interactive element: buttons, CTAs, icon buttons, **info/help (i) icons**, toggles, radio/checkbox rows, list rows (tappable), chips, links, kebab/overflow menus, swipe affordances, FABs. List them.
  - No node type means "interactive", so build the list in two passes. First the wired nodes: `screen.findAll(n => n.reactions && n.reactions.length > 0)` (reactions live on nested children, not on the screen frame root: see "Prototype reads" in [`figma-canon/references/plugin-api-anomalies.md`](../figma-canon/references/plugin-api-anomalies.md)). Then walk the screen for the element types above that are drawn but not wired, by layer and component names and by eye. An unwired control is exactly what this check hunts.
  - Print each candidate as node id + name. The audit mode of `figma-preflight` ("Cross-screen flow") cross-checks the same screens for dangling CTAs and dead ends.
- For EACH, name the designed outcome (a frame / sheet / state in the file). If the outcome does not exist as an artifact: **FAIL** (orphan action).
- **Inverse-pair law:** if one direction exists, its inverse MUST exist. Add / Remove, Assign / Unassign, Open / Close or Dismiss, Enable / Disable, Mute / Unmute, Ban / Unban, Expand / Collapse, Follow / Unfollow, Pin / Unpin, Approve / Reject, Block / Unblock. An "Add another item" button with no remove path = FAIL.
- **Help/info icon law:** any `(i)` / `?` / help affordance MUST open a designed info screen or sheet (not a dangling icon).
- **Actor-symmetry law:** any feature where one actor acts ON another needs BOTH surfaces designed: the actor's (admin/owner) AND the affected member's. Example: an admin can suspend a member, so the member's own screen showing the suspension must exist too. The admin side drawn without it = FAIL.
- **Destructive/irreversible law:** delete / remove / ban / leave / reset needs a confirm state designed. The "after" (toast, empty state, updated list) needs to exist too.
- Output an **action -> outcome map** in the gate result. Orphans are blockers, not warnings.

This is mechanical on purpose: it removes reliance on "remembering to design the whole flow". Run it as the LAST gate check before declaring the handoff done.

### 16. Hand-crafted surface (client/owner-facing files)

Calibrated on a client handoff (field note, 2026-07). Rule: nothing in a delivered handoff may look machine-made; every surface must read as hand-crafted. In a file that a client, owner or external stakeholder will open:

- **Zero process log on the canvas:** no QA log, no fix list, no "adversarial pass", no "sprint", no session changelog. Process notes (QA log, fix list) live outside the Figma file, in a project file of your choice or in the agent's own memory system if it has one, never in a visible frame.
- **Zero mention of a review or AI tool:** ChatGPT, "external review/judgment", skill or pipeline names. A recommendation on a board is written in the designer's voice ("my recommendation is..."), never "reviews recommend".
- **Layout grids OFF** on every delivered frame. Clones inherit visible grids and the canvas takes on an assembly-line look. Hide the grids and keep their definitions by reassigning a modified copy, the same clone-mutate-reassign pattern as fills (see [`figma-canon/references/plugin-api-core.md`](../figma-canon/references/plugin-api-core.md)): `frame.layoutGrids = frame.layoutGrids.map(g => ({ ...g, visible: false }))`.
- **Context boards belong to the designer:** architecture, behavior contracts, handoff notes. Those stay. What leaves is the trace of HOW the work was produced.
- **Mechanical sweep:** collect the TEXT nodes of the page with `page.findAllWithCriteria({ types: ["TEXT"] })` and match them against a term list (ChatGPT, GPT, adversarial, fix list, sprint, QA, external review, prompt, plus the names of the AI tools, skills and pipelines your own process used), then triage the hits by hand. On a large page, raise the `figma_execute` timeout (default 5000 ms, maximum 30000 ms). Watch for false positives: "This is a prompt message." is the prompt slot of an iOS navigation bar, and a place name can contain "AI" as a substring ("Mumbai").
- **Process artifacts** (review exports such as a zip of renders, file manifests, review verdicts) are PRIVATE to the designer. They never travel with the handoff.

### 17. Scale of proof + simulating the recipient (field note, 2026-08, paid for in production)

The checks above measure STRUCTURE. None of them measures USE, and all of them inherit the scale of the artifact you looked at. On one delivery of an options board, `figma-slop-check` (both lenses), this gate and a flow-graph audit (such as the audit mode of `figma-preflight`) all came back green, and **four real defects survived**.

**17a. Proof of a small element is a capture of the NODE, at scale >= 2x.** The send button of a composer was an empty ellipse, with no icon, on 16 screens. It had been checked several times on a render of the whole section scaled down to 40%, where 36px becomes a colored dot. Rule: list the elements under ~48px that you created or cloned (send button, chip, badge, toggle, avatar, icon) and capture ONE of each type in isolation, at 2x or more: `figma_capture_screenshot` with that element's `nodeId` and `scale` set to 2 or higher. A container render does not judge a small element.

**17b. An entry point is not wiring.** Wiring between frames and reachability are one axis. The starting point of the prototype is another. A perfectly connected graph can open on a random screen when the stakeholder presses `Present`. Before writing "clickable" or "you can walk through it", run:

```js
figma.currentPage.flowStartingPoints.map(f => f.nodeId)
```

and confirm that the screens you are going to present are in the result. Flow starting points belong to a page, and `figma.currentPage` is whatever page is active, which another session or the designer can switch. Make sure the page that holds the prototype is the active one first (re-assert it from a known node, as in "findAllWithCriteria runs on figma.currentPage" in [`figma-canon/references/plugin-api-anomalies.md`](../figma-canon/references/plugin-api-anomalies.md)).

**17c. Simulate the recipient, in writing.** Before sending, answer as the recipient:

- They press Play and land where?
- Do they find the section, or is it 30 thousand pixels of scroll?
- Does the text I wrote match what they see?
- What new question does this screen create that the file does not answer?
- If the artifact offers more than one alternative, can they decide, or did it become a menu with no bet?

## Output

### Pass

```
PASS figma-handoff-gate: all 17 checks clear. Handoff ship-ready.

Section: <section name>
Frames: <N>
Components used: <N>
Last verified: <timestamp>

Action -> outcome map:
<action> -> <frame name> (<node-id>)
...
```

### Fail

```
FAIL figma-handoff-gate: <N> issue(s) before ship:

[BLOCKER] 1. <issue> -> location <node-id> -> apply-fix: <command>
[WARN]    2. <issue> -> location <node-id> -> fix: <description>
...

Action -> outcome map:
<action> -> <frame name> (<node-id>)
<action> -> ORPHAN
...

Run apply-fix commands OR address manually, then re-invoke gate.
```

Either result carries the action -> outcome map from check 15. Each orphan action is a `[BLOCKER]`, never a `[WARN]`.

## Apply-fix commands

For automated fixes, the gate emits explicit commands like:

- `figma_execute: set frame "01-home" gap to 80px`
- `figma_execute: rebind caption-body from FILL-in-HUG to AUTO+FILL`

These are plain-language fix descriptions addressed to `figma_execute`, not tool syntax: `figma_execute` takes Plugin API JavaScript. At apply time, write that code for the approved fix.

The user approves each fix before execution. NO mass mutation. An approved fix is a write to the file, so it goes through `figma-preflight` like any other `figma_execute` write.

## Decay

If frames are mutated AFTER a gate pass, re-run the gate before re-declaring done.

## Composes with

- `figma-slop-check`: runs BEFORE this gate (machine-made tells and precision pass first)
- `figma-canon`: this gate reads [`figma-canon/references/handoff-format.md`](../figma-canon/references/handoff-format.md) (every check) + [`figma-canon/references/ai-slop-signatures.md`](../figma-canon/references/ai-slop-signatures.md) (checks 5 and 10: "Hype copy ban" and "Self-corrections in reports")
- `figma-preflight`: gates every approved apply-fix write, and its audit mode cross-checks check 15
- Your project's own build skill or workflow, if any: this gate is the final gate, after `figma-slop-check`. If such a workflow exists, it writes component descriptions and this gate does not. Either way, this gate validates frame layout and spec cards, and check 11 sweeps descriptions for dashes and curly quotes
