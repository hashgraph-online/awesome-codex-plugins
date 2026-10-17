---
name: forgiveness-confirmation-and-prevention
description: 'Use this skill when the user must commit to an irreversible or high-stakes action and reversibility isn''t enough — confirmation dialogs, type-to-confirm patterns, password re-entry, two-step authentication for destructive actions, and structural prevention that makes the wrong action impossible. Trigger when designing destructive flows for genuinely-irreversible commitments, when reviewing confirmation fatigue, or when picking between a single confirm dialog and a multi-step verification. Sub-aspect of `forgiveness`; read that first.'
---

# Forgiveness through confirmation and prevention

When an action can't be made reversible, the next-best forgiveness is requiring deliberate intent. The user must take an explicit, considered step before the irreversible thing happens. The challenge: confirmation overuse trains users to dismiss it on autopilot, defeating the purpose. Confirmation must be reserved for the moments when it earns its friction.

## When confirmation is appropriate

A useful test before adding confirmation: is the action irreversible *and* high-stakes?

- **Irreversible + high-stakes** → confirm. (Account deletion, ownership transfer, large financial transaction.)
- **Reversible + high-stakes** → use undo / soft-delete instead. Confirmation here is fatigue-inducing.
- **Irreversible + low-stakes** → consider whether it should be reversible. If it must be irreversible, a light confirmation may suffice.
- **Reversible + low-stakes** → no confirmation. Just do it; let undo catch mistakes.

## Confirmation strength

Match confirmation friction to action severity:

### Light confirmation: "Yes / No" dialog

```
Cancel reservation?
[ Cancel ]   [ Cancel reservation ]
```

For actions the user clearly initiated, where the dialog mostly catches accidental clicks. The user reads the title, picks an option.

### Medium confirmation: dialog with summary

```
Delete project "Acme Q4"?

This deletes 24 tasks and 8 attached files.

[ Cancel ]   [ Delete project ]
```

For actions where the user benefits from seeing what they're about to lose. The summary gives them a chance to step back.

### Strong confirmation: type-to-confirm

```
Delete project "Acme Q4"?

This deletes 24 tasks and 8 attached files. Cannot be undone.

To confirm, type the project name below:
[ Acme Q4__________ ]

[ Cancel ]   [ Delete project ]   (button enabled only when name matches)
```

For irreversible high-stakes actions. The user must actively type the resource name, breaking autopilot. The button stays disabled until the confirmation matches.

### Strongest: re-authentication

```
This action requires re-authentication.
Enter your password to continue.

[ Password__________ ]

[ Cancel ]   [ Continue ]
```

For account-affecting actions: deleting account, changing email, transferring ownership, viewing audit logs. Re-authentication catches both autopilot mistakes and someone-else-using-my-session attacks.

## Type-to-confirm: the canonical pattern for irreversible action

```html
<dialog id="delete-dialog">
  <h2>Delete workspace "Acme Inc"?</h2>
  <p>
    This permanently deletes the workspace, all 47 projects, all 12 members'
    access, and 3.2 GB of files. This cannot be undone.
  </p>
  <p>To confirm, type the workspace name below:</p>
  <input id="confirm" placeholder="Acme Inc" autocomplete="off" />
  <div class="actions">
    <button onclick="closeDialog()">Cancel</button>
    <button id="confirm-btn" disabled class="destructive">
      Delete workspace permanently
    </button>
  </div>
</dialog>

<script>
const input = document.getElementById('confirm');
const btn = document.getElementById('confirm-btn');
input.addEventListener('input', () => {
  btn.disabled = input.value !== workspace.name;
});
</script>
```

What this achieves:

- The dialog must be opened deliberately.
- The consequences are stated plainly.
- The user must type — an active gesture that breaks autopilot.
- The button is disabled until the typed name matches, so even autopilot Enter doesn't trigger.

For actions that should genuinely never happen by accident, this stack is appropriate.

## Re-authentication for security-sensitive operations

```html
<button onclick="requireReauthThen('delete-account')">
  Delete account
</button>

<dialog id="reauth-dialog">
  <h2>Confirm your identity</h2>
  <p>For your security, please re-enter your password to continue.</p>
  <input type="password" id="reauth-password" autofocus />
  <div class="actions">
    <button onclick="closeDialog()">Cancel</button>
    <button id="reauth-submit">Continue</button>
  </div>
</dialog>
```

Use re-authentication when:

- The action affects security or billing.
- The action affects other users' access.
- The action would be devastating if performed by someone with stolen session access.
- Compliance requires it.

The cost: an extra password entry. The benefit: a second opportunity for the user to reconsider, plus protection against session theft.

## Structural prevention (the highest forgiveness)

Stronger than any confirmation: making the wrong action impossible.

### Disable the action when invalid

A "Submit" button disabled when the form has errors. The user can't trigger the failure path. (Pair with inline error explanations so the user knows what's missing — see `affordance-false-and-anti`.)

### Type-restricted inputs

`<input type="email">` rejects non-email format. `<input type="number">` rejects non-numeric. `<input type="tel">` shows a numeric keyboard on mobile. Each is structural prevention of certain input errors.

### Constraint by selection rather than typing

A `<select>` for state names prevents typos that a free-text field would allow. A date picker prevents impossible dates. A typeahead constrained to known values prevents misspelled selections.

### Physical / hardware analogies

The USB-C connector that can't be inserted upside-down. The pill organizer that shows visual state. The medical injector that can't deliver a dangerous dose.

### Required-field marking + blocked submit

```html
<form>
  <label>Email <span class="required">*</span>
    <input type="email" required />
  </label>
  <button>Submit</button>
</form>
```

The browser blocks submission with focus on the missing field. Native scaffolding for prevention.

## Anti-patterns

- **Confirmation fatigue.** "Are you sure you want to save? / open? / apply?" Every routine action confirmed. Users dismiss everything on autopilot.
- **Pre-selected destructive option.** A confirm dialog with the destructive button as default Enter target. Users who hit Enter without reading commit the destruction.
- **Trivial type-to-confirm.** Forcing users to type "DELETE" for a routine archive operation. Heavy friction for low-stakes action.
- **Hidden cancellation path.** A confirm dialog with no Esc, no backdrop dismiss, just two buttons. The user feels trapped.
- **Confirmation as the *only* forgiveness.** Apps where every destructive action is confirmed but nothing is reversible. Confirmation alone is insufficient — users still make mistakes.
- **Sneaky double-negatives.** "Are you sure you don't want to keep your account?" Users misread; mistakes happen.

## Calibrating friction to stakes

A useful framing: every confirmation step is a tax. Ask whether the tax is worth it for *this specific action*.

| Action | Reversibility | Stakes | Recommended confirmation |
|---|---|---|---|
| Save | Reversible | Low | None |
| Apply filter | Reversible | Low | None |
| Archive item | Reversible (toast undo) | Low | None |
| Delete (soft) | Recoverable in trash | Medium | None |
| Empty trash | Irreversible | Medium | Light dialog |
| Delete project | Irreversible | High | Strong dialog with summary |
| Delete account | Irreversible | Very high | Type-to-confirm + reauth |
| Transfer ownership | Irreversible | Very high | Type-to-confirm + reauth + email verification |

Each step up the friction ladder should correspond to a step up in stakes.

## Heuristics

1. **The reversibility-first check.** Before adding any confirmation, ask: can this be made reversible instead? If yes, do that.
2. **The autopilot test.** If a typical user would dismiss the confirmation without reading, the confirmation isn't doing its job. Either remove it or make it harder to dismiss without reading.
3. **The "what would they regret?" test.** For irreversible actions, imagine the user a week later realizing they made a mistake. Did the confirmation do enough to prevent that?
4. **The disabled-button question.** When you reach for confirmation, ask whether structural prevention (disabling the action when it shouldn't apply) would work better.

## Related sub-skills

- **`forgiveness`** (parent).
- **`forgiveness-undo-and-soft-delete`** — the preferred alternative when reversibility is possible.
- **`affordance-false-and-anti`** — disabled states and structural prevention.
- **`constraint`** — input constraints prevent invalid actions.
- **`expectation-effect`** — confirmation buttons in unexpected positions surprise users.
- **`accessibility-understandable`** (process) — confirmation flows must be operable for all users.
