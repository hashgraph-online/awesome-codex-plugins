# Slip prevention: patterns and case reference

A reference complementing `errors-slips` with patterns and case studies.

## Common slip-prone interfaces

- **Email send**: Reply All slips; wrong-recipient slips; forgot-attachment slips.
- **Delete buttons**: clicking when meaning to archive.
- **Form submit**: pressing Enter prematurely; double-clicking submit.
- **Multi-tab navigation**: switching tabs in middle of a workflow.
- **Modal dialog dismissal**: clicking the wrong button on autopilot.
- **Drag-and-drop**: dropping in the wrong container.

## Patterns that work

### Distinct affordances

```html
<!-- Both buttons are clearly buttons; their roles are visually distinct -->
<button class="btn-secondary">Cancel</button>
<button class="btn-destructive">Delete project</button>
```

### Defensible space

Position destructive controls away from frequent ones. The "Delete account" button lives in a "Danger zone" panel at the bottom of settings, not next to "Save profile."

### Recovery affordances

Most modern destructive actions support undo:

```js
async function archive(item) {
  const previous = items.slice();
  items = items.filter(i => i.id !== item.id);
  showToast(`"${item.name}" archived`, {
    action: { label: 'Undo', onClick: () => { items = previous; render(); } },
    duration: 7000
  });
}
```

### Forgot-attachment heuristics

Gmail, Outlook, and similar email clients scan body text for "attached," "attachment," and similar words. If found and no attachment exists, prompt before sending.

### Two-step destructive flows

For irreversible actions: a click opens a dialog with type-to-confirm. The user types the resource name; only then is the destructive button enabled.

### Auto-save against losing work

Any form longer than ~5 fields benefits from auto-save. The user navigating away by mistake doesn't lose progress.

## Cross-domain slip prevention

### Aviation: sterile cockpit rule

Below 10,000 feet, only essential conversation in the cockpit. Reduces attention slips during high-workload phases (takeoff, landing).

### Medicine: barcoded medication administration

The nurse scans both the patient wristband and the medication. Wrong-patient or wrong-drug slips are blocked at the scan.

### Industrial: dual-key authorization

For hazardous operations, two operators must turn keys simultaneously. A single-person slip can't trigger the action.

### Software: keyboard-shortcut conflicts

Modern apps avoid global keyboard shortcuts for destructive actions. Cmd-Z is widely safe (undo); Cmd-Delete is more destructive but typically also reversible.

## Resources

- **Gawande, A.** *The Checklist Manifesto* (2009).
- **Norman, D.** *The Design of Everyday Things* (2013).
- **NN/g articles** on confirmation, undo, and form-design slip prevention.
