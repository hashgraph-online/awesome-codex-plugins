# Experience Rules

Read only sections selected by `SKILL.md`. Apply them to the affected task and
accepted project requirements; this reference does not own routing or approval.

## User effort and task structure

- Start with the user's outcome and relevant users, including occasional and
  expert use where applicable. Internal data models and conversion metrics do
  not substitute for that outcome.
- Compare understanding, decisions, input/navigation, waiting, and recovery.
  A dense one-screen form can cost more effort than a clear multi-step flow.
  Optimize the complete task, including correcting, cancelling, and exiting.
- Reuse valid information already supplied during the flow. Derive reasonable
  defaults where permitted; make consequential defaults understandable and
  overridable. Do not expose internal choices the system can reliably resolve.
- Ask for information when useful. Reveal advanced choices when needed while
  keeping important requirements and consequences discoverable.
- Remove a confirmation only when the action's consequences, reversibility,
  or equivalent safeguards support it. Permanent or costly actions need a
  proportionate way to review/correct, prevent error, or recover. Fewer clicks
  do not justify losing informed control or shifting effort to recovery.
- For competing flows, state the expected effort change and what user/task
  evidence would falsify it. Keep an untested improvement claim provisional.

## Visual hierarchy and consistency

- Reuse the project's design tokens and component variants. When none exist,
  choose a coherent provisional direction for this scope; seek preference only
  when it changes product behavior or the accepted visual direction.
- Make the task's entry, primary action, supporting information, and result
  distinguishable. Use typography, spacing, grouping, alignment, and contrast
  deliberately; avoid competing emphasis without a task reason.
- Keep the meaning of controls, icons, colors, and status presentation
  consistent across related screens. Inspect existing components before adding
  a parallel component or token owner.
- Verify composition and information density with realistic long/short text,
  representative data, missing images, and the supported languages/themes
  affected by the change. A polished empty/demo screen is insufficient.
- Treat visual refinement and brand expression as explicit project targets.
  If a maturity label is used, verify its dimensions separately; strong visuals
  cannot compensate for a broken journey or inaccessible control.

## Interaction states and recovery

- Select states relevant to the operation: initial, loading, empty, partial,
  disabled, success, validation error, failure, cancel, and retry. Do not add
  states with no scenario evidence, or verify only the happy path.
- Keep action feedback understandable and associated with its control or
  result. Prevent duplicate side effects where repeated submission is possible.
- Explain errors with an actionable next step. Preserve valid input and work
  across validation/server failures and relevant back/cancel transitions;
  respect sensitive-data handling requirements.
- Distinguish retryable failure, invalid input, permission denial, and partial
  success when they need different recovery. Do not blindly retry an operation
  whose outcome is unknown or repeat a completed destructive side effect.
- Include the actual API response/state contract when a backend change affects
  visible errors, loading, displayed data, or recovery. UI-file changes are not
  the only trigger for these checks.

## Inclusive use and device conditions

- Use semantic controls, meaningful labels/accessible names, suitable focus
  behavior, and keyboard operation for the affected interaction. Feedback must
  remain understandable without color alone or pointer-only interaction.
- Check applicable contrast, text resizing/reflow, target usability, and
  alternatives to motion or gesture under the project's accessibility target.
  Use the relevant platform standard instead of inventing universal thresholds.
- Verify supported viewport sizes, zoom, input methods, content length,
  languages, and assistive-technology scope affected by the change. Check
  overflow, truncation, obscured actions, and focus after dynamic updates.
- Automated checks cover a subset of accessibility; report manual and user
  testing gaps. A generic "accessible" claim needs an explicit scope and evidence.

## Waiting and performance experience

- Set latency/layout-stability acceptance from the affected task and project
  budget. Measure under stated conditions; avoid universal unsupported targets.
- Show meaningful progress or status for noticeable work. Preserve context;
  offer cancellation when supported, and explain an unavailable action.
- Evaluate skeletons, animation, and optimistic updates by clarity and actual
  outcome. Account for failure/reconciliation and motion preferences; decorative
  feedback does not prove an operation has completed.

## Source references

These are supporting sources, not a mandatory external read-set or project
authority. Read a relevant criterion only when the task needs its exact scope.

- [GOV.UK: make the service simple to use](https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use)
- [GOV.UK Design System contribution criteria](https://design-system.service.gov.uk/community/contribution-criteria/)
- [WCAG 2.2 quick reference](https://www.w3.org/WAI/WCAG22/quickref/)
- [WCAG: redundant entry](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html)
- [WCAG: error prevention](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html)
