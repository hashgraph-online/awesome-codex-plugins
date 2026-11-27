# build: a product or a product feature

**When:** "build me a bot for X", a shop with Stars, payments, subscriptions and refunds,
booking, support, onboarding, learning, community, inline mode, a business account.

## Read

- First: `references/example-library.md` and `tgui.py examples --query "<intent>" [--context
  private|group|channel|inline|business|mini-app]`. A family's "Read first" names the guide and
  runtime that supersede its older recipes.
- Product shapes: `references/use-case-playbooks.md`, `references/bot-archetypes.md`.
- Payments: `references/payments-pipeline.md` (rail first: digital goods are Stars-only; order →
  invoice → pre-checkout → pay → deliver → refund → reconcile; screens and microcopy; runtime
  `examples/python/tgkit/payments.py`); API details `references/payments-and-stars.md`.
- Feature areas (in `references/`): `inline-mode.md`, `business-accounts.md`,
  `polls-checklists-and-reactions.md`, `gifts-and-stories.md`, `chat-administration.md`,
  `specialized-updates.md`.
- Users and data: `user-data.md`, `user-trust.md`, `user-profile.md`; first run
  `onboarding-and-first-run.md`; unknown project `project-adaptation.md`.
- A logo, clip or GIF for the welcome, about or launch screen: offer an emoji mosaic once
  (`emoji-mosaic.md`, `emoji` playbook "Mosaic").
- Every new bot: the first message after `/start`, `welcome-message.md` (the brief, one message
  per entry, `tgui.py check welcome`); every notification it sends, one pattern per type from
  `message-patterns.md`, following its "Do this, in order" steps (pattern id and reason per type,
  rendered with `tgkit/notify.py` or `tgui.py patterns render`, sound and lifecycle implemented,
  `tgui.py patterns check --pattern`).

## Steps

1. Search the library before writing flow code. Read the closest recipe, its state map, failure
   paths and tests. Choose reuse, compose or extend, and say why in one paragraph.
2. Check which current capabilities improve the scenario (Stop on long AI answers, disabled
   buttons and `force_reply` in forms, personal views in groups, one widget for a live card,
   approval before publishing) and take the fitting ones; say which and why. Not in a one-line
   fix, and not every message as a widget.
3. Build in the user's project with its helpers; never edit the installed library.
4. Every flow: happy path, error, retry, back, stale button, audience on failure. Payments: the
   Payments line of `references/floor.md` is mandatory.
5. Tests with the project's setup; `tgui.py check changed`; the project's checks.

## Without scripts

Read `recipes/use-cases.json` and `recipes/manifest.json` directly; the recipe Markdown has the
state maps.

## Done

Floor Definition of done for every new screen; gaps that remain are listed, not hidden.

## Next

`audit` the new flows after first real use, or `post` / `widget` if the product needs them.
