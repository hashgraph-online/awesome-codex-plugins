---
name: textmock
description: Make fictional text conversations that open as editable Textmock links, or edit and render an existing Textmock conversation through its browser API or Mac command.
---

Use [Textmock](https://textmock.com) to make an iMessage-style conversation. For a new text-only mockup, use the bundled link helper. It runs locally with Node.js 24 or later and prints a link; it does not open a browser or change a saved conversation.

From this skill's directory, run the helper below. If your shell is elsewhere, use the helper's absolute path:

```sh
node scripts/textmock-link.mjs - <<'JSON'
{"name":"Mira","messages":[{"from":"them","text":"Did you bring the telescope?"},{"from":"me","text":"Yes. You bring the clear sky."}]}
JSON
```

Give the link to the user. It opens a preview; **Make a Copy** adds an editable conversation, subject to the app's conversation limit. The helper puts the text in the fragment after `#`, which browsers omit from navigation requests. Anyone who receives the full link can read it. Use fictional content unless the user asks to share their own material.

The helper accepts `name`, `messages`, optional `dark` and optional `clock`. Each message has `from` (`me` or `them`) and `text`. It refuses unknown fields, photos, imports and private notes. It supports one-to-one conversations, with 1–120 messages, up to 4,000 characters per message and a 180 KB document limit. Replies are off in the new copy.

For an existing conversation, images, video, groups or attachments, read [Use Textmock from an agent](https://textmock.com/docs/agents). In the editor, wait for `window.textmock` or `textmock:ready`. On Mac, use the app's `textmock` command. Inspect `status`, `list` and `get` before changing a saved conversation; follow the user's chosen conversation ID. A file passed to `textmock render --out` is replaced if it exists, so use a new path or a directory when preserving files matters.

Free use allows one conversation and exports with a badge. Respect `pro_required`; only the user can subscribe. Do not import Messages, delete conversations or share private content unless the user requests that action. Use the installed API's `help` for its current fields and limits.
