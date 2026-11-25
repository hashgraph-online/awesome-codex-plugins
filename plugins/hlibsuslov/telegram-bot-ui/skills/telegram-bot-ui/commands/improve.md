# improve: change existing screens

**When:** nicer, premium or cleaner; a new screen or form; streaming with Stop; pagination;
wording; brand fit; rethink the menus; move to the newest Bot API.

## Scale (pick one and say which)

- **One label, button or message:** fix it, `tgui.py check keyboard|rich|payload`, test. No audit.
- **A screen, form or feature:** the steps below, for the affected screens only.
- **Premium pass ("make it nicer"):** `references/visual-language.md` §7 first. Every screen in
  scope gets copy and a first line, then hierarchy and labels, then color, icons last; every list
  its empty state, every load its error state, old buttons the stale answer.
- **Whole bot, brand fit, migration:** `references/redesign-orchestration.md` §0-9 with its gates
  (mandate, research, voice gate "show, don't ask", structure, migration), and
  `references/bot-style-profile.md` (`tgui.py profile probe|scaffold|check`).

## Read (only what the change touches; all in `references/`)

Wording `microcopy-and-labels.md` · buttons and color `buttons-and-styles.md` · inline keyboards,
pagination `inline-keyboards.md` · reply keyboards, `ForceReply` `reply-keyboards.md` · screens,
back, commands, deep links `navigation-and-flows.md` · first run `onboarding-and-first-run.md` ·
body format `format-selection.md`, `tables.md`, `data-views.md`, `telegram-capabilities.md`,
`regular-formatting.md` · media `media-and-files.md`, `rich-media.md` · limits
`limits-and-splitting.md` · feedback and Stop `dynamic-feedback-and-streaming.md`,
`streaming-and-editing.md` · groups and personal views `ephemeral-and-personal.md`,
`topics-and-contexts.md` · personalization `personalization-and-links.md`, `user-profile.md` ·
bot settings `bot-settings.md` · languages `localization-and-rtl.md` · version gates
`ui-changelog.md` · unknown project `project-adaptation.md` · worked examples
`examples-before-after.md`, `case-study-btc-tracker.md`.

## Steps

1. Map the affected screens and their states, or take them from saved findings.
2. Show, don't ask: one screen before and after (text, keyboard, order) before editing the rest.
3. Design text → structure → layout → color and icons. Check every new field with
   `tgui.py lookup show <Symbol>` and the installed SDK.
4. Implement in the project's builders; keep `callback_data`, deep links, routing, locale keys.
5. Add an audience-preserving fallback and tests; run `tgui.py check changed` and the project's
   checks. Close what you fixed: `tgui.py findings close <id>`.

## Without scripts

Check fields in `data/bot-api/catalog.json` by searching the method or type name; count
`callback_data` in UTF-8 bytes (at most 64).

## Done

`references/floor.md` Definition of done for the screens in scope; before/after shown; evidence
level named.

## Next

Remaining findings → `improve <screens>`; icons chosen → `emoji`; posts affected → `post`.
