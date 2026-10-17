---
name: forgiveness-undo-and-soft-delete
description: 'Use this skill when designing reversibility — undo systems, soft delete, archive-with-recovery, version history, "Undo Send" patterns, and any mechanism that lets a user step back from an action they regret. Trigger when designing destructive actions you want to be safe rather than friction-heavy, when picking between confirmation dialogs and undo toasts, when defining recovery windows, or when planning version-history features. Sub-aspect of `forgiveness`; read that first.'
---

# Forgiveness through reversibility

Reversibility is the highest-leverage form of forgiveness short of structural prevention. It makes destructive actions safe by allowing recovery — users keep speed (no friction up front) and safety (the action is undoable). Whenever an action *can* be made reversible, that's almost always preferable to confirming it.

## The reversibility ladder

Different actions need different reversibility approaches:

### Synchronous undo (Cmd-Z)

The classic. The user takes an action; pressing Cmd-Z (or Ctrl-Z) reverses it. Multi-level undo lets the user back out through a sequence of actions.

**When it applies:** editing operations on a single object — text editing, image manipulation, design tool actions, code edits.

**Implementation pattern:**
- Maintain an undo stack of inverse operations.
- On each action, push the inverse onto the stack.
- On Cmd-Z, pop and apply the inverse.
- On any new action after undo, optionally clear the redo stack (or maintain redo separately).

```js
const undoStack = [];
const redoStack = [];

function executeAction(action) {
  action.do();
  undoStack.push(action);
  redoStack.length = 0;
}

function undo() {
  const action = undoStack.pop();
  if (!action) return;
  action.undo();
  redoStack.push(action);
}

function redo() {
  const action = redoStack.pop();
  if (!action) return;
  action.do();
  undoStack.push(action);
}
```

### Toast-with-undo (the modern default for one-off destructive actions)

The user takes an action that destroys or moves data; a toast appears with an "Undo" button for several seconds.

**When it applies:** archive, delete, move-to-folder, mark-read, and similar one-shot list actions.

**Implementation pattern:**
- Optimistically update the UI (item disappears).
- Send the destructive request to the server (or defer it for the undo window).
- Show a toast with an Undo affordance for 5–10 seconds.
- On Undo: reverse the optimistic update, cancel/reverse the server action.
- On timeout: commit the action permanently.

```js
async function archive(item) {
  const previous = items.slice();
  items = items.filter(i => i.id !== item.id);
  render();

  let undone = false;
  showToast(`"${item.name}" archived`, {
    action: { label: 'Undo', onClick: () => { undone = true; items = previous; render(); } },
    duration: 7000,
    onDismiss: () => { if (!undone) api.commitArchive(item.id); }
  });
}
```

The user gets the speed of "click and it happens" plus the safety of "you have 7 seconds to undo."

### Soft delete with explicit recovery

A delete that doesn't actually remove the data — instead moves it to a recoverable state for some window (30 days, indefinitely, until storage cleanup).

**When it applies:** account-level data the user might want back later; emails, documents, files. Common in B2B SaaS.

**Implementation pattern:**
- Mark the item as deleted with a timestamp.
- Hide it from default views.
- Provide a "Trash" or "Archive" view where deleted items can be restored.
- After the recovery window, hard-delete via background job.

```js
// Soft delete
async function softDelete(item) {
  await api.update(item.id, { deletedAt: new Date(), deletedBy: currentUser.id });
}

// In default queries
const visibleItems = items.filter(i => !i.deletedAt);

// Recovery view
const trashedItems = items.filter(i => i.deletedAt && daysAgo(i.deletedAt) < 30);

async function restore(item) {
  await api.update(item.id, { deletedAt: null, deletedBy: null });
}
```

### Version history

The strongest reversibility: every state of the object is preserved; the user can return to any prior state.

**When it applies:** documents, code, designs, configurations — anything users edit over time and might want to revert.

**Implementation pattern:**
- Snapshot the object on each meaningful change (or at intervals, or on explicit save).
- Provide a "Version history" UI listing past states.
- Allow viewing, restoring, or branching from any prior version.

Google Docs, Notion, Figma, GitHub all implement this. The user never fears editing because they can always restore.

### The "Undo send" pattern

Gmail's pattern: an action that *appears* committed actually defers for a few seconds, allowing cancellation in that window.

**When it applies:** actions that the user often regrets immediately after triggering — sending an email, posting publicly, sending a message.

**Implementation pattern:**
- On "Send," show "Sending..." with an Undo affordance for N seconds.
- Don't actually transmit until N seconds elapse with no Undo.
- On Undo, return to draft state.

The user feels they sent it; the system just defers commitment briefly. The defer window is short (5–30 seconds) — long enough to catch reflexive "wait!" moments, short enough not to delay genuine sends.

## Choosing the right reversibility approach

| Action type | Recommended reversibility |
|---|---|
| Text/edit/format change | Synchronous undo (Cmd-Z) |
| Archive / soft delete one item | Toast-with-undo |
| Hard delete / account changes | Soft delete + recovery view |
| Document edits | Version history + Cmd-Z |
| Send / publish / post | Undo-send window |
| Bulk destructive | Soft delete + bulk-restore in trash |

## When reversibility isn't possible

Some actions genuinely can't be reversed at the data layer:

- **External communications** (sent emails, sent SMS, public tweets) — the recipient already saw it.
- **Financial transfers** — money has moved.
- **Compliance / legal commits** — once signed, signed.
- **Hardware operations** — once a physical command goes to a robot or printer, it's done.

For these, lean on the next-strongest forgiveness levels: structural prevention (good affordances), confirmation (deliberate intent), and warnings.

The "Undo send" pattern bridges this for some communications: the *external* action is still irreversible, but the system delays it long enough for the user to catch second thoughts.

## Recovery window length

For toast-with-undo: 5–10 seconds is the typical range.

- < 5 seconds: too short for users who realized after a moment of reflection.
- 5–7 seconds: covers most reflexive corrections.
- 10+ seconds: lingers; some users dismiss the toast before reading it.

For soft delete: 7–30 days is typical.

- 7 days: balances storage cost with user recovery needs.
- 30 days: standard for most SaaS; forgiving enough for vacations and weekends.
- Indefinite: storage cost grows but maximum forgiveness.

## Discoverability of recovery

A reversibility mechanism that users don't know exists doesn't help. Patterns:

- **Toast affordance** is its own discovery — users see the Undo button and learn the pattern.
- **"Trash" or "Archive" navigation entry** signals that deleted items can be recovered.
- **Onboarding mention** for version history ("All changes saved. View history at any time.").

If users are filing tickets to recover data they could have restored themselves, the recovery affordance isn't visible enough.

## Anti-patterns

- **Toast that vanishes too fast.** A 2-second toast with an Undo button most users never see.
- **Soft delete with no recovery UI.** Items go to a "trash" the user can't access.
- **Version history that's hidden.** Buried under three menu levels; users don't know it exists.
- **Cmd-Z that doesn't undo destructive actions.** Some apps undo formatting but not deletion. Inconsistent.
- **Undo that fails silently.** Click Undo; nothing happens; no error; user is confused. If undo fails, say so.

## Heuristics

1. **The "did they recover?" check.** Look at support tickets for data loss. Each one is a reversibility failure.
2. **The toast-button audit.** For every destructive action, is there a toast with Undo? If not, why not?
3. **The trash audit.** Is there a Trash / Archive / Recycle Bin in your app? If items can be deleted but there's no recovery view, you're missing soft delete.

## Related sub-skills

- **`forgiveness`** (parent).
- **`forgiveness-confirmation-and-prevention`** — the alternative when reversibility isn't possible.
- **`feedback-loop`** — toast-with-undo is feedback that doubles as reversibility.
- **`factor-of-safety`** (process) — engineering analog of "design with margin so errors are recoverable."
