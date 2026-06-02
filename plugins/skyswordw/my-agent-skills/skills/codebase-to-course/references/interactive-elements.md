# Codebase to Course Interactive Elements

This document defines the runtime contract for authoring course content. Each block is keyed by one root `data-*` attribute, uses a small shared state vocabulary, and is intended to remain readable when opened directly from disk.

## Shared Conventions

- Put one primitive per root container.
- Use real `<button>` elements for clickable controls.
- Runtime-managed state classes:
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
- Runtime readiness marker:
  - `data-runtime-ready="true"` is added to the course root after initialization.
- Optional reveal-on-scroll:
  - Add `data-reveal` to any section-sized block.

## 1. Code to English Translation Block

Root:

- `data-translation-block`

Required children:

- `data-translation-panels`
- one `data-translation-panel="code"`
- one `data-translation-panel="plain"`

Optional controls:

- `data-translation-toolbar`
- `data-translation-toggle="code"`
- `data-translation-toggle="plain"`
- `data-translation-toggle="split"`

Optional root attributes:

- `data-default-view="code|plain|split"`

Behavior:

- Runtime sets `data-view` on the root.
- In split view, both panels remain visible.
- In single view, the non-selected panel is hidden with `hidden`.

Example:

```html
<section data-translation-block data-default-view="split">
  <div data-translation-toolbar>
    <button type="button" data-translation-toggle="code">Code</button>
    <button type="button" data-translation-toggle="plain">English</button>
    <button type="button" data-translation-toggle="split">Both</button>
  </div>
  <div data-translation-panels>
    <article data-translation-panel="code"><pre><code>main()</code></pre></article>
    <article data-translation-panel="plain"><p>This function starts the app and wires dependencies.</p></article>
  </div>
</section>
```

## 2. Multiple-Choice Quiz

Root:

- `data-quiz`

Required attributes:

- `data-quiz-answer="option-id"`

Required children:

- one or more `data-quiz-option="option-id"`

Optional children:

- `data-quiz-submit`
- `data-quiz-reset`
- `data-quiz-feedback`
- `data-quiz-response="option-id"`

Optional root attributes:

- `data-quiz-mode="instant|submit"`
- `data-quiz-success="..."`
- `data-quiz-failure="..."`

Behavior:

- Clicking an option marks it selected.
- In `instant` mode, evaluation happens on selection.
- In `submit` mode, evaluation waits for `data-quiz-submit`.
- Matching `data-quiz-response` panels are shown by selected option id.

## 3. Drag-and-Drop Matching

Root:

- `data-match`

Required children:

- `data-match-bank`
- one or more `data-match-token="token-id"`
- one or more `data-match-slot`

Required slot attributes:

- `data-accept="token-id"` or a comma/space-separated list of acceptable ids

Optional children:

- `data-match-check`
- `data-match-reset`
- `data-match-feedback`
- `data-match-placeholder`

Behavior:

- Tokens can be dragged into slots.
- Clicking a token then a slot also assigns it.
- Clicking a filled slot without a selected token returns the token to the bank.
- `data-match-check` compares assigned tokens to `data-accept`.

Example:

```html
<section data-match>
  <div data-match-layout>
    <div data-match-bank>
      <button type="button" data-match-token="parser">Parser</button>
      <button type="button" data-match-token="renderer">Renderer</button>
    </div>
    <div data-match-targets>
      <div data-match-slot data-accept="parser">
        <strong>Reads syntax tree</strong>
        <span data-match-placeholder>Drop the right module here.</span>
      </div>
      <div data-match-slot data-accept="renderer">
        <strong>Turns state into pixels</strong>
        <span data-match-placeholder>Drop the right module here.</span>
      </div>
    </div>
  </div>
  <div class="course-controls">
    <button type="button" data-match-check>Check matches</button>
    <button type="button" data-match-reset>Reset</button>
  </div>
  <p data-match-feedback></p>
</section>
```

## 4. Group Chat Animation

Root:

- `data-chat-demo`

Required children:

- `data-chat-thread`
- one or more `data-chat-message`

Useful message attributes:

- `data-speaker="guide|learner|system"`
- `data-chat-delay="milliseconds"`

Optional controls:

- `data-chat-play`
- `data-chat-reset`
- `data-chat-status`

Optional root attributes:

- `data-chat-interval="milliseconds"`
- `data-autoplay="true|false"`

Behavior:

- Messages reveal sequentially by DOM order.
- `data-chat-delay` overrides the root interval for a message.
- The runtime only adds `is-visible`; it does not mutate message text.

## 5. Message or Data Flow Animation

Root:

- `data-flow-demo`

Required children:

- one or more `data-flow-item="id"`
- one or more `data-flow-step`

Required step attributes:

- `data-flow-targets="space-separated ids"`

Useful optional step attributes:

- `data-flow-caption="human-readable explanation"`

Optional controls:

- `data-flow-prev`
- `data-flow-next`
- `data-flow-play`
- `data-flow-reset`
- `data-flow-caption-output`

Optional root attributes:

- `data-default-step="0-based index"`
- `data-flow-interval="milliseconds"`
- `data-flow-intro="initial caption"`
- `data-autoplay="true|false"`

Behavior:

- The active step gets `is-active`.
- Matching `data-flow-item` nodes get `is-active`.
- Non-targeted items receive `is-muted`.
- `data-flow-caption` stays reserved for per-step metadata, while `data-flow-caption-output` is the live status node updated by the runtime.

Authoring note:

- Use `data-flow-role="edge"` on connector items when you want edge styling.

## 6. Interactive Architecture Diagram

Root:

- `data-architecture`

Required children:

- one or more `data-architecture-node="node-id"`
- one or more `data-architecture-panel="node-id"`

Useful optional children:

- `data-architecture-focus="node-id"`

Useful optional node attributes:

- `data-links="space-separated node ids"`

Optional root attributes:

- `data-default-node="node-id"`

Behavior:

- Selecting a node marks it `is-active`.
- Nodes named in `data-links` on the active node receive `is-linked`.
- Non-selected and non-linked nodes may receive `is-muted`.
- Only the matching `data-architecture-panel` stays visible.

## 7. Layer Toggle Demo

Root:

- `data-layer-demo`

Required children:

- one or more `data-layer="layer-id"`
- one or more `data-layer-toggle="layer-id"`

Optional children:

- `data-layer-summary`

Optional root attributes:

- `data-hidden-layers="space-separated layer ids"`
- `data-layer-summary-prefix="custom summary text"`

Behavior:

- Toggling a layer applies or removes `is-hidden`.
- If exactly one layer remains visible, that layer gets `is-emphasized`.
- Summary text is updated if `data-layer-summary` exists.

## 8. Spot-the-Bug Challenge

Root:

- `data-bug-hunt`

Required attributes:

- `data-bug-answer="marker-id"`

Required children:

- one or more `data-bug-choice="marker-id"` or `data-bug-marker="marker-id"`

Optional children:

- `data-bug-submit`
- `data-bug-reset`
- `data-bug-feedback`
- `data-bug-panel="marker-id"`

Behavior:

- Choice buttons and inline markers both target the same answer ids.
- The selected line or choice gets `is-selected`.
- Evaluation adds `is-correct` and `is-incorrect`.
- The selected explanation panel is shown with `hidden` removed.

Authoring note:

- Inline markers are ideal when the code block contains obvious suspicious fragments.
- Choice buttons are better when you want learners to compare named failure modes.

## 9. Scenario Quiz

Root:

- `data-scenario-quiz`

Required attributes:

- `data-scenario-answer="option-id"`

Required children:

- one or more `data-scenario-option="option-id"`

Optional children:

- `data-scenario-submit`
- `data-scenario-reset`
- `data-scenario-feedback`
- `data-scenario-panel="option-id"`

Optional root attributes:

- `data-scenario-mode="instant|submit"`
- `data-scenario-success="..."`
- `data-scenario-failure="..."`

Behavior:

- Same selection and reveal contract as `data-quiz`.
- Use it when the answer needs consequence-oriented framing rather than fact recall.

## 10. Callout Boxes

Root:

- `data-callout`

Optional attributes:

- `data-tone="warning|success|info"`

Behavior:

- Purely presentational.
- Works without JavaScript.

Recommended usage:

- Warning: pitfalls, edge cases, unsafe assumptions
- Success: confirmed patterns, green-path guidance
- Info: framing, mental models, naming explanations

## 11. Pattern and Feature Cards

Card roots:

- `data-pattern-card`
- `data-feature-card`

Grouping helpers:

- `data-pattern-grid`
- `data-feature-grid`

Behavior:

- Purely presentational.
- The runtime does not mutate these cards.

## 12. Flow Diagrams

Container:

- `data-flow-diagram`

Children:

- `data-flow-card`
- optional `data-flow-arrow`

Behavior:

- Static visual rhythm only.
- Use the interactive `data-flow-demo` when state changes over time matter.

## 13. Permission and Config Badges

Badge root:

- `data-badge-kind="permission|config"`

Recommended state values:

- `data-badge-state="required|optional|granted|enabled|disabled"`

Behavior:

- Purely presentational.
- Meant for short, high-signal labels such as scopes, env flags, or capability gates.

## 14. Glossary Tooltips

Root:

- `data-glossary`

Required children:

- `data-glossary-trigger`
- `data-glossary-tooltip`

Behavior:

- Tooltip is toggled by click.
- Runtime closes other glossary popovers before opening a new one.
- Escape closes the active tooltip.

Example:

```html
<span data-glossary>
  <button type="button" data-glossary-trigger>idempotent</button>
  <span data-glossary-tooltip hidden>Calling it twice leaves the system in the same end state.</span>
</span>
```

## 15. Visual File Tree

Container:

- `data-file-tree`

Node labels:

- `data-file-node`

Recommended node attributes:

- `data-kind="folder|file"`

Behavior:

- Purely presentational.
- Nested lists are expected and styled to show tree connectors.

## 16. Icon-Label Rows

Row root:

- `data-icon-row`

Suggested children:

- `data-icon-mark`
- `data-icon-body`

Behavior:

- Purely presentational.
- Good for key takeaways, responsibilities, and subsystem summaries.

## 17. Numbered Step Cards

Container:

- `data-step-cards`

Child cards:

- `data-step-card`

Behavior:

- Purely presentational.
- Numbering is generated with CSS counters.

## No-JS Fallback Guidance

When JavaScript does not run:

- Translation blocks still show both panels by default.
- Quizzes and scenario panels remain static unless you pre-show content in HTML.
- Matching blocks still display tokens and targets in reading order.
- Chat blocks render as a readable message log.
- Architecture, flow, and bug panels remain authored HTML; do not hide core explanations exclusively behind runtime behavior.

## Fixture Authoring Tips

- Prefer stable ids like `parser`, `store`, `event-bus`, `cache-read`.
- Keep answer ids human-readable. They appear in HTML and are easy to test with `rg`.
- Keep panel ids aligned exactly with option ids.
- Use `hidden` in source HTML for panels that should start collapsed.
- Put explanatory prose outside interactive containers when it matters to the lesson outcome.
