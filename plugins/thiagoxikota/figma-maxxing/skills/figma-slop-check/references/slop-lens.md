# slop lens

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

## Lens 1: Slop (does it look machine made)

Run the checks that apply to what was made: design (S1 to S6), copy (S7), reply (S8).

### S1. Overlap and spacing integrity

- No frame, card or element overlaps another.
- Free-positioned frames stacked in a column leave room for the frame-name label that Figma draws above each frame: no label lands on the frame above it.
- A caption or annotation beside a frame sits at least 32px from it.
- The internal padding of a card is at least 16px.
- The section background is distinct from the frame background.

Detect: take a screenshot of the whole section at scale 0.4 and review it. In a handoff section built with right-side annotations, the stricter spacing constants of [`figma-canon/references/handoff-format.md`](../../figma-canon/references/handoff-format.md) apply.

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

Detect: scan the top-level names of the page for emoji, codenames and dates. The expected count is zero. Before creating a section or a note, ask: would a designer in a hurry write this? Full rule: the Human authorship section of [`figma-canon/references/naming-canon.md`](../../figma-canon/references/naming-canon.md).

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
- **Sample data:** no realistic creator-style handle (a first name plus a vibe word, or a first name plus an initial). Two rules conflict on the replacement: the field slop rule offers neutral i18n handles such as `@user_001`, while [`figma-canon/references/handoff-format.md`](../../figma-canon/references/handoff-format.md) bans `@user_NNN` placeholders and asks for realistic names in the file's language. The project map decides; if it is silent, ask the designer.
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
