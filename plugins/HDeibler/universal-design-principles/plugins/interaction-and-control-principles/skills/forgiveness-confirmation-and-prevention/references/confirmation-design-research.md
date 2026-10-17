# Confirmation design: research and pattern reference

A reference complementing `forgiveness-confirmation-and-prevention` with deeper detail on confirmation patterns and how they degrade.

## The science of confirmation fatigue

Confirmation fatigue is well-documented in HCI literature. Key findings:

- **Habituation kicks in fast.** After 3–5 confirmation dialogs in a session, attention to subsequent dialogs drops measurably.
- **Same-shape dialogs degrade fastest.** If every confirmation looks the same, users dismiss them on shape recognition alone, not content.
- **Pre-selected default options compound the problem.** When the destructive button is the default, users hit Enter without reading.
- **Modal interruption increases dismissal rate.** A modal that blocks the page is dismissed faster than an inline confirm because users want to get back to work.

The research conclusion: confirmations work *only* when they are rare, distinct, and require active engagement (typing, not just clicking).

## Type-to-confirm patterns

The most reliable way to break autopilot:

```
To delete this workspace, type "Acme Inc" below:
[ ___________________ ]
```

Variations:

- **Resource name** (most common): user types the project/account name. High specificity, hard to autopilot.
- **Action verb** ("type DELETE"): used when there's no specific resource name. Lower specificity but still breaks autopilot.
- **Random verification code**: shown in the dialog, typed by the user. Used when even the resource name might be auto-completed by browser.

## Confirmation copy

Effective confirm copy answers three questions:

1. **What is being acted on?** Name the specific resource ("Delete project Acme Q4?"), not the generic action ("Delete?").
2. **What is the consequence?** Spell out what will happen and what will be lost.
3. **Is it reversible?** Either say "This cannot be undone" or describe the recovery path.

```
Delete project "Acme Q4"?

This will:
  • Delete 24 tasks
  • Remove 8 attachments (12 MB)
  • Revoke access for 3 collaborators

This action cannot be undone.

[ Cancel ]   [ Delete project ]
```

The user has enough information to decide; the friction earns the consequence.

## Re-authentication patterns

For account-affecting actions, requiring password re-entry:

- **Acts as confirmation** by requiring active engagement.
- **Acts as security** by verifying the current user is who they claim.
- **Defends against session theft** — even if someone has your active session, they don't have your password.

Common in: account deletion, email change, ownership transfer, billing changes, viewing audit logs.

Implementation pattern: a separate dialog that intercepts before the destructive action proceeds. The user types their password; on success, the protected action runs.

## Two-factor confirmation

For the highest-stakes actions (transferring ownership, deleting an organization, irreversible financial commits), two-factor authentication can act as confirmation:

```
This action requires verification.
Enter the 6-digit code from your authenticator app:
[ _ _ _ _ _ _ ]
```

The user must access another device or app, breaking autopilot decisively. Used in: enterprise admin actions, compliance-sensitive operations, large financial transfers.

## When the dialog itself is the dark pattern

Confirmation can be weaponized. Examples:

- **"Are you sure you want to cancel?"** with "Cancel" buttons and "Continue" buttons in confusing layouts. Designed to retain users who tried to leave.
- **"Don't quit! Try our offer first!"** — confirmations that interpose marketing content.
- **"You'll lose your benefits!"** — playing loss aversion to dissuade legitimate cancellation.

Regulators (FTC, EU consumer protection) increasingly penalize these. Even if not yet illegal in your jurisdiction, they damage trust badly.

A useful test: would this dialog be acceptable if you were the user? If you'd resent the dialog, your users probably will too.

## Resources

- **Norman, D.** *The Design of Everyday Things* — chapters on errors and forcing functions.
- **Reason, J.** *Human Error* (1990) — slip vs. mistake; designing against both.
- **NN/g** — many articles on confirmation design and dialog design.
- **Brignull, H.** *Deceptive Patterns* (deceptive.design) — catalog of dark-pattern confirmations to avoid.
