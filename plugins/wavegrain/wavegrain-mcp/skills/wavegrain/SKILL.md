---
name: wavegrain
description: Make, edit, schedule and export TikTok slideshows and Instagram carousels in the user's Wavegrain account through the Wavegrain MCP server. Use when the user asks for a slideshow or carousel post, wants to copy the look of a post they link, plans a week of social posts, changes slide text, puts posts on their Wavegrain Calendar, or exports slides.
---

# Wavegrain

Wavegrain (https://wavegrain.com) makes curated TikTok slideshows and Instagram carousels for your brand on autopilot.
It turns a topic, a linked post or an image board into a finished TikTok slideshow or Instagram carousel for one of the user's brands.
This skill tells you when to use it and which tools to call.
The full tool list and limits are on https://wavegrain.com/mcp.

## When to use it

- The user wants a slideshow or carousel post about a topic.
- The user links an Instagram or TikTok post and wants one like it for their brand.
- The user wants a week of posts planned and put on their Calendar.
- The user wants to change slide text, swap a photo, reorder slides or export a slideshow.
- The user asks what is scheduled, what a post costs or how many credits are left.

## Connect first

The server address is `https://wavegrain.com/api/mcp` (Streamable HTTP).

- claude.ai, the Claude app and ChatGPT sign in with OAuth: add a custom connector with the server address, then sign in to Wavegrain and choose the permissions and a daily credit limit.
- Claude Code, Codex, Cursor, VS Code and other tools send an access key.
  The user makes one in Wavegrain under Settings, AI agents, and saves it in the `WAVEGRAIN_MCP_TOKEN` environment variable.
  Never ask the user to paste the key into the chat, and never write it into a file in a project.

The tools work only for an account with a Wavegrain plan.
When a tool answers with a plan message, tell the user and link https://wavegrain.com/pricing.

## Permissions

Each key or connected app has its own permissions, and each tool description ends with the permission it needs.

| Permission | What it allows |
| --- | --- |
| `read` | Read brands, briefs, formats, slideshows, the Calendar, collections and credits. Free. |
| `write` | Change saved work without spending credits: slide text, photos, order, captions, Calendar slots and exports. |
| `generate` | Spend the user's credits to make slideshows, brands and images, within the limit each call names. |
| `post` | Post to the user's connected accounts after the user confirms a summary. Never on by default. |
| `approve` | Approve finished slideshows for posting. Off until the user turns it on for that key in Settings. |

If a tool says a permission is missing, nothing changed.
Tell the user which permission the key needs; do not retry.

## Common jobs

### Make a slideshow from a topic

1. `list_brands` to find the brand. Ask the user if there is more than one and none is clearly meant.
2. `estimate_cost` to price the run, and tell the user the credits.
3. `generate_slideshow` with the topic, the brand and `maxCredits`. It answers a `jobId` at once.
4. Poll `get_generation_status` with the `jobId` until the state is `ready` or `failed`. Making a slideshow can take a minute or two.
5. `get_slideshow` to show the slides, then offer edits or export.

### Make one like a post the user links

1. `copy_post` with the link and the brand. It makes a finished slideshow in that look and answers a `jobId`.
2. Poll `get_generation_status` as above.
3. To make another post in the same look, call `copy_post` again with the `styleId` from the answer and a new topic.

`generate_slideshow` and `copy_post` take an `idempotencyKey`, a string you choose such as a UUID.
Send the same key when you retry the same call, so a retry never charges twice.

### Plan a week of posts

1. `get_brand_brief` and `get_playbook` to learn the brand's voice and what makes a good hook.
2. `plan_week` to find the free Calendar slots.
3. Make each slideshow as above, then `schedule_slideshows` to put them in the slots.

### Edit and export

- `update_slide_text`, `set_slide_image`, `reorder_slides`, `edit_slides` and `update_caption` change a slideshow without spending credits.
- `export_slideshow` answers a download link that works for ten minutes.

### Post

`post_slideshow` needs the `post` permission.
The user always confirms a summary of what goes where before anything is posted: in the chat where the app draws a Post button, or else on a page in Wavegrain.
Network choices, such as TikTok visibility, stay with the user.

## Rules

- Always name the credits before a call that spends them, and keep `maxCredits` to what the user agreed.
- Reading is free, and so are edits, scheduling and exports.
- When a run fails, `get_generation_status` says what was charged; tell the user.
- If you are unsure which brand, format or account the user means, ask.

## Help

- Docs and setup per app: https://wavegrain.com/mcp
- Support: support@wavegrain.com
