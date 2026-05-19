# Layer 05 — Feature / UX

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

User-facing flows that implement PDP-family obligations or interact with personal data. Universal patterns across native, hybrid, and web stacks.

## Signup consent

The signup flow is where the user first agrees to the terms. Two requirements:

1. **Specific, informed, freely given consent.** A single checkbox bundling T&C + privacy policy is acceptable when both documents are clearly linked and both cover only operational uses of data.
2. **Consent must not be required beyond what is reasonable to provide the service.** If the application sends marketing alongside transactional content, marketing consent must be unbundled (separate toggle, defaulted off).

**Common signup-form elements:**

| Element | PDP-family requirement |
|---|---|
| T&C / Privacy Policy checkbox (active opt-in) | Required. Pre-checked is generally not consent. |
| Email / phone for verification | Required to provide service if used for OTP / account recovery. |
| Date-of-birth picker (where age gating applies) | Some jurisdictions require minimum age (e.g. 13 or 16). Gate the submit button. |
| Marketing-consent toggle (if marketing exists) | Must be separate from operational consent. Default off. |

When the application has only transactional notifications (chat, account events, content-the-user-asked-for), consent for those channels can be bundled into the T&C acceptance — completing signup with a working contact constitutes consent for transactional use. The line shifts the moment marketing / promotional content is added.

## Settings — consent management

Every consent the user gave at signup must be revocable from in-app settings, with **equal effort** to grant.

| Toggle | What revoking it does |
|---|---|
| Push notifications | Stops push delivery + clears the push token from the server |
| Email notifications | Stops promotional / non-essential email; transactional may still send |
| Location processing (if used) | Stops collection; existing stored coordinates should be deletable separately |
| Marketing communications (if separate) | Stops promotional content immediately |

Each toggle change writes a row to the consent log (see [layer 03](03-data-model.md)) — granted or revoked, with timestamp.

## Account deletion

The deletion flow must be findable, completable without contacting support, and irreversible after a clear confirmation.

**Recommended UX:**

1. Settings → "Delete account" (visible, not hidden in submenus).
2. Warning dialog: what will be deleted (their data) vs what will be retained (anonymised attribution to chat history etc.).
3. Triple-confirm: typed `"DELETE"` (or equivalent) plus password / OAuth re-verification.
4. Best-effort revocation of any third-party tokens (OAuth, push tokens).
5. Server-side delete via a single transactional function (cascade).
6. Sign out and return to signup screen.

**Things often missed:**
- Object-storage cleanup — DB cascade doesn't reach the file storage layer; explicit cleanup is needed.
- OAuth provider revocation — if the user signed in with Apple / Google, attempt to revoke the refresh token at the provider so they're informed the user is gone (Apple App Store guideline 5.1.1(v) requires this on iOS).
- Push-token cleanup — null the device token before delete, otherwise a push could be sent to a phantom account during the window between cleanup and DB delete.

## Data export (Access right)

The user can request all personal data the organisation holds about them. The UX is typically:

1. Settings → "Download my data".
2. The function generates a JSON (or similar structured) payload.
3. Delivered via native share-sheet (mobile) or download link (web).
4. Rate-limited (e.g. once per 7 days) to prevent abuse.

**Critical:** the export must include *all* personal data, not just the visible profile. See [layer 03](03-data-model.md) — keep the inventory in sync, and reference it whenever a new column / field is added.

## Just-in-time permission prompts (OS-level)

For permissions that the OS gates (camera, photos, location, notifications):

- **Don't request at app launch.** Cold OS prompts have high decline rates and consume the one-shot ask. Once denied, re-asking is much harder.
- **Request just-in-time, in context.** When the user taps "Take photo" → request camera. When the user opts into nearby matching → request location.
- **Soft-prompt first** (in-app modal) before triggering the OS dialog. Explain why the permission is needed in your app's voice, with a "Not now" option that does NOT consume the OS one-shot. Then the OS prompt fires for users who tap "Allow" in the soft-prompt.

## Soft-prompt dialog pattern

**Anatomy:**
- Branded image (mascot, illustration, or icon)
- Title in plain language ("Stay in the loop", "Find friends nearby")
- Body listing concrete benefits the user gets, in their voice not yours
- Primary button: "Allow" / "Turn on …" — calls the underlying request function
- Secondary button: "Not now" — returns false WITHOUT marking the OS one-shot as consumed
- Modal pattern: not dismissible by tap-outside (force a deliberate choice)

**Why "Not now" matters:** if the user dismisses the soft-prompt this time, you can re-show it the next time the same context arises. If you'd already triggered the OS dialog and they declined, you're done — only Settings deep link recovers.

## Block / unblock

When the application has user-to-user interactions (messaging, friend requests, matching):

- Blocking creates a record (e.g. `friend_requests.status = 'blocked'`).
- Server-side enforcement: blocked users cannot message, search for, or see the public profile of the blocker.
- The block list is itself personal data — include it in the data export.

## Photo / file uploads — EXIF stripping

Modern phone cameras embed extensive metadata in image files: GPS coordinates of where the photo was taken, device model, software version, exact timestamp. **This metadata is personal data**, often more revealing than the image itself.

**Strip EXIF before upload.** Most image-compression libraries do this automatically as a side-effect of re-encoding (e.g. WebP encoding strips EXIF). Verify your upload pipeline includes a re-encoding step.

Disclose in the privacy policy that EXIF is stripped, and what the upload pipeline retains (typically: image content + dimensions + content-type, nothing else).

## OAuth signup flows

When supporting Sign in with Apple, Google, or similar:

- Capture only what the provider returns: name (first sign-in only for Apple), email, provider user ID.
- Don't request additional scopes unless they're directly needed for a feature.
- Store the OAuth refresh token securely so it can be revoked at the provider on account deletion.
- For Sign in with Apple specifically: the user may choose to hide their email; Apple provides a private relay address. Treat it like any other email — don't try to discover the real one.

## Email / phone verification (OTP)

When email or phone is used for account verification:

- Be explicit in the signup flow that completing verification is required to use the service.
- The verification act constitutes consent for transactional use of that channel (account events, security alerts, content-requested notifications).
- For marketing use of the same channel: separate opt-in is required.

## Re-prompting after a previous decline

If the user denied a permission at the OS level, you cannot re-prompt directly — only Settings deep link recovers. Common patterns:

- **Settings deep link**: when the user later tries to use a feature requiring the denied permission, show an explainer with a button that opens the OS settings page.
- **Avoid annoyance**: don't repeatedly ask the user to enable a permission they've already declined; one well-timed prompt per session is the upper bound.

## Children's / minors' data

Most PDP-family statutes have specific protections for under-13 (or under-16, jurisdiction-dependent) data subjects. If your application is or could be used by minors:

- Gate signup on age (DOB picker with minimum-age check).
- If minors are permitted users: stricter defaults (no marketing, no public discovery, parental-consent flow if required).
- Disclose the minimum age in the privacy policy and T&C.

If your application is not directed at minors and you make that explicit (T&C + privacy policy say "16+ only"): you've shifted the gating burden to the user's representation, but you still must take down accounts when you become aware they're under-age.
