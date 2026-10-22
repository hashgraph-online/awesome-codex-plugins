# handoff checks

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

### 1. Frame spacing

- Sections with a right-side annotation column:
  - `SCREEN_TO_ANNOTATION_GAP` = 80px (screen right edge to annotation column left edge)
  - `CLUSTER_TO_CLUSTER_GAP_H` = 160px (cluster to next cluster)
  - `ROW_GAP_V` = 200px (cluster row to next cluster row)
  - `SECTION_TITLE_CLEARANCE` = 48px
- Sections without per-screen annotations: uniform spacing of at least 80px between handoff frames, no tight clustering (under 60px = fail), no excess gaps (over 120px = flag)
- See [`figma-canon/references/handoff-format.md#spacing-canon`](../../figma-canon/references/handoff-format.md#spacing-canon) for the full table

### 2. Frame-name clearance

- At least 24px gap above the first frame for label readability
- Frame name visible without zooming
- Section title not overlapping frame content

### 3. Caption layout

- Badge + title: HUG horizontal frame
- Body + triggers: AUTO + FILL vertical frame
- NOT all-FILL inside HUG (the caption FILL-in-HUG overflow bug)
- See [`figma-canon/references/handoff-format.md`](../../figma-canon/references/handoff-format.md) for the diagram

### 4. Caption visual

- Subtle dashed border (1px, neutral color)
- NO amber/yellow slop
- NO heavy backgrounds
- These rules cover captions (the content of a spec card). Note cards (checks 13 and 14) follow their own dark visual spec, including a small accent on their `Why:` / `Edge:` prefixes. That accent is part of the note card spec, not amber slop.

### 5. Spec card content

- 3-5 bullets max per card
- Each bullet = `deliverable + value`
- NO internal jargon: ticket codes (`TICKET-123`), internal tool names ("the v2 validator"), registry or rule codes, and the like
- Apply the project’s sample-data policy; no real private identities or invented factual claims. Neutral handles may be required by project canon.
- NO AI-stuffed verbose explanations. Check the copy against "Hype copy ban" in [`figma-canon/references/ai-slop-signatures.md`](../../figma-canon/references/ai-slop-signatures.md)

### 6. Screen-count integrity

- Components / banners / sheets categorized SEPARATELY from screens
- Screens numbered NN-name; components, banners and sheets are not in the screen count
- No inflation: "12 screens" must be 12 actual screens

### 7. State variants in Component sets

- Hover / disabled / loading / error states live in Component variant sets
- NOT as raw frames in the delivered handoff
- See [`figma-canon/references/handoff-format.md#state-variants-live-in-component-sets`](../../figma-canon/references/handoff-format.md#state-variants-live-in-component-sets), and your project's own build skill or workflow, if any

### 8. Recipient concerns

Evaluate the applicable developer, designer, product and owner concerns against the requested handoff. Record real gaps or decisions, not a mandatory four-line stamp or separate model pass. Existing evidence can satisfy more than one concern.

### 9. Localization rule (applied per project)

- If the project has a localization rule, it is applied consistently across the whole handoff. For example, a project may keep the Figma source in one language and leave the others to app localization. Do not mix locales in one handoff.
- Follow the project’s declared sample-data convention; do not replace required neutral handles merely because a generic reference prefers names.
- See [`figma-canon/references/handoff-format.md#project-locale-and-sample-names`](../../figma-canon/references/handoff-format.md#project-locale-and-sample-names)

### 10. Self-correction in reports

- If the gate is for a stakeholder report deliverable: no bullets exposing your own audit/fix history
- See [`figma-canon/references/handoff-format.md#reports--comms`](../../figma-canon/references/handoff-format.md#reports--comms) and "Self-corrections in reports" in [`figma-canon/references/ai-slop-signatures.md`](../../figma-canon/references/ai-slop-signatures.md)
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
- Required states per screen class: [`figma-canon/references/state-coverage.md`](../../figma-canon/references/state-coverage.md)

### 13. Annotation contrast (dark notes on light screens)

- When the handoff shows light/white mockups, note cards and panels must be dark themed
- This creates visual hierarchy between "the design" and "meta-content about the design"
- Use the project's own dark tokens. With none, use these neutral values: card background `#16181D`, stroke `#2A2E37`, title `#FFFFFF`, body `#C4C8D0`
- Accents: two accent colors from the project's tokens, one for the label and one for the `Why:` / `Edge:` prefixes (for example a green and an amber). With no project accent, use `#E5484D` (configurable) for the label. With no second accent, reuse the label accent for the prefixes, as [`figma-canon/references/handoff-format.md`](../../figma-canon/references/handoff-format.md) specifies.

### 14. Annotation pattern (2026-05-25, cross-project canon)

- Annotations live in a **right-side column** per screen, top-aligned, 320px wide, 80px gap from the screen edge
- Each note card uses the `HandoffNote` component instance (NOT raw frames). No prebuilt component ships with these skills: if the file has no annotation component, build one once from the spec in [`figma-canon/references/handoff-format.md`](../../figma-canon/references/handoff-format.md), then reuse instances
- Copy voice: `When [trigger], [outcome].` (a human sentence: subject + verb + condition)
- Schema: label + WHEN + WHAT (always) + WHY (only when non-obvious) + EDGE (only when the state varies)
- Card density 30-100 words. Over 100 = split. Under 20 while the developer needs more = add WHY/EDGE
- See [`figma-canon/references/handoff-format.md#annotation-pattern-cross-project-canon-2026-05-25`](../../figma-canon/references/handoff-format.md#annotation-pattern-cross-project-canon-2026-05-25)

### 15. Action-completeness / flow closure (mandatory, the "no orphan actions" check)

A repeated production miss (field note, 2026-05: a developer saw an "add" action drawn and had to ask how removing would work). The developer builds exactly what is drawn: **every visual action needs its outcome drawn**, or the developer has to guess.

- **Enumerate, don't eyeball.** For each new or changed screen, `findAll` every interactive element: buttons, CTAs, icon buttons, **info/help (i) icons**, toggles, radio/checkbox rows, list rows (tappable), chips, links, kebab/overflow menus, swipe affordances, FABs. List them.
  - No node type means "interactive", so build the list in two passes. First the wired nodes: `screen.findAll(n => n.reactions && n.reactions.length > 0)` (reactions live on nested children, not on the screen frame root: see "Prototype reads" in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md)). Then walk the screen for the element types above that are drawn but not wired, by layer and component names and by eye. An unwired control is exactly what this check hunts.
  - Print each candidate as node id + name. The audit mode of `figma-preflight` ("Cross-screen flow") cross-checks the same screens for dangling CTAs and dead ends.
- For EACH, name the designed outcome (a frame / sheet / state in the file). If the outcome does not exist as an artifact: **FAIL** (orphan action).
- **Inverse-pair law:** if one direction exists, its inverse MUST exist. Add / Remove, Assign / Unassign, Open / Close or Dismiss, Enable / Disable, Mute / Unmute, Ban / Unban, Expand / Collapse, Follow / Unfollow, Pin / Unpin, Approve / Reject, Block / Unblock. An "Add another item" button with no remove path = FAIL.
- **Help/info icon law:** any `(i)` / `?` / help affordance MUST open a designed info screen or sheet (not a dangling icon).
- **Actor-symmetry law:** any feature where one actor acts ON another needs BOTH surfaces designed: the actor's (admin/owner) AND the affected member's. Example: an admin can suspend a member, so the member's own screen showing the suspension must exist too. The admin side drawn without it = FAIL.
- **Destructive/irreversible law:** delete / remove / ban / leave / reset needs a confirm state designed. The "after" (toast, empty state, updated list) needs to exist too.
- Output an **action -> outcome map** in the gate result. Orphans are blockers, not warnings.

This is mechanical on purpose: it removes reliance on "remembering to design the whole flow". Complete this check before declaring the affected flow complete; evidence collection order is not itself a gate.

### 16. Hand-crafted surface (client/owner-facing files)

Calibrated on a client handoff (field note, 2026-07). Rule: nothing in a delivered handoff may look machine-made; every surface must read as hand-crafted. In a file that a client, owner or external stakeholder will open:

- **Zero process log on the canvas:** no QA log, no fix list, no "adversarial pass", no "sprint", no session changelog. Process notes (QA log, fix list) live outside the Figma file, in a project file of your choice or in the agent's own memory system if it has one, never in a visible frame.
- **Zero mention of a review or AI tool:** ChatGPT, "external review/judgment", skill or pipeline names. A recommendation on a board is written in the designer's voice ("my recommendation is..."), never "reviews recommend".
- **Layout grids OFF** on every delivered frame. Clones inherit visible grids and the canvas takes on an assembly-line look. Hide the grids and keep their definitions by reassigning a modified copy, the same clone-mutate-reassign pattern as fills (see [`figma-canon/references/plugin-api-core.md`](../../figma-canon/references/plugin-api-core.md)): `frame.layoutGrids = frame.layoutGrids.map(g => ({ ...g, visible: false }))`.
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

and confirm that the screens you are going to present are in the result. Flow starting points belong to a page, and `figma.currentPage` is whatever page is active, which another session or the designer can switch. Make sure the page that holds the prototype is the active one first (re-assert it from a known node, as in "findAllWithCriteria runs on figma.currentPage" in [`figma-canon/references/plugin-api-anomalies.md`](../../figma-canon/references/plugin-api-anomalies.md)).

**17c. Verify recipient use.** Test or inspect the relevant recipient path and report defects or limits, without a required written thought exercise:

- They press Play and land where?
- Do they find the section, or is it 30 thousand pixels of scroll?
- Does the text I wrote match what they see?
- What new question does this screen create that the file does not answer?
- If the artifact offers more than one alternative, can they decide, or did it become a menu with no bet?
