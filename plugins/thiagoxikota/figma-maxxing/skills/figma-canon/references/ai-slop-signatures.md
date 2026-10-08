# AI-slop signatures

Load during write, audit and pre-ship gates. AI-slop detection patterns: generic spacing cocktails, hype copy, WCAG fails, default names, detached instances, hardcoded values, decorative cocktails.

Detection patterns. Used by the `figma-slop-check` and `figma-handoff-gate` skills, and by the optional precheck hook (`hooks/figma-canon-precheck.py`).

## Visual cocktail signature (model training prior)

The "I default to median web UI" cocktail, a model's training prior: the defaults it falls back to when no design system constrains it.

- 12px gap + 16px padding + 8px radius + soft drop-shadow defaults
- Lavender/purple gradient backgrounds
- Generic "elevated card" with all four edges rounded equally
- Stack of colored callouts (red/blue/green status): a known anti-pattern

When you see ALL of these together, it is almost certainly AI freestyle. Flag for replacement with DS-bound values.

## Hype copy ban (generic AI words)

Forbidden in delivered copy:

- "Empower"
- "Best-in-class"
- "Seamlessly" / "Seamless"
- "Intuitive"
- "Powerful"
- "Robust"
- "Elevate"
- "Unlock"
- "Revolutionary"
- "Game-changing"
- "Cutting-edge"
- "Next-generation"
- "Innovative"

These flag for rewrite. Replace with concrete user-value statements.

## WCAG auto-fails

Drops to score 0 immediately. Not every line below is a WCAG AA criterion: the text size floor is this canon's own threshold. When you report one of them, cite this canon rather than WCAG.

- Body text contrast <4.5:1
- UI component contrast <3:1
- Text size <12px for UI, <16px for body
- Color-only conveyance of state (red text without icon/label)
- Missing focus indicators on interactive variants

## Component reuse failures

- Default Figma names in delivered screens: `Frame N`, `Group N`, `Rectangle N`, `Vector N`, `Ellipse N`, `Text N`. AUTO-FAIL.
- Detached instance of a published component without justification: flag
- New `Button` drawn when `Button/Primary` exists: flag
- New `Card` drawn when `Card/*` exists: flag
- New `Input` drawn when `Input/*` exists: flag
- Recreating an icon as vectors when `Icon/*` exists: flag

## Token violations

- Hardcoded hex in fills/strokes when variables exist: flag. Never hardcode a hex where a variable covers the value (the optional precheck hook flags this pattern).
- Hardcoded font sizes outside the type scale: flag
- Hardcoded corner radius outside the radius token set: flag
- Hardcoded spacing values when spacing tokens exist: flag
- Effect styles inline when elevation/shadow tokens exist: flag

## Layout & positioning

- Top-level node at (0,0) colliding with existing content: flag
- Manual X/Y positioning inside an auto layout parent: flag
- Auto layout missing on a multi-child container: flag
- `layoutSizing*=FILL` set before `appendChild`: flag (silent FIXED)
- `resize()` called AFTER sizing modes are set: flag (resets sizing)

## Decorative excess

- Corner radius >16px on standard cards (excessive softness)
- Drop shadow + heavy border + gradient bg (overdesigned)
- Gradient backgrounds when the DS uses solid colors
- Multiple competing focal points on one screen
- Excessive icon decoration without semantic purpose

## Sibling-check rule

BEFORE flagging a card as slop / inconsistent / dead-space:

1. Inspect at least 2 siblings of the same class on the canvas
2. Compare structure, spacing, content density
3. The flagged item often IS canon: your call is the bug

Do not make slop calls without sibling evidence.

## Card and state anti-patterns

Built on one production project and generic enough to apply anywhere. A project's own anti-pattern list lives in its project map (`figma-map.md`).

- Glass effects on full-screen opaque cards: use a solid surface color from the project's tokens instead
- Status emoji in every state: minimize
- Cards verbose with redundant info: trim to essence
- Stack of colored callouts: use the project's actual hierarchy instead

## Self-corrections in reports

Do not expose your own audit/fix process in stakeholder reports:

- BAD: "I noticed and fixed X" / "Audit caught Y" / "Round 8 corrected Z"
- GOOD: just describe the fix's value, drop the process bullets

## Multi-pass verification flag

When the user asks to fix everything, or asks whether everything was verified, multi-pass is mandatory. A single pass misses ~80% of contradictions. Show the verification: the search you ran (grep or equivalent) and its count of remaining hits, which must be zero. Do not claim "done" on a single pass.

## Subagent fan-out caveat

For audit work with a shared evidence base: prefer a single-agent close read over a parallel fan-out to subagents (a feature of the agent runtime, such as Claude Code, not of Figma). Field note: 4 parallel agents derailed, while a single agent produced 24 evidence-cited findings.

## Severity scoring

This table sets the severity of a finding and its action. `Block` = the gate does not pass until the pattern is fixed (the optional precheck hook only warns by default). Whether work can be declared done also follows the 5 auto-fails of `references/quality-rubric.md`: hardcoded colors, missing auto layout and detached components are auto-fails there, even though this table only flags them.

| Pattern | Severity | Auto-action |
|---|---|---|
| WCAG auto-fail | Critical | Block |
| Default Figma names | Critical | Block |
| Detached instance | High | Flag |
| Hardcoded hex/spacing | High | Flag (the optional precheck hook flags hardcoded hex) |
| Auto layout missing | High | Flag |
| Hype copy | Medium | Rewrite |
| Decorative excess | Medium | Trim |
| Multi-pass needed | Medium | Re-run |
| (0,0) collision | Low | Reposition |
