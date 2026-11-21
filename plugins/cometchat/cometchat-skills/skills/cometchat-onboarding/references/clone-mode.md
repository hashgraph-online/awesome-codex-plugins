# Clone mode — "build me a clone of X"

Load this when the user names an existing app to copy: "build a <app> clone", "make it like <app>",
"a chat app like <app>", "clone <app> with CometChat", or shares screenshots of an app to match. The
one-line request is complete: run the whole flow below yourself. Never ask the user to spell out the
process.

**Source of truth:** the CometChat chat experience blueprint, `https://www.cometchat.com/docs/design-system.md`.
Read it first, before planning. Read its sections *From a one-line request*, *Cloning an existing
app*, *Kit component or your own UI?*, *Calls and huddles*, *Design sync*, *Per-platform notes* and
*Verify it looks and feels real*. Getting it, in this order:

1. **Docs MCP:** `fetch_cometchat_doc_page` with `path: "/design-system"` (the `cometchat`
   MCP server; no sign-in needed). This is the normal path; use the Docs MCP for every other CometChat doc lookup too.
2. **Plain web fetch of the URL** if the Docs MCP returns `not_found` or another error, refuses the
   URL, or isn't connected.
3. **Check what came back.** It is the blueprint only if it has the *Cloning an existing app* section.
   A redirect to the docs home, an index page or an error page is not the blueprint.
4. **If neither path returns the blueprint,** run the flow from this file, which carries the same
   rules, and say in the plan that the blueprint couldn't be read.

## How clone mode changes the four beats

### Beat 1 — DETECT
Unchanged. A detected project fixes the platform; don't ask for it.

### Beat 2 — UNDERSTAND (one short message, then work)
Ask at most **one** message of questions, each with a default so "go with the defaults" is a valid answer:

- **Platform / framework** — only if no project was detected. Default for a new web app: React + Vite
  with the current React UI Kit.
- **App name** — the customer's product name, shown instead of the target's. Default: a neutral placeholder.
- **Screenshots (optional)** — a few of the target's main screens, light and dark, make the clone
  noticeably closer.

Everything else is a default, not a question:

| Decision | Default |
| --- | --- |
| Archetype | Inferred from the target (team workspace, consumer messenger, community server, support, marketplace) |
| Design / theming | **Match the target**: tokens measured from it, light + dark following the OS |
| Form factor | Follow the target (desktop-first or mobile-first), responsive to the other |
| Login | A real login screen; for a demo, a user picker; auth tokens noted for production |
| Brand | The customer's name + an open icon set in the target's style — never the target's logo, name, or icons |
| Third-party packages | UI Kit / SDK only; packages that would get closer are listed as options |
| Scope | Everything the target has at levels L0–L4 (below); L5/L6 listed separately with their cost |

### Research the target (before the plan)
**Research first, then write the inventory.** Inventory the target, per screen and per form factor.
Sources, best first: the user's screenshots or recordings → the real app if you can open it → the
target's public help docs and product pages (search for them and read them) → your own knowledge only
to know where to look. Record the sources you used in the requirements file. A row that comes from
memory alone, with no source, is **unverified**. Record:

- **Every feature: entry point → container → close.** Button, field, menu or shortcut → centered
  dialog, popover, side panel, bottom sheet, new page or inline → Esc, click outside, back, or close.
  The same feature opening in a different place is what makes a clone feel wrong.
- Screens and navigation; list rows (sections, unread style, badges, hover, row actions); messages
  (bubbles or flat, grouping, timestamps, receipts, reactions, replies, thread entry); composer
  (toolbar, Enter vs Shift+Enter, slash commands, drafts); interactions (hover toolbar, long-press,
  right-click, swipe, keyboard shortcuts); every state (empty, loading, error, offline, no results);
  copy style; measured colors, fonts, spacing, radii, icon style and density in light and dark;
  motion; what changes on small screens.
- **Every secondary surface**, not only the main screens: thread / replies view and its header,
  message info (read-by), reactions list, emoji / sticker picker, context and hover menus, confirm
  dialogs, toasts, image / video viewer, forward picker, call screens. Each one is an inventory row
  with the target's design. Users judge a clone by these, and the kit opens several of them by itself
  (hover toolbar → Message info, reply count → thread). Each one is themed to the target, rebuilt
  (L4), or hidden. A kit default left in place is not acceptable.
- **Message chrome** (avatar, name, alignment, grouping) as its own rows: see *Message chrome* below.
- **Motion as its own list:** what animates and where. Examples: animated emoji in emoji-only
  messages, reactions and the reaction bar; how a sent message enters; menu and panel transitions;
  typing indicator. Each entry is a row with a level. Animated emoji assets the target owns are L6
  (use an open set such as Noto Animated Emoji, or say it's static).
- Anything you can't confirm is **unverified** and goes to the user as a question. Never fill it with
  a UI Kit default.

### Pick a build level per item
Lowest level that matches the target's behavior and look:

| Level | Meaning |
| --- | --- |
| L0 | Kit component as-is |
| L1 | Kit + props / Dashboard settings / theme tokens |
| L2 | Kit + its custom views / templates / formatters |
| L3 | Kit component hosted in **your** container (dialog, popover, side panel, sheet, route) |
| L4 | Your own UI on the Chat/Calls SDK, styled with the same tokens |
| L5 | Third-party package (only under the agreed package policy) |
| L6 | Not natively possible — label it, offer the closest alternative |

Rules: placement is never a reason to rebuild (use L3) or to keep the kit's default placement. Keep
the message list and composer on the kit where config, slots, or templates reach the target. Never
patch kit internals. Every name a level relies on (prop, slot, SDK method) is checked in the
family's docs first; if it isn't there, the item moves up a level.

**An L4 piece takes over everything the kit component did.** When your own component replaces a kit
one (a custom channel header, a custom sidebar), it must carry what the kit gave for free — call
buttons, presence, unread counts, typing — or keep the kit piece for those parts. And it **owns its
data alone**: remove the kit component it replaces, take the selection from kit callbacks instead of
re-fetching, and register each real-time listener once with cleanup. Two components fetching the
same list, or a listener added per render, is the usual cause of duplicate API calls
(`RULES.md` → *One request per need*).

**Change the kit through its API, never by editing its DOM.** Custom bubbles, emoji upgrades, time
formats and entrance animations go through the kit's templates, custom views, formatters and props.
A MutationObserver or `querySelector` script that rewrites kit markup breaks whenever the kit
re-renders or remounts a row, and the kit does remount rows (see *Sending feels smooth* below). If
the API can't reach it, move the item up a level; don't patch the kit's DOM.

### Sending feels smooth (one change, not two)
In the target, a sent message appears once and only its status changes (clock → tick). In a clone it
often appears, then jumps or re-renders when the server confirms it. Cause: the kit shows a pending
copy keyed by its `muid`, then swaps in the confirmed message with a server `id`, and the server's
`sentAt` can differ from the local one. Where the kit keys rows by id, the row remounts. React UI
Kit 7.2.4 keys each row `getId() || getMuid()` and each date separator by `sentAt`, so both remount
on success. So:

- Anything stateful in a bubble (entrance animation, loaded image, animated emoji, a custom view's
  state) must survive a remount. Key your own state by `muid` (fall back to `id`). Make custom views
  render the same result from the same message, with no "first render" effects.
- An entrance animation runs once per `muid`, never on the confirmed copy. Don't detect new rows by
  watching the DOM.
- **Check it** (an acceptance check; see *Who runs the checks* below): send a text, an emoji-only message and an image. Record frames (screenshots or a
  `requestAnimationFrame` trace of the last row's position and size) from send until it's confirmed.
  Position and size must not change, and only the status icon may change. If the kit's remount still
  shows (a flash or a restarted animation) and you can't hide it through the API, report it as a
  known kit limitation with the version. Don't call it smooth.

### Message chrome (avatar, name, alignment)
Small, but users notice it first. For each item, write the kit default next to the target in the
inventory, for your own messages and others', in a 1:1 chat and in a group:

- **Avatar and sender name.** Check the family's default; don't assume it. A kit may show them
  only on other people's messages in groups. Team apps (Slack, Discord, Teams) show both on every
  message; consumer messengers (WhatsApp, iMessage) show neither in 1:1 chats.
- **Alignment.** Bubbles left/right, or one flat left column. A kit's "all left" setting often makes
  every message count as incoming, which brings the avatar in groups but not in 1:1 chats.
- **Grouping.** Avatar once per run of messages from the same sender, or on every message. A
  per-message slot can't see the previous message, so "once per run" is usually L4; say so.
- **Also:** timestamp place, receipts, date separators, edited and deleted states.

Fix through the kit's own API, and do it yourself without asking:

1. Set the kit's alignment and avatar settings first.
2. **If the avatar or name still isn't on every message the target shows it on** (commonly 1:1 chats
   and your own messages), customize the per-message **leading view** (avatar) and **header view**
   (sender name) through the kit's slots (custom views, templates or message plugins, depending on
   the kit), for own and others' messages in 1:1 and group chats. The kit has these slots, so
   "the kit doesn't show it" is never a reason to ship without it. The family's customization skill
has the verified "how". If it doesn't cover your platform yet, find the slot in the family's docs and
check every name before using it. **Check:** open a 1:1 chat and a group and compare your own and
others' messages with the target.

### Calls, huddles and other live features
If the target has calls of any kind, the plan includes calling and the hand-off pulls in
`cometchat-<family>-calls` — calling is OFF until its Calls SDK is installed and enabled at init, so
a clone that only themes the UI shows no working call.

- **1:1 voice/video** → the kit's call buttons + incoming/outgoing call surfaces (L0–L1).
- **Where the live call shows is an inventory row**, not just the start button: full screen, a
  docked bar (Slack's huddle sits at the bottom of the sidebar and expands into a window), a
  floating mini window, or inline. If the kit's ongoing-call screen opens full screen (the family's
  calls skill says), a docked or mini target means that screen is a kit default left in place.
- **Persistence features** the target has and CometChat doesn't (huddle threads, notes, screen
  drawing) are L6 — say so in the plan.

**Huddle / drop-in room pattern** (start a live audio session in a channel; others see it's active and
join; no ringing). Same on every platform:

1. **Start:** a group call, audio-only, started from the channel header. Send the same group-call
   ("meeting") message the kit's own group call button sends, so the channel shows a Join entry and
   the conversation list updates. Use the group's id as the session id, so the whole channel shares
   one room. Group calls never ring.
2. **Join:** replace the kit's Join entry (its call bubble) so joining opens YOUR container, not the
   kit's full-screen call screen.
3. **Dock:** join the session INTO your own fixed-size container through the Calls SDK (generate the
   call token, then join with your container as the target). Mounting the kit's ongoing-call
   component in your panel may not dock it: some kits always open it full screen.
4. **Indicator:** "huddle active" and who started it from the latest meeting message; the live
   participant list only from the Calls SDK's participant events (look them up, never guess).
5. **Leave:** leave the session and stop the mic and camera when the dock closes; keep the dock
   mounted while the user switches channels.

Levels: L3–L4. The verified "how" for each family is in `cometchat-<family>-calls` → *Huddle / docked call*
(and the message-chrome how-to in `cometchat-<family>-customization`). If your family's skill lacks it,
build the same five steps from that family's Calls SDK and UI Kit docs, check every name, and mark
the row unverified in the plan.

**Done means connected, not rendered:** a call is only done when two different users in two
browsers or devices connect and hear/see each other. If you can't run that yourself, say calling
is **built but not verified**, give the user the two-user check, and never report it as working.

### Sample data
After login, if the lists are empty, the clone looks dead — but **never send messages, reactions or
calls as users, or create users and groups, without asking** (`RULES.md` → *Sample data*). Say the
app has no conversations yet and ask whether to create clearly marked sample data (which app, how
many users, channels and messages); create it only after a yes, outside the app's code, and list
what was created and how to remove it.

### Beat 3 — PLAN
The plan artifact (`plan-artifact.md`) gains a **Clone inventory** section: the table below, also
written to `cometchat-requirements.md` at the project root.

| # | Item | Target behavior (entry → container → close) | Level + one-line reason | Effort | Scope |
| --- | --- | --- | --- | --- | --- |

In chat, give a short summary: the proposed scope, the items that need a decision (L5/L6, unverified
details, Dashboard actions such as enabling Search), and the file path. One "go" approves the proposed
scope; the user can cut or add rows in the file instead.

### Beat 4 — hand-off
The directive to `cometchat-<family>-core` carries the clone inventory, the level per item, and the
measured tokens, and pulls in `cometchat-<family>-customization` for theming and `cometchat-<family>-calls` when the target has calls or huddles. The build then runs
**one item at a time**: build it at its level, compare it with the target (behavior first, then
looks), fix the differences, then move on.

**Design sync:** one token source measured from the target; the kit is themed from it (including
menus, pickers, dialogs, reaction chips, badges, and on web the filter-tinted icons) and every L4 piece
uses the same tokens, so nobody can tell kit parts from custom parts.

**Who runs the checks.** Compare with the target from the code, the kit's docs and the user's
screenshots while you build. The runtime checks in this file (sending messages, screenshots, frame
traces, the network log, a two-user call) are the **acceptance checklist you hand to the user**: run
them yourself only when the user asked you to test or verify (`RULES.md` → *Verification scope*),
and send messages for them only after a yes to sample data (*Sample data* above). Otherwise list each
check with the steps to run it, and report those rows as built, not verified.

**Done =** every approved row built at its level or explicitly left out; each feature opens, is
reached, and closes like the target; each request appears once in the network log; calls connect
between two users (or are reported as not verified); no data was created without a yes; side-by-side screenshots (light + dark, desktop + mobile) show no
difference the user didn't agree to, **including every secondary surface** (open each one: thread,
message info, reactions list, pickers, menus, dialogs, viewer, call screens); every message-chrome
row matches in a 1:1 chat and a group, for your own messages and others' (avatar, name, alignment);
a live call opens in the target's container (docked, mini or full screen); every motion row
**actually moves** (two frames ~300 ms apart differ; a static fallback counts as not done); sending
is one visual change (above); no unverified detail shipped as a guess. Report against the plan:
done, left, and not possible.
