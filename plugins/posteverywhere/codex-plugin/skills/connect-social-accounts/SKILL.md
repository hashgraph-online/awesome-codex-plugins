---
name: connect-social-accounts
description: Connect a social media account or channel to PostEverywhere. Use when the user wants to add Instagram, TikTok, YouTube, LinkedIn, Facebook, X, Threads, Pinterest, Bluesky, Telegram, Discord or WordPress, or when a post can't go out because no account is connected.
---

# Connect social accounts

Accounts connect in one of two ways, depending on the platform.

## Sign-in platforms

Instagram, Facebook, LinkedIn, X, YouTube, TikTok, Threads and Pinterest connect through the platform's own sign-in.

1. Call `create_connect_link` with the `platform`.
2. Give the user the link. It works for about 10 minutes, in any browser.
3. Tell them what the platform will ask for:
   - **Instagram:** a Business or Creator account. A personal account can't be connected for posting.
   - **Facebook:** a Facebook Page they manage. Tick every Page and permission on Facebook's screen.
   - **YouTube:** a YouTube channel on the Google account, and every YouTube permission ticked on Google's screen.
   - **TikTok:** allow every permission on TikTok's screen.
4. After they finish, call `list_accounts` to confirm the account appears.

## Platforms that use a key or password

These connect directly in the conversation with `connect_credential_account`. The user gives you the values; never guess them.

- **Bluesky:** `handle` and an `app_password` from Bluesky Settings, App Passwords. Never the main password.
- **Telegram:** a `bot_token` from @BotFather, and the `channel` (@username or chat id). The bot must be an admin of the channel.
- **Discord:** a `webhook_url` from Server Settings, Integrations, Webhooks.
- **WordPress** (self-hosted, WordPress 5.6 or newer): `site_url`, `username`, and an `app_password` from Users, Profile, Application Passwords. Never the login password.

## When an account stops working

Call `create_reconnect_link` with the `account_id` and give the user the link. For key and password platforms, call `connect_credential_account` again with new values.

## Plan limits

Each plan includes a number of accounts. If connecting fails because the limit is reached, tell the user plainly. They can remove an account they no longer use, or change their plan at app.posteverywhere.ai.
