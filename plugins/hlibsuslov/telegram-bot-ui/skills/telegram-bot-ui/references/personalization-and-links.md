# Personalization and links

Two adjacent surfaces that decide whether a bot feels *addressed to me* and
whether its actions are reachable.

## What the API actually gives you about a user

`User` fields (Bot API), with their real optionality — the source of most
personalization bugs:

| Field | Guaranteed? | Use for |
|---|---|---|
| `id` | **Yes** | Internal identity only — never display it |
| `is_bot` | Yes | Branching bot/human flows |
| `first_name` | **Yes** | Greeting, meaningful results |
| `last_name` | **Optional** | Rarely useful; never assume it exists |
| `username` | **Optional** | `t.me/…` links only when present |
| `language_code` | **Optional** | *Initial hint* for locale, not the decision |
| `is_premium` | **Optional** (`True` when set) | Feature gating, never flattery |
| `added_to_attachment_menu` | Optional | Attachment-menu flows |

In Mini Apps a `photo_url` may be available depending on the user's privacy
settings. **`initDataUnsafe` is untrusted** — send the signed `initData` to your
backend and validate it there before personalizing anything that matters.

## Safe display name

```ts
const displayName =
  user.first_name?.trim() ||
  user.username?.trim() ||
  "there";                      // localized neutral fallback
```

- `username` is optional → `https://t.me/${username}` cannot be built
  unconditionally. Guard every such link.
- Names are **user-controlled input**: escape them for the parse mode in use, or
  better, pass `MessageEntity` objects instead of concatenating markup
  (`security-and-escaping.md`). A user named `<b>` or `[x](y)` will otherwise
  break or hijack your formatting.
- Names can be long, RTL, or emoji-only — don't let one into a button label or a
  table column without truncation (`localization-and-rtl.md`).

## Personalize functionally, not decoratively

Good — the personalization carries information:

```
Hi Alex, shall we continue where you stopped?
Your last score: 28 / 34.
Resume the test from question 17?
Open your July results
```

Bad — the bot narrating what it knows about the user:

```
Alex, I can see you have Telegram Premium, your username is @example
and your interface language is Russian.
```

Rules:

- **Name in the greeting and in results that matter** — not in every message.
  Repeated first-name use reads as manipulative, and it ages badly in long
  threads.
- **`language_code` is a hint.** Use it to pick the initial locale, then let the
  user change it and store their choice; never override an explicit setting.
- **`is_premium` gates features**, it is not a compliment. Note that custom emoji
  eligibility depends on the **bot owner's** Premium, not the viewer's
  (`custom-emoji.md`).
- **History beats attributes.** "Resume step 3 of 5" is worth more than any
  demographic detail.
- **Never surface raw identifiers** (`id`, internal keys) in the UI.
- **Never claim knowledge you inferred.** If personalization is wrong, the user
  loses trust in everything else the bot says.

## Links: choosing the right surface

| Intent | Surface |
|---|---|
| The main action of the screen | **URL button** (`url`, optionally `style: "primary"`) |
| Supporting source inside a sentence | **Inline text link** (`text_link` / `<a href>`) |
| Bring a user into a specific flow from outside | **Deep link** (`t.me/<bot>?start=<payload>`) |
| Mention a user without a username | `tg://user?id=<id>` link |
| Open the bot's app | **Mini App button** / menu button |
| Copy a code or address | `copy_text` button (`CopyTextButton`, 1–256 chars) |

**Never dump a bare URL** as the message body:

```
Documentation:
https://example.com/documentation/telegram-bot-api
```

Write the link into the sentence, or make it a button:

```json
{ "text": "Open the report", "url": "https://example.com/report", "style": "primary" }
```

Rule of thumb: **one primary destination per screen goes to a button**;
secondary references stay as text links. Clients may show the full URL and a
warning before opening an external link — so the label must match the
destination, or the confirmation dialog will contradict your copy.

## Link previews

`LinkPreviewOptions` (verified fields): `is_disabled`, `url`,
`prefer_small_media`, `prefer_large_media`, `show_above_text`.

```json
{
  "link_preview_options": {
    "url": "https://example.com/article",
    "prefer_large_media": true,
    "show_above_text": true
  }
}
```

- `prefer_small_media` / `prefer_large_media` are **ignored unless `url` is set
  explicitly** and the preview supports resizing.
- `show_above_text` turns a link into a header image — good for announcements,
  distracting inside a menu.
- **Disable the preview** (`is_disabled: true`) whenever the link is incidental;
  an unwanted preview is the most common visual noise in bot messages.
- Only one preview per message — if the text has several links, choose which one
  represents it.

## Mentions without a username

```html
<a href="tg://user?id=123456789">Alex</a>
```

Works as an inline link or a URL button, and depends on chat context and the
user's privacy settings. Treat it as best-effort: never build a flow whose
correctness requires the mention to resolve.

## Deep links

`t.me/<bot>?start=<payload>` starts the bot on a specific screen — referrals,
resuming a flow, onboarding, connecting an account, entering a campaign.

- Keep payloads **short and opaque**: `start=flow_8f31a2`, with the real state
  on the backend.
- **Never** encode personal data, prices, or privileges in the payload — it is
  visible, shareable, and forgeable.
- **Validate** the payload and re-check permissions on arrival.
- Deep links printed on posters, QR codes, or ads are **long-lived**: do not
  retire or repurpose one during a redesign (`navigation-and-flows.md`).
- `/start` with an unknown or expired payload must degrade to the normal landing
  screen, not to an error.

## In-message navigation (Rich Messages)

For a long report, Rich Messages (Bot API 10.1+) support anchors and anchor
links, references and footnotes, collapsible `details` blocks, email and phone
links, and user mentions. A single navigable document beats five loose messages
— see `telegram-capabilities.md` and `tables.md`.

## Checklist

- [ ] `last_name`, `username`, `language_code`, `photo_url` treated as optional
      everywhere.
- [ ] Display-name fallback chain implemented and localized.
- [ ] All user-supplied text escaped, or passed as entities.
- [ ] Name used where it adds meaning, not in every message.
- [ ] `language_code` used as an initial hint; explicit choice stored and wins.
- [ ] Mini App personalization based on validated `initData`, not
      `initDataUnsafe`.
- [ ] Primary destination is a button; incidental links are text links.
- [ ] Link previews deliberately configured or disabled.
- [ ] Deep-link payloads opaque, validated, and preserved across the redesign.
