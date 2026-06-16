---
name: hermes-tweet
version: 0.1.6
author: Xquik
description: Use Xquik from Hermes Agent for X search, posting, replies, likes, retweets, follows, DMs, monitors, extraction jobs, draws, media, and trends.
tags:
  - hermes-agent
  - xquik
  - twitter
  - x
  - social-media
  - automation
metadata:
  version: 0.1.6
  author: Xquik
  tags:
    - hermes-agent
    - xquik
    - twitter
    - x
    - social-media
    - automation
---

# Hermes Tweet

Use Hermes Tweet when the user wants to automate or inspect X through Xquik.

## When to Use

Use this skill for Hermes Agent sessions that need X/Twitter data or controlled
X actions through the Hermes Tweet plugin.

Use this skill especially for social listening, launch monitoring, support
triage, creator research, brand research, giveaway audits, community audits,
and controlled publishing workflows.

Use `tweet_explore` first when the user asks for a capability, endpoint, route,
or Xquik API surface. Use `tweet_read` only after a read-only endpoint is known.
Use `tweet_action` only after the user requests a write, private read, monitor,
webhook, extraction job, giveaway draw, or media operation that requires action
permissions.

## Workflow

1. Use `tweet_explore` to find the endpoint.
2. Use `tweet_read` for public read-only endpoints.
3. Use `tweet_action` only for writes or private reads after stating the exact endpoint and payload.

## Decision Rules

- IF the task is endpoint discovery, THEN call `tweet_explore` with a short
  query.
- IF the endpoint method is `GET` and the catalog does not mark it as an
  action, THEN call `tweet_read`.
- IF the endpoint method is not `GET`, or the route touches private account
  state, THEN call `tweet_action` only when actions are enabled and the user has
  approved the operation.
- IF `tweet_action` is unavailable or disabled, THEN explain that action tools
  are intentionally gated by `HERMES_TWEET_ENABLE_ACTIONS=true`.
- IF `XQUIK_API_KEY` is missing, THEN ask the user to set it in the Hermes
  runtime environment without requesting the key value in chat.
- IF Hermes lists the plugin as `not enabled`, THEN tell the user to run
  `hermes plugins enable hermes-tweet` or reinstall with `--enable`.
- IF the plugin is installed as a project-local `.hermes/plugins/` copy, THEN
  remind the user that Hermes requires `HERMES_ENABLE_PROJECT_PLUGINS=true` for
  trusted repositories.
- IF the task is unattended, scheduled, gateway-driven, or cron-driven, THEN
  prefer `tweet_read` and keep `tweet_action` disabled unless the workflow has a
  clear approval step.
- IF the user is in Hermes Desktop with a remote gateway profile, THEN remind
  them that Hermes Tweet must be installed, enabled, and configured on the
  remote Hermes host where plugin tools execute.
- IF the user uses the Hermes dashboard for gateway administration or
  credentials, THEN keep Hermes Tweet secrets in the runtime environment and do
  not ask for key values in chat.

## Safety

- Never ask for or reveal API keys, signing keys, passwords, cookies, or TOTP secrets.
- Never pass credentials in tool arguments.
- Use only catalog-listed `/api/v1/...` endpoints.
- Copied endpoint URLs are accepted only when they resolve to catalog-listed paths.
- Do not use account connection, re-authentication, API key, billing, credit top-up, or support-ticket endpoints.
- For posting, deleting, following, DMs, profile changes, monitors, webhooks, extraction jobs, and draws, summarize the action before calling `tweet_action`.

## Pitfalls

- Do not guess endpoint paths. Always use the catalog returned by `tweet_explore`.
- Do not treat a slash command prompt as proof that Hermes registered the
  command. Verify slash commands through an active Hermes session or plugin
  registry test.
- Do not use bare `hermes tools` for scripted diagnostics. Run
  `hermes tools list` instead.
- Do not assume installation means execution. Current Hermes Agent versions
  discover third-party plugins before they are enabled.
- Do not assume the Desktop app stores plugin secrets for a remote gateway.
  Configure `XQUIK_API_KEY` where the Hermes runtime executes.
- Do not retry writes through alternate routes after a policy, auth, or account
  state error.
- Do not include secrets in examples, logs, prompts, issue bodies, or tool input.

## Hermes Agent v0.16.0 Surfaces

Hermes Agent v0.16.0 added a native Desktop app, remote gateway profiles, a
larger web dashboard, and a command palette that can surface skills and quick
commands. Hermes Tweet uses the same plugin entry point on all of those
surfaces:

- Install and enable `hermes-tweet` on the Hermes runtime host.
- Put `XQUIK_API_KEY` in the runtime environment or `~/.hermes/.env`.
- Keep `HERMES_TWEET_ENABLE_ACTIONS=false` unless the session intentionally
  allows account-changing actions.
- Use Desktop, TUI, CLI, or gateway sessions for interactive slash commands such
  as `/xstatus` and `/xtrends`.

## Examples

Search tweets:

```json
{"query":"tweet search","method":"GET"}
```

Then call:

```json
{"path":"/api/v1/x/tweets/search","query":{"q":"AI agents","limit":25}}
```

Post a tweet:

```json
{"query":"post tweet","include_actions":true}
```

Then call `tweet_action` with:

```json
{"path":"/api/v1/x/tweets","method":"POST","body":{"account":"@example","text":"Hello from Hermes Tweet"},"reason":"Post the user-approved tweet."}
```

## Testing

After installing or upgrading the plugin in Hermes Agent:

1. Run `hermes plugins enable hermes-tweet` unless the install used `--enable`.
2. Run `hermes plugins list` and confirm the plugin is `enabled`.
3. Run `hermes tools list` and confirm the `hermes-tweet` toolset is enabled.
4. Confirm `tweet_explore` is available without `XQUIK_API_KEY`.
5. Confirm `tweet_read` appears only when `XQUIK_API_KEY` is configured.
6. Confirm `tweet_action` stays hidden or disabled unless `HERMES_TWEET_ENABLE_ACTIONS=true`.

Useful CLI checks:

```bash
hermes plugins enable hermes-tweet
hermes tools list
```

## Version History

- Unreleased: Refresh current Hermes Agent opt-in plugin lifecycle guidance and
  workflow positioning.
- 0.1.6: Refresh catalog wording from current Xquik OpenAPI.
- 0.1.5: Add registry-compatible nested metadata and clearer Hermes runtime guidance.
- 0.1.4: Add public registry frontmatter for skill directory discovery.
