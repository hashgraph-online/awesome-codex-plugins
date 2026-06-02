# Codebase to Course Design System

This runtime uses a warm notebook visual language intended for direct browser-open reading, offline packaging, and shell-based page assembly.

## Goals

- Feel like a taught-through workbook, not a product dashboard.
- Keep code, diagrams, quizzes, and prose inside one coherent visual grammar.
- Use local and system font stacks only.
- Work without network access, bundlers, or remote assets.
- Stay simple enough that build scripts can assemble pages by string replacement.

## Shell Templates

The runtime shell is split into two generic partials:

- `runtime/templates/_base.html`
- `runtime/templates/_footer.html`

Both use plain `{{TOKEN_NAME}}` placeholders so shell scripts can replace them with `sed`, `perl`, `envsubst`, or similar local tooling.

Required placeholders:

- `{{PAGE_LANG}}`
- `{{PAGE_TITLE}}`
- `{{PAGE_DESCRIPTION}}`
- `{{RUNTIME_STYLESHEET}}`
- `{{RUNTIME_SCRIPT}}`
- `{{COURSE_TITLE}}`
- `{{COURSE_CONTENT}}`

Common optional placeholders:

- `{{HEAD_EXTRA}}`
- `{{BODY_CLASS}}`
- `{{COURSE_EYEBROW}}`
- `{{COURSE_KICKER}}`
- `{{COURSE_DEK}}`
- `{{COURSE_META}}`
- `{{COURSE_APPENDIX}}`
- `{{FOOTER_NOTE}}`
- `{{FOOTER_META}}`
- `{{BODY_END}}`

The shell intentionally does not assume a specific lesson structure beyond:

1. Masthead
2. Main content
3. Optional appendix
4. Footer

## Typography

The system uses three local stacks:

- Display: `Iowan Old Style`, `Palatino Linotype`, `Book Antiqua`, `Palatino`, `Georgia`, `serif`
- Body: `Avenir Next`, `Segoe UI`, `ui-sans-serif`, `system-ui`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif`
- Code: `SFMono-Regular`, `Cascadia Mono`, `Liberation Mono`, `Menlo`, `Consolas`, `monospace`

Typography rules:

- Large explanatory headings should use the display stack.
- Longform prose, controls, and metadata should use the body stack.
- Code, inline flags, config keys, and file paths should use the code stack.
- Avoid center-aligned multi-line body text. The runtime is optimized for scanability.

## Color System

The palette is paper-first with one warm accent and one cool balance color.

- Paper base: `#f6efe1`
- Bright paper: `#fffaf0`
- Ink: `#2f251d`
- Muted text: `#6e6357`
- Accent orange: `#c55d2d`
- Accent deep: `#8f3b18`
- Teal support: `#2f7975`
- Gold highlight: `#d59a2f`
- Error: `#b44a31`
- Success: `#44784a`

Rules:

- Use orange as the primary emphasis color.
- Use teal to separate systems, secondary flows, and linked architecture nodes.
- Use gold sparingly for milestones, highlights, and guided progression.
- Do not introduce purple as a primary accent.

## Layout Language

The page layout is intentionally editorial:

- One centered page column with generous side breathing room.
- Panels look like pinned notebook sheets rather than app cards.
- Top borders use a short accent strip to give larger interactive blocks clear entry points.
- Repeating ruled lines in the page background reinforce the notebook feel without dominating content.

Recommended content rhythm:

- Alternate explanatory prose with one interactive or diagrammatic block.
- Keep dense multi-column layouts to desktop widths only.
- Collapse to one column on narrow screens.

## Surface Rules

Primary surfaces:

- `course-masthead`
- `course-footer`
- `data-translation-block`
- `data-quiz`
- `data-scenario-quiz`
- `data-match`
- `data-chat-demo`
- `data-flow-demo`
- `data-architecture`
- `data-layer-demo`
- `data-bug-hunt`
- `data-callout`
- `data-pattern-card`
- `data-feature-card`

Surface rules:

- Rounded corners should feel tactile, not bubble-like.
- Borders are soft and warm, never pure gray.
- Shadows should lift surfaces slightly off the paper background, not simulate floating glass.
- The code panel is the only intentionally dark surface.

## Motion

Motion is purposeful and low-frequency:

- Reveal-on-scroll: `data-reveal`
- Sequential chat playback: `data-chat-demo`
- Step-through flow animation: `data-flow-demo`
- Layer emphasis: `data-layer-demo`

Motion rules:

- Use motion to clarify order, not to decorate every control.
- Preserve a readable still state when JavaScript is disabled.
- Respect `prefers-reduced-motion: reduce`.

## State Vocabulary

The runtime uses a small shared state vocabulary across components:

- `is-selected`
- `is-active`
- `is-linked`
- `is-muted`
- `is-visible`
- `is-correct`
- `is-incorrect`
- `is-over`
- `is-hidden`
- `is-emphasized`

These classes are runtime-managed. Author content should not hard-code them in source HTML unless producing a static fixture snapshot.

## Accessibility and Offline Rules

- No remote fonts, icon packs, scripts, or images are required.
- Every interactive control should still be understandable in static HTML.
- Hidden panels use the native `hidden` attribute.
- Buttons are real `<button>` elements whenever interaction is expected.
- Tooltips and reveal panels must not be the sole place where essential course content lives.
- The shell includes a skip link and a focusable main landmark.

## Component Families

The system is organized into three families:

### 1. Guided teaching blocks

- Translation blocks
- Callouts
- Pattern cards
- Feature cards
- Icon rows
- Numbered step cards

### 2. Interactive reasoning blocks

- Multiple-choice quiz
- Scenario quiz
- Drag-and-drop matching
- Spot-the-bug challenge
- Layer toggle demo

### 3. Systems explanation blocks

- Group chat animation
- Message/data flow animation
- Interactive architecture diagram
- Flow diagrams
- Visual file tree
- Permission/config badges
- Glossary tooltips

## Authoring Guidance

- Prefer short, inspectable attribute names over framework-specific conventions.
- Keep each block self-describing from its root `data-*` attribute.
- Use prose around interactions to explain why the block exists.
- Do not build hidden logic into CSS class names alone. Keep behavior keyed off `data-*`.
- If a lesson can work without JavaScript, author it so the no-JS version remains legible first.

## Minimal Lesson Skeleton

```html
<section class="course-surface" data-reveal>
  <p class="course-section__eyebrow">Execution Path</p>
  <h2>How a request moves through the codebase</h2>
  <p>Start with the main entrypoint, then zoom into state changes and side effects.</p>
</section>

<section data-translation-block data-default-view="split">
  ...
</section>

<section data-flow-demo data-default-step="0">
  ...
</section>
```

Use the runtime as a teaching substrate, not a page builder theme. The page should still read well when every interactive block is paused.
