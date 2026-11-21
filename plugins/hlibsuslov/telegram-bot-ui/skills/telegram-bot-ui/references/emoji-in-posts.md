# Premium emoji in posts, long texts and rich messages

> Status labels: **API**, **Official**, **Heuristic** (as in `emoji-packs.md`). Checked
> 2026-11-15 against Bot API 10.4. Code: `examples/python/tgkit/icons.py` (`decorate_post`,
> `IconSystem.rich`, `rich_label`, `TextComposer`, `density_warnings`). Recipe:
> `recipes/72-channel-post-series.md`.

## Channel eligibility — stated exactly

**API:** custom emoji (entities, `<tg-emoji>`, `tg://emoji`, button icons) "can only be used
by bots that purchased additional usernames on Fragment or in the messages directly sent by
the bot to private, group and supergroup chats if the owner of the bot has a Telegram
Premium subscription." Channels are not in that list: **a bot posting to a channel needs the
Fragment route.** With owner Premium only, decorate channel posts with Unicode accents.
`icons.for_context(SendContext.channel())` makes this decision for the whole post.

## Where custom emoji can go in a post

| Surface | Syntax | Notes |
|---|---|---|
| Regular HTML text/caption | `<tg-emoji emoji-id="ID">📣</tg-emoji>` | **API**: the tag's content must be a valid emoji |
| MarkdownV2 | `![📣](tg://emoji?id=ID)` | escape `)` and `\` inside `(…)` (**API**) |
| Entities | `{"type": "custom_emoji", "offset", "length", "custom_emoji_id"}` | UTF-16 offsets (**API**); `TextComposer` builds them |
| Rich message blocks | `{"type": "custom_emoji", "custom_emoji_id": ID, "alternative_text": "📣"}` | any RichText field: headings, paragraphs, list items, table cells, captions, footers |
| Rich HTML / rich Markdown | `<tg-emoji emoji-id="ID">📣</tg-emoji>`, `<img src="tg://emoji?id=ID" alt="📣"/>`, `![📣](tg://emoji?id=ID)` | **API** (Rich Message Formatting Options) |
| Rich message buttons | RichText with plain text, `RichTextCustomEmoji`, `RichTextDateTime` only | **API** |
| Poll question / options | custom emoji entities only | **API**: "only custom emoji entities are allowed" |
| Legacy `Markdown` | — | **API**: cannot express custom emoji |

Not inside links, code or pre (**API** nesting rules for regular entities); this skill also
skips `pre` blocks, formulas and link-type rich texts (**Heuristic**, mirroring the regular
rules). Custom emoji alternative text counts toward the 32768-character rich limit (**API**).

## Accents that help a reader

| Role (slot) | Use | Budget (**Heuristic**) |
|---|---|---|
| headline (`headline`, `announcement`, `update`) | one mark before the post title | 1 |
| section (`section`) | before a bold sub-heading | 1 per section |
| bullet (`bullet`, `check_item`, `cross_item`) | one list per post; otherwise plain `•` | 1 list |
| status (`done`, `failed`, `pending`, `warning`) | state of an item, never decoration | as needed |
| callout (`callout`, `tip`) | a note box lead | 1 |
| CTA (`cta`) | before the call-to-action line, not inside the link | 1 |

Density (**Heuristic**): ≤ 1 custom emoji per line, ≤ 8 per post, ≤ 3 per bot screen text;
`density_warnings(params, post=True)` and `audit_icons.py --payload FILE --post` check it.
One family across a series. Animated marks: at most one per post.

## Accessibility

The alternative emoji is what screen readers announce, what notifications and chat previews
show, what non-Premium users see after a forward, and what old clients render (**Official**:
the fallback "will be shown instead of the custom emoji in places where a custom emoji cannot
be displayed"). So pick slots whose fallback means the same thing, use the sticker's own
`emoji` field (`resolve_icon_map` stores it as `fallback`), and never let an accent carry
meaning the words do not.

## Decorating a post model

```python
from tgkit.icons import IconSystem, SendContext, decorate_post
view = icons.for_context(SendContext.channel())
params = {"chat_id": "@channel", **decorate_post({
    "headline": "Version 2.4 is out", "lead": "Faster sync.",
    "sections": [{"title": "New", "bullets": ["Offline drafts"]}],
    "cta": {"text": "Changelog", "url": "https://example.com"}}, view)}
```

`decorate_post` returns regular-HTML `sendMessage` params; when the view is off it emits the
same post with Unicode accents (or none with `unicode_fallback=False`).

## Integration with the publishing helper

The publishing stream owns `examples/python/tgkit/publish.py`; this skill does not edit it.
The integration point is one call before any send it makes:

```python
params = icons.for_context(SendContext.channel()).prepare(method, params)
```

`prepare` converts Unicode emoji in `text`/`caption` (by `parse_mode` or entities), rich
messages and keyboards to the pack, or strips every custom emoji when the post is not
eligible — all or nothing per post. For error handling use `icons.send(...)` instead, which
adds the one-retry kill switch (`custom-emoji.md#runtime-errors-and-the-kill-switch`).
