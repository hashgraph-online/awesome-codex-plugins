# Controls

## Optional controls, not the default sheet

A fixed ladder or matrix needs none of this; render its specimens directly. Add a
slider only when the user asks to adjust directly, or when a continuous transition
can't be judged from fixed steps, and say that purpose on the sheet. Numeric values,
a matrix, or discrete layouts (one/two/three columns) are not reasons.

Include only the controls the task needs. Label each with the property and a live
value with units (`블러 12px`), never a generic `창` or `간격`.

Selection and refinement requests still happen in chat, using the specimen letters.

**What controls may move, the whole guardrail:**

- the **window** of the axis that was ordered (which values the rungs show)
- the **context** it is judged in (background, repetition, size, content)

**Nothing else.** A colour picker on a spacing ladder turns this into a toy and the
measurement dies with it. The one exception is the blank-slate matrix: two axes by
construction, `references/sweeping.md`.

## Writing one

There is no ready-made engine. Write the smallest script the task needs, at the end of
the section's markup and before the reloader, and keep to these rules:

- **Rungs stay lettered** A, B, C in order, and every rung keeps the caption lines from
  `references/sweeping.md`. Lines 2 and 3 (what the value resolves to, what it does to
  the eye) are computed from the value, never written per letter, because the letter
  now points at whatever value is in that position.
- **The cost chip follows the value.** A rung on the project's scale reads
  `토큰 그대로`; one off it reads `--token 고침 (N곳) · 또는 새 토큰` and gets a dashed
  outline. Default the window to the project's own steps.
- **State survives a reload.** My next edit reloads the page while the user is
  mid-comparison. Keep each section's window in `sessionStorage` under
  `ctl:<section id>` and the context under `ctx`, and restore them on load.
- **One `<section>` per ladder**, appended at the end. `references/liveview.md` counts
  them.
- **Apply a class to the component, not the wrapper.** With utilities, a class put on
  the frame never reaches the component and every rung renders the same, with no error.
  Mark component nodes and set the class on each.

## Before presenting it

A sheet with controls is verified before it is shown, not after (the exception in
`references/liveview.md`, `After every edit`). Move every control to its minimum,
middle and maximum, and check that the component's computed style actually changes (Verification step 2 in `worker.md`), the captions
match, the bounds hold, and a reload restores the state. If the interaction can't be
verified, drop the slider and draw fixed candidates instead; never ship a control that
doesn't work.

## Choosing in chat

When the user has moved a window, letters refer to what is on their screen now. Read
the user's actual tab before resolving a letter; a fresh tab may have different
`sessionStorage`, and the initial values are no longer what they see. If the tab can't
be read, ask for the displayed value rather than guessing.

A boundary line written for one window is stale once the window moves. Look again and
rewrite it on the next turn; never report a boundary that no longer holds.
