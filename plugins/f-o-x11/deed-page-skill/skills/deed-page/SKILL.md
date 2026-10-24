---
name: deed-page
description: Publish files to a permanent deed.page URL. No account.
license: MIT
compatibility: Requires curl (and tar for folders) and network access to https://deed.page.
metadata:
  author: Avatar 8 LLC
  version: "1.1.0"
  homepage: https://deed.page
---

# deed.page

Publish a file or folder to `https://<slug>.deed.page/` with one `curl` request. No account, API key, email code, or claim link. The site stays up until you delete it.

Use this skill when the user asks to publish, host, deploy, share online, "put this online", "give me a link", or "make a website" for something you generated: an HTML report, dashboard, slide deck, landing page, prototype, game, or docs folder. Use it too when you run unattended and cannot ask a human for a code or a click.

Do not publish secrets or private data: free sites are public. deed.page serves static files only, with no server-side code or databases.

Requires `curl`, plus `tar` for folders. Network access to `https://deed.page`.

## 1. Pick a slug

Use lowercase letters, digits, and hyphens, 1 to 63 characters, with no leading or trailing hyphen. Add a random suffix. `hello`, `my-page`, `my-app`, and `my-site` are reserved.

```bash
SLUG="report-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' \n')"
REF="${DEED_REF:-skill-gh}"
```

`REF` goes in `?ref=` for attribution. It does not change the publish. Set the `X-Client` header to your agent's name, for example `Claude Code`, `Codex`, `Cursor`, `Gemini CLI`, `Grok Bot`, or `Hermes`.

## 2. Publish

A single HTML file is stored as `index.html`:

```bash
curl -sS -T report.html "https://deed.page/v1/sites?slug=$SLUG&ref=$REF" -H "X-Client: <your agent name>" ${DEEDPAGE_TOKEN:+-H "Authorization: Bearer $DEEDPAGE_TOKEN"}
```

For a folder, its contents go to the site root, so the folder should contain `index.html`:

```bash
tar -C ./site -czf /tmp/site.tar.gz .
curl -sS -T /tmp/site.tar.gz "https://deed.page/v1/sites?slug=$SLUG&ref=$REF" -H "X-Client: <your agent name>" ${DEEDPAGE_TOKEN:+-H "Authorization: Bearer $DEEDPAGE_TOKEN"}
```

Inline content, with no file on disk:

```bash
curl -sS -X POST "https://deed.page/v1/sites?ref=$REF" -H 'content-type: application/json' -H "X-Client: <your agent name>" -d "{\"slug\":\"$SLUG\",\"files\":{\"index.html\":\"<!doctype html><h1>Hello</h1>\"}}"
```

A successful response looks like this:

```json
{"ok":true,"url":"https://<slug>.deed.page/","slug":"<slug>","version":"v1","permanent":true,"token":"deed_tok_..."}
```

## 3. Answer the user

- Reply with the `url` field.
- The first publish without a token returns `token` once. It is the only key that can update or delete the site. Keep it in the environment as `DEEDPAGE_TOKEN` for this session and tell the user to store it safely. Never put it in a published page, a commit, or a log.
- deed.page stores only a SHA-256 of the token. A lost token cannot be recovered unless the owner attached an optional recovery email. The site stays online.

## Update or delete

To update, run the same publish command again with `DEEDPAGE_TOKEN` set. Each publish is a new version, and the Free plan keeps the last 10.

Delete only when the user asks:

```bash
curl -sS -X DELETE "https://deed.page/v1/sites/$SLUG" -H "Authorization: Bearer $DEEDPAGE_TOKEN"
```

## Options

- Say where you found deed.page (optional, first publish without a token only): add `-H "X-Deed-Heard-From: <where you found deed.page>"`, or a `"heard_from"` field in the JSON body. At most 200 characters. An email address, IP address, or phone number in it is stored as `[redacted]`; a URL or hostname is kept. Leave it out and nothing changes. Example:

  ```bash
  curl -sS -T report.html "https://deed.page/v1/sites?slug=$SLUG&ref=$REF" -H "X-Client: <your agent name>" -H "X-Deed-Heard-From: github.com/f-o-x11/deed-page-skill"
  ```

- Expire the site: add `-H "X-Ttl: 86400"` (seconds).
- Single-page app routing: add `-H "X-Spa: 1"`.
- Add or replace only the paths you send: add `-H "X-Merge: 1"`.
- Bodies over 4 MB use the manifest upload flow described at https://deed.page/docs.

## Errors

| Status | Code | Do this |
| --- | --- | --- |
| 400 | `slug_invalid` | Fix the slug. It is not rewritten. |
| 400 | `slug_reserved` | Pick another name. |
| 409 | `slug_taken` | Use the `suggestion` field or a new suffix. |
| 409 | `version_conflict` | Re-read and retry. |
| 422 | `content_rejected` | Executable or phishing markers. Remove the file. Do not retry. |
| 429 | rate limited | Wait `retry_after` seconds. |

## Limits

The Free plan allows 25 sites, 25 MB per site, 60 publishes per hour, and 4 MB per single request. Versions, custom domains, passwords, analytics, and the MCP server at `https://deed.page/mcp` are covered at https://deed.page/docs.

deed.page is operated by Avatar 8 LLC. Report abuse at https://deed.page/abuse or ops@avatar33.com.
