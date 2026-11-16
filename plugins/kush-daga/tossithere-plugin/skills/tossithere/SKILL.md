---
name: tossithere
description: Share HTML with the user as a link, and read their comments back. Use this whenever you have made HTML content the user should see (a report, plan, briefing, dashboard, prototype, deck, tracker, one-pager), instead of pasting HTML into the chat or sending a file. Also use it when the user asks you to share something, send them a link, show it to their team, or address the feedback or comments on something you published. Triggers: "share this", "send me the link", "make it a page", "show the team", "what did they say", "address the comments", "publish that".
---

# tossithere: share HTML as a link, get comments back

tossithere turns an HTML file into a page at a link that opens on any screen, laptop or
phone. The user (and anyone they share it with) comments on the exact element or text
they mean. You read every comment with the markup it points at, fix the HTML, and
publish the next version to the same link.

Use it every time you make HTML for the user. A link is the deliverable: don't paste the
HTML into the chat, and don't send a file they'd have to open on a laptop.

## Connected over MCP?

If you have the tossithere MCP tools (`publish_page`, `list_comments`, `resolve_comment`
and the rest), use them and skip the CLI: they do everything below, signed in as the
user. The server is `https://tossithere.com/mcp`. The steps are the same: publish, give
the user the link, read the comments, publish the fix with the same `id`, resolve what
you fixed.

## Install and sign in (once)

If you can run shell commands, install the CLI:

```bash
command -v toss || npm install -g tossithere
# or, without npm: curl -fsSL https://tossithere.com/install.sh | sh
toss whoami
```

If `toss whoami` says "Not signed in", run `toss login`. It prints a short code and a
link. Send both to the user and ask them to open the link and approve. Wait for the
command to finish; after that you stay signed in.

No shell? Use the HTTP API at the end of this file. It does the same things.

If the user can't sign in right now, publishing still works without an account: the
page is public, expires in 24 hours, and the output includes a claim link they can
open later to keep it.

## Personal or team

Before the first publish, find out where pages should go, then remember the answer:

- **Personal** (the default): pages land in the user's own workspace, private to them.
  Right for briefings, logs, plans and anything only they should see.
- **Team**: if the user works with others, `toss teams:list` shows their teams. Publish
  with `--team <slug>` and everyone in that team can open and comment, with no share
  step. If there is more than one team, ask which one rather than guessing.

The user may have set defaults with `toss config:set` (team, visibility, who can
comment). `toss config:get` shows them, and `doc.visibility` in every push says what
actually applied.

## Publish

```bash
toss docs:push report.html --json
toss docs:push report.html --team <slug> --json   # into a team workspace
```

Keep `doc.id` from the output and remember which file it belongs to: it is how you
publish new versions to the same link. Give the user `doc.url`, once.

For a page with assets (CSS, images, data files), push the folder. It needs an
`index.html` at its root, and relative links between files keep working.

Write HTML that reads well on a phone: a readable font size, a fluid layout, no fixed
widths. Pages run without network access (`connect-src 'none'`), so inline your data.
Google Fonts and cdnjs libraries do load.

## Share it with someone

A signed-in push is private. If the user wants someone else to see it:

```bash
toss docs:share <docId> --visibility public --allow comment
```

Visibility is `private`, `team` or `public` (anyone with the link). `--allow` is `read`,
`comment` or `edit`. Reading never needs an account; commenting takes a Google sign-in,
so every comment has a name. Pages are hidden from search engines unless the owner
turns indexing on.

## Read the comments and fix the page

When the user says they've left comments, or asks you to address feedback:

```bash
toss comments:list <docId> --unresolved --json
```

Each thread carries what it points at:

- `anchor.elementHtml`: the exact markup the comment is about
- `anchor.selectedText`, `anchor.prefix`, `anchor.suffix`: for text, enough to find the
  right occurrence when the same words appear twice
- `anchor.selector`: a structural CSS path
- `version`: the version the comment was written against

Match `elementHtml` against your source file. Don't re-fetch the page or guess from the
comment text; the anchor is there so you don't have to. A comment on an older `version`
may point at markup that has already changed, so check the current file first.

Then publish the fix to the same link, and close only what you fixed:

```bash
toss docs:push report.html --id <docId> --note "what changed"
toss comments:resolve <docId> <commentId>
```

Leaving a thread open is the honest signal that you didn't address it. Say so in your
reply instead of resolving it quietly.

## Read a page someone else published

When the user hands you a tossithere link and wants you to work from it:

```bash
toss docs:pull <docId-or-link>          # the HTML, exactly as published
toss docs:pull <docId-or-link> --json   # with doc, version and path
```

It uses your own access, so private and team pages work if your account can open them.
`FORBIDDEN` means it can't: ask the user to share it with that account.

## Good to know

- **Retries are safe.** Pushing identical content returns `version.reused: true` and
  creates nothing.
- **One link per thing.** Recurring pages (a daily briefing, a running log, a weekly
  report) should push to the same `--id` each time, so one bookmark always shows the
  latest version and older ones stay readable.
- **Errors are coded**: `{ "error": { "code", "message", "hint" } }`. `UNAUTHENTICATED`
  means sign in again. `DOC_LIMIT_REACHED` means the workspace is full on the Free plan
  (10 documents): tell the user, upgrading is at tossithere.com/billing.
  `TEAM_NOT_FOUND` means they aren't in that team. `FORBIDDEN` on a push means publish a
  new document instead of a version.

## No shell? The HTTP API

Everything above works over HTTPS with JSON. Base URL: `https://tossithere.com/api`.

**Sign in.** Either the user creates an API key at https://tossithere.com/keys and gives
it to you, or you start a sign-in they approve:

```
POST /api/auth/device/start
  -> { deviceCode, userCode, verificationUrlComplete, interval, expiresIn }
```

Send the user `verificationUrlComplete` and ask them to approve. Then poll every
`interval` seconds:

```
POST /api/auth/device/poll   { "deviceCode": "..." }
  -> 428 while waiting, then { "token": "..." }
```

Keep the token (or API key) and send it on every call as
`Authorization: Bearer <token>`.

**Publish** (a new page, or a new version with `id`):

```
POST /api/docs/push
  { "html": "<!doctype html>...", "name": "report.html", "id": "d_...", "team": "<slug>", "note": "what changed" }
  -> { doc: { id, url, visibility, ... }, version: { number, reused } }
```

**Share:** `POST /api/docs/<docId>/share` with
`{ "visibility": "public", "capability": "comment" }`.

**Teams:** `GET /api/teams`. **Who am I:** `GET /api/whoami`.

**Comments:** `GET /api/docs/<docId>/comments?unresolved` returns the threads with their
anchors. Resolve one with `POST /api/docs/<docId>/comments/<commentId>` and
`{ "action": "resolve" }`.

**Read a page:** `GET /api/docs/<docId>/content`.

## The whole loop

```bash
toss docs:push briefing.html --json                       # -> d_briefing-0926, a link
# ... the user reads it on their phone and comments ...
toss comments:list d_briefing-0926 --unresolved --json    # -> threads with markup
# ... fix the HTML using anchor.elementHtml ...
toss docs:push briefing.html --id d_briefing-0926 --note "moved the dentist"
toss comments:resolve d_briefing-0926 c_001
```
