---
name: agency-clients
description: Work safely across several clients or brands in PostEverywhere. Use when the user manages social media for more than one client, brand or business, mentions a client by name, asks to switch clients, or when the connected accounts belong to different companies.
---

# Agency clients

One wrong account means a client's post goes out on another client's page. Check which client and which accounts before every action.

## How the connector works

The connector works inside one PostEverywhere workspace: the one that was active when the user connected it in Claude. It sees only that workspace's accounts, posts, media and campaigns. It can't switch workspaces. To work on a client in another workspace, the user switches workspace in the PostEverywhere app, then disconnects and connects the PostEverywhere connector again in Claude. Say this plainly when the client they name isn't in the current workspace.

## Steps

1. **Check where you are.** At the start, call `get_me` and tell the user the workspace name. Call `list_accounts` and list the accounts by platform and username.
2. **Match accounts to clients.** If one workspace holds several clients' accounts, ask the user which accounts belong to which client. Write the map back to them, for example "Acme: Instagram @acme, LinkedIn Acme Ltd". Use it for the rest of the conversation.
3. **Name the client before every action.** Before you create, change, schedule, publish, retry or delete anything, say the client name and the exact accounts, and ask the user to confirm.
4. **Never mix clients.** One post goes to one client's accounts only. If the user asks for a post for two clients, make two separate posts, each written for its client.
5. **Label the work.** Name the client next to every post id in your summaries. For scheduled posts, a campaign per client helps: find or make one with `list_campaigns` and `create_campaign` (for example "Acme: October"), and pass its `campaign_id` on each post in `bulk_create_posts`. Drafts are not linked to campaigns. Don't add the client name to the post text unless the user wants it there.
6. **Filter by client.** When listing or reporting, use `list_posts_advanced` with `account_id` (one call per account), or `campaign_id`, so one client's report never shows another client's posts.
7. **Keep media apart.** Check media belongs to the right client before you attach it. `list_media` shows the whole workspace library.

## Be careful

- If an account name is unclear (two similar pages), ask. Never guess.
- Reports for a client show only that client's accounts. Don't mention other clients' results.
- Follow each client's own voice guide when the user has one (see `brand-voice`). Don't reuse one client's voice for another.
