---
name: errors-slips
description: 'Use this skill when designing to prevent or recover from execution errors — actions that don''t match the user''s intent. Trigger when designing critical action confirmations, distinct affordances for similar-purpose elements, recovery from wrong-button presses, "I didn''t mean to do that" flows. Sub-aspect of `errors`; read that first.'
---

# Slips: errors of execution

A slip happens when the user knew what they wanted to do but their action didn't match. The intent was right; the execution was wrong. Slips are common in routine tasks where conscious attention has lapsed: the user types "definately" instead of "definitely," clicks Reply when they meant Reply All, deletes the file they meant to keep.

The design responses for slips don't increase the user's knowledge — the user already knew what to do. They make wrong actions structurally harder, give clear feedback when they happen, and provide easy recovery.

## The two slip subtypes (from the book)

### Action slips

Wrong action despite correct intent. Triggered by:

- Routine tasks performed automatically.
- Distractions or interruptions.
- Similar-looking controls.
- Auto-pilot button-pressing on confirmations.

**Design responses**:

- **Distinctive affordances** — make destructive actions visibly different from common ones (color, position, shape).
- **Defensible space** — separate destructive controls from frequent ones (the "Cancel" near "Save" and "Delete" elsewhere).
- **Confirmation for critical tasks** — explicit confirmation step (sparingly).
- **Constraints** — make wrong actions impossible (can't submit a form with required fields empty).
- **Mappings** — controls match the layout of what they affect (stovetop knobs match burner positions).

### Attention slips

Steps missed during a procedure. Triggered by:

- Interruptions (a phone call mid-procedure).
- Long task sequences.
- Resuming a paused task.

**Design responses**:

- **Status cues** that survive interruption ("You're on Step 3 of 5").
- **Orientation aids** when resuming.
- **Alarms or alerts** for critical steps.
- **Highlighting** to focus attention on the current step.

## Common slip-prevention patterns

### Distinct destructive button styling

The destructive button differs from the safe button by color (typically red), position (typically right of the safe button in modal footers), and label (specific verb: "Delete" not "OK"). This triple-difference makes the slip harder.

```html
<div class="dialog-actions">
  <button>Cancel</button>
  <button class="destructive">Delete project</button>
</div>
```

### Type-to-confirm for irreversible actions

The user must type the resource name to enable the destructive button. Breaks autopilot Enter-pressing.

```html
<p>To confirm, type <strong>Acme Inc</strong>:</p>
<input id="confirm" />
<button id="delete-btn" disabled>Delete Acme Inc</button>
```

### Undo for routine destructive actions

Most slips are caught immediately. A 5–10 second undo window covers them.

```js
async function archive(item) {
  const previous = items.slice();
  items = items.filter(i => i.id !== item.id);
  render();
  showToast('Archived', { undo: () => { items = previous; render(); } });
}
```

### Forgot-attachment detection

Email clients scan body text for "attached," "attachment," etc. If found and no attachment exists, prompt before sending.

### Step indicators in multi-step procedures

A visible stepper or progress indicator survives interruptions. Returning users see "you were on Step 3."

### Read-only by default for sensitive views

Power-user surfaces (admin panels) start in read-only and require explicit "Edit mode" to change values. Reduces accidental edits.

## Slip-prone contexts

Some contexts produce more slips than others:

- **Routine tasks** done many times — automatic execution is more likely to slip.
- **Interrupted tasks** — resuming at the wrong step.
- **Similar-control clusters** — adjacent buttons with similar appearance.
- **Time pressure** — fast typing, fast clicking.
- **Modal dialogs** users dismiss on autopilot.

Audit slip-prone contexts in your product; apply prevention.

## Anti-patterns

- **Identical-looking destructive and safe buttons.** Slips are inevitable.
- **Pre-selected destructive option.** Default Enter triggers destruction.
- **No undo for routine destructive actions.** Each slip is permanent.
- **Excessive confirmations for non-destructive actions.** Confirmation fatigue; users dismiss real ones too.

## Heuristics

1. **The "what slip is most likely here?" audit.** For each high-frequency action, name the slip that would happen and design against it.
2. **The post-incident slip diagnosis.** When users report mistakes, distinguish slips from mistakes. Different fixes.
3. **The undo-coverage check.** What percentage of routine destructive actions have undo? If less than 90%, you have slip exposure.

## Related sub-skills

- **`errors`** (parent).
- **`errors-mistakes`** — the other half; intentional errors driven by wrong models.
- **`forgiveness`** — recovery from slips after they happen.
- **`affordance`** — distinct affordances prevent slip-type wrong-clicks.
- **`constraint`** — structural prevention of wrong actions.
