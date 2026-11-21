# Textmock conversation links

Make a fictional text conversation that opens as an editable copy in [Textmock](https://textmock.com). This package includes a coding-agent skill and a small local link helper. The helper needs Node.js 24 or later and has no dependencies.

## Make your first link

Save this as `conversation.json`:

```json
{
  "name": "Mira",
  "messages": [
    { "from": "them", "text": "Did you bring the telescope?" },
    { "from": "me", "text": "Yes. You bring the clear sky." }
  ]
}
```

From this package's folder, run:

```sh
node scripts/textmock-link.mjs conversation.json
```

Open the printed link and choose **Make a Copy**. Edit the conversation, then choose **Save Image** or **Make Video**. Creating the link and viewing its preview change no saved conversation. Making a copy follows Textmock's usual conversation limit: free use keeps one conversation and adds a badge to exports; Pro allows more conversations and removes the badge. An untouched starter can be replaced by the new copy. An existing edited conversation is preserved if there is no room.

The helper accepts `name`, `messages`, optional `dark` and optional `clock`. Each message has `from` (`me` or `them`) and `text`. It creates one-to-one conversations with replies off, up to 120 messages and 4,000 characters per message, within a 180 KB JSON document limit. Unknown fields are refused. Use the app's agent interface for groups, photos, attachments and rendering.

The helper encodes conversation content in the fragment after `#`, which browsers omit from navigation requests. Anyone with the complete link can read it. Keep full links out of logs when they contain private material.

Read [Use Textmock from an agent](https://textmock.com/docs/agents) for the browser API and Mac command, or the [conversation format](https://textmock.com/docs/conversation-format) for the app's full document shape. The MIT license covers this skill and helper; the Textmock application has its own terms.

## Add the skill to an agent

Set up the product as described above, then install its integration files.

For Codex CLI:

```sh
codex plugin marketplace add https://github.com/hraness/product-skills.git
codex plugin add textmock@hraness-products
```

In Claude Code:

```text
/plugin install textmock --marketplace hraness/product-skills
```

A Cursor team marketplace administrator can import
`https://github.com/hraness/product-skills`, then select this product. See
[Cursor's repository import instructions](https://cursor.com/docs/plugins#add-a-team-marketplace).
These repository installs are separate from public directory approval.
