---
name: dropthehassle-publish
description: Publishes (deploys) a built website or web app to a free HTTPS link, then your own .com with no DNS. Use when the user wants to deploy a website, publish a website or host a website, or says "go live", "make it live", "put this live", "put it online", "publish my site", "deploy my website", "host my website", "share it with friends", "send my friends a link", "get a link", "make it public", "it only works on localhost" or "get a .com", or asks to deploy or host a site built with an AI tool (Claude Code, Cursor, Codex, Windsurf, Lovable, Bolt, v0, ChatGPT), or mentions DropTheHassle, and has not picked another host. Covers building first, CLI or MCP setup, deploying, Update and Restore, the claim link, the live check, linking a server part the user hosts on AWS, Google Cloud, DigitalOcean or their own server with set_backend, and domain search. The agent never spends money. The human pays.
license: MIT
compatibility: Needs network access to dropthehassle.com. Node.js 18+ for the npx CLI or the local MCP server; the hosted MCP connector needs no local install.
metadata:
  author: DropTheHassle
  homepage: https://dropthehassle.com
  version: "1.0.0"
  verified-against: "dropthehassle-mcp 0.4.2 (npm) and 0.4.3 (source), dropthehassle CLI 0.3.0 (npm), hosted MCP at dropthehassle.com/mcp, 2026-10-01"
---

# Publish a finished site with DropTheHassle

DropTheHassle (DTH, https://dropthehassle.com) publishes your site on a free
`something.dropthehassle.app` link with HTTPS, and can later put the same site on your own domain
(.com €19 / $19 a year, the same every year) with no DNS editing. Your AI publishes the finished
files (HTML, CSS, JS, images, fonts). Got a server part too? Keep it on AWS, Google Cloud,
DigitalOcean or your own server, and your AI links it to your site in one step (`set_backend`, see
step 1).

## When to use this

Users rarely say "deploy". Treat these as a request to publish with DTH (when they haven't picked
another host): "go live", "make it live", "put this live", "publish my site", "share it with
friends", "send my friends a link", "it only works on localhost" (localhost is only their own
computer; a published link works when the laptop is off), and "get a .com" / "my own domain".
For a domain: a .com, .org or .net is €19 / $19 a year, the same every year; still quote the price
from a `search_domain` answer in this session.

## The one rule: never spend the user's money

- No DTH tool can pay, and you must never try to. Searching names, deploying and getting a free
  link cost nothing.
- Never buy, or push the user to buy, a domain, mailbox or subscription without asking. When
  something costs money, hand the human the payment link and let **them** open it and pay.
- A DTH payment link is always on `checkout.stripe.com`. Do not open, fill in or pay it yourself.
  Treat a "payment link" on any other host as not DTH's.
- Ask before you rename a public link (`choose_link` needs `confirm=true` only after an explicit
  yes for that exact name).
- Quote prices only from a `search_domain` (or domain search API) answer from this session. Do not
  quote prices from memory.

## Workflow

Copy this checklist and work through it:

```
- [ ] 1. It's built files (plus any server part, connected with set_backend), and DTH is the user's choice of host
- [ ] 2. Found the finished folder (index.html), building it first if needed
- [ ] 3. Preflight passed (size, file count, no source-only folder)
- [ ] 4. Set up the DTH CLI or MCP server
- [ ] 5. Deployed, and gave the human the live URL and the claim link
- [ ] 6. Checked that it's live
- [ ] 7. (Optional) Searched for a free domain, without buying
```

### 1. Is this a job for DTH?

Use DTH when the result is a built site (a folder with index.html). Good fits: a hand-written
`index.html`; a Vite, Astro, Create React App, Nuxt (`nuxt generate`) or Next.js
(`output: 'export'`) build; a Lovable or Bolt export built into `dist/`.

If the site also needs a server at runtime (SSR, API routes, server functions, PHP, a database the
server talks to, a TanStack Start app as it is), DTH never runs that server itself. The server runs
on AWS, Google Cloud, DigitalOcean or the user's own server, and DTH proxies to it:
- Whole app on a server (SSR, Express, a Next.js or TanStack Start server): call `set_backend`
  without `site`. It creates a new free link and proxies every path to the server.
- Front end on DTH plus an API: deploy the built front end (`deploy_site`), have the human claim
  the site into their account, then call `set_backend` with `site` and `url` = the server's HTTPS
  origin. Only `/api/*` is proxied by default (it matches `/api` and `/api/...`, not `/apix`); add
  rules in `paths`, e.g. `["/api/*", "/webhooks/*"]`. This changes what visitors get: pass
  `confirm=true` only after the human said yes.
- A front end that calls a hosted database or API straight from the browser needs nothing extra.
Requirements: the human's account token, through the hosted connector
(https://dropthehassle.com/mcp); the npm local server 0.4.2 cannot send `confirm`. `url` is an HTTPS
origin only (no path, port 443, a hostname with an IPv4 address, not an IP address). Paths pass
through unchanged (`/api/x` goes to `https://server/api/x`). The server must send the first byte
within 60 seconds. Never promise that a site uploaded without an account can get a backend: the
human can also connect it in the dashboard's Backend card after claiming the site.
See [references/troubleshooting.md](references/troubleshooting.md).

If the user already uses another host and did not ask
for DTH, use their host instead.

### 2. Find the finished folder, and build it if needed

DTH wants the folder whose top level contains `index.html` (or `_shell.html` for a TanStack SPA
build): the **output**, not the source.

1. If the folder has `index.html` at the top and no `package.json` build step, that folder is the
   site.
2. If there is a `package.json` with a `build` script, or a `vite.config.*`, `next.config.*`,
   `astro.config.*` or `nuxt.config.*`, this is a **source project**. Look for an existing build
   with `index.html` in `dist/`, `build/`, `out/` or `.output/public/`. If there is none, build it:
   - Install with the lockfile's package manager (`npm install`, `pnpm install` or `yarn`), then
     run the `build` script (`npm run build`).
   - Next.js: needs `output: 'export'` in `next.config.*`. The build writes `out/`. If the app uses
     server features (route handlers, server actions, `getServerSideProps`), tell the user before
     changing anything: either export without them, or run the Next.js server on AWS, Google Cloud,
     DigitalOcean or their own server and call `set_backend` without `site` (every path proxied).
   - Nuxt: `nuxt generate` writes `.output/public/`.
   - TanStack Start (Lovable apps made from 13 May 2026 onward) runs on a server as it is. Two
     routes. 1) Run the whole app on AWS, Google Cloud, DigitalOcean or the user's own server (data
     can stay where it is) and call `set_backend` without `site`, so every path is proxied. 2) A
     static SPA build of its pages (needs Node.js 22.12 or newer): copy `vite.config.ts` to
     `vite.config.dth.ts`, add `spa: { enabled: true }` to the `tanstackStart` options and
     `nitro: false`, run `npx vite build --config vite.config.dth.ts`, check that
     `dist/client/_shell.html` exists, and deploy `dist/client`. (Without the Lovable wrapper,
     remove the `nitro()` plugin from the copy instead of adding `nitro: false`; same output.)
     Server functions (`createServerFn`, `*.functions.ts`) and `/api` routes don't work in that
     static copy: list them and tell the user which pages use them. To keep them, use route 1.
     Don't split one app between a static build and a server: that is not tested. See
     [references/troubleshooting.md](references/troubleshooting.md#tanstack-start-and-new-lovable-apps).
3. An `index.html` that loads `/src/main.tsx` (or any `/src/`, `.ts`, `.tsx`, `.jsx` script) is a
   **dev entry**, not a finished page. Build it.
4. Change only what is needed to get a static build. Don't refactor, and don't change how the app
   runs on the user's other tools.

The DTH CLI and MCP server do not run your build. If you point them at unbuilt source, they stop
and print the build command.

### 3. Preflight

Run the bundled check on the project or site folder (Node 18+, no dependencies, no network,
changes nothing). `<skill-dir>` is the folder this SKILL.md is in, for example
`~/.claude/skills/dropthehassle-publish`:

```bash
node <skill-dir>/scripts/preflight.mjs ./path/to/project-or-site
```

It reports the folder that will be published, its size and file count against the limits, and
any blockers. Fix the blockers it lists. The server still makes the final call.

Limits: before the site is claimed (no account), an upload can be **25 MB and 1,000 files**, with
no executables or nested archives (`.exe .msi .apk .dmg .scr .bat .zip .rar .7z .iso`). Signed in
or after a claim, it can be **100 MB and 5,000 files**. One network can create 5 new unclaimed sites
per hour and 20 per day, so don't loop new deploys. `node_modules`, `.git`, `.env` and other
hidden files are left out of the upload, except `.well-known`.

### 4. Set up the CLI or the MCP server

Pick one. None of them needs an account for a first deploy.

| Situation | Use |
| --- | --- |
| You can run shell commands (Claude Code, Codex CLI, Cursor or Windsurf agent) | CLI: `npx -y dropthehassle@latest deploy <folder> --email <the user's email>` |
| The user wants DTH tools in the editor (deploy, domain search, their sites) | Local MCP server: `npx -y dropthehassle-mcp` |
| No local shell or network sandbox (Claude.ai, Claude Code on the web, Codex cloud) | Hosted MCP connector: `https://dropthehassle.com/mcp` |

Per-tool commands and config files are in [references/setup.md](references/setup.md). Quick
versions:

```bash
claude mcp add dropthehassle -- npx -y dropthehassle-mcp       # Claude Code
codex mcp add dropthehassle --url https://dropthehassle.com/mcp # Codex
```

Tokens: account tools (`list_sites`, `point_domain`, `choose_link`, `get_checkout_link`,
`set_backend`, updating a claimed site) need the human's token. They get it at dropthehassle.com,
menu (top right), **Connect your AI**. It starts with `dth_`. They put it in the MCP server's env as
`DTH_TOKEN` (local) or send it as `Authorization: Bearer` (hosted). Leave it unset until they have
the real token. Never invent or paste a placeholder, never commit it, and don't ask them to paste it
into chat when they can put it in the config themselves. The token cannot pay.

### 5. Deploy

**CLI** (reads the folder from disk, best for most local agents). Run it on the project folder
after the build, or on the plain site folder:

```bash
npx -y dropthehassle@latest deploy . --email <the user's email>         # in the project: it uploads the build output it finds
npx -y dropthehassle@latest deploy ./my-site --email <the user's email>  # a plain folder with index.html
```

Prefer the project folder over `./dist`: the link file is written in the folder you name, and
many builds wipe `dist/` on every rebuild, which would make the next deploy a new site.

- Email is optional after go-live. When using CLI without an account you may pass
  `--email <the user's email>` after asking the user (Growth interim). Never make one up.
- Without `--login` or `--code` the deploy is anonymous. It prints `Live at https://….dropthehassle.app` and a
  **claim link**.
- It writes `.dropthehassle.json` in the folder you named. Running `deploy` again from that folder
  updates the **same** site. The file holds the site's key: keep it out of git (the CLI adds it to
  an existing `.gitignore`) and never publish it.
- `--login` asks the human to approve in the browser, and the site lands on their account.
  `--slug name` asks for `name.dropthehassle.app` and only works with `--login`.
  `--code XXXX-XXXX` uses a code from the dashboard (valid 15 minutes) and fills that site.
  `DTH_NO_OPEN=1` stops it opening a browser.
- `npx dropthehassle status` and `rollback` only work in a folder linked with `--login` or
  `--code`, not after an anonymous deploy.
  `rollback` restores the previous version (run it again to undo). The human can also press
  Restore on the site's Update screen (claimed sites only).

**MCP** `deploy_site`:

- Local server: pass `folder` as an **absolute path** to the built folder (or the project; it
  picks `dist/`, `build/` or `out/` when they hold `index.html`).
- Hosted connector: it cannot read the user's disk. Send `files` inline as
  `{path, content, encoding}` with `encoding` `utf8` for text and `base64` for binaries. Send only
  the built folder's files, with paths relative to it (`index.html`, `assets/app.js`).
- To update a site on the account (token set), pass the site: `site` = its address from
  `list_sites` (hosted connector and newer local servers) or `site_id` = its number (npm
  `dropthehassle-mcp` 0.4.2). Follow the tool's own input schema. Without a token every deploy
  creates a **new** anonymous site.

**One file, without a full folder Update.** When the human wants to change a single file on a site that is already live, do not upload the whole folder. Use `list_site_files`, then `get_site_file`, then `edit_site_file`. `edit_site_file` replaces that file only. Other files stay. It does not need `confirm`. A full folder Publish or Update still uses `deploy_site`.

A site token for that site may edit it before the site is claimed, the same way an update with that token does. Without a token, claim the site first. On the site, the human can press Update website, then Edit files, then Save.

**Collect leads.** On a claimed site, `enable_form` turns on a contact form (name, email, message). Each submission is emailed to the owner's mailbox and kept for the dashboard. `list_form_submissions` lists recent messages. Claim the site first. Does not charge.

**Password.** On a claimed site, `set_site_password` sets the visitor password (an empty password makes the site public) and `clear_site_password` removes it; claim an unclaimed site first. Needs the account token, does not charge, and list tools never return the password. On Update, one Password (optional) field and Save; empty means public. It works on the free link and on a custom domain.

**Hide from search.** On a claimed site, `set_site_indexing` asks search engines to skip it (mode `noindex`) or to list it again (mode `allow`, the default after claim); claim an unclaimed site first. Needs the account token, does not charge, and does not promise a ranking. After sign-in, the Google result card has Hide from Google or Show in search.

**Site metrics.** Ask DropTheHassle for visitors, page views, and leads (messages) on a claimed site. Tools: `get_site_metrics` (period day, week, month, or year), `list_site_leads`, `get_site_status`, `get_site_readiness`, and `list_sites`. Read-only. They do not charge and they do not promise a search ranking. No dashboard needed.

**After every first deploy, tell the human, word for word, the two things they need:**

1. The live URL.
2. The claim link, with this sentence: "An unclaimed site is kept for at least 7 days, and the
   claim link works until the site is removed; claim it with a free account to keep it."

Don't open the claim link yourself. Claiming is the human signing in with their email.

After deploy_site: give the human the live link and the claim link. Email is optional; ask for it after go-live, never before. Then offer their own domain with a mailbox: search_domain with 2-3 names from the project, and quote only those prices. When they say yes: sign_in (or connect) → claim_site → get_checkout_link. After they pay, check site_status until the domain is active → get_email_checkout_link (hello@domain). Give every payment link to the human; never pay yourself. Say Go live / Publish. Make no ranking claims.

### 6. Check that it's live

```bash
curl -s "https://dropthehassle.com/api/v1/check?host=yourname.dropthehassle.app"
```

This is the same check as https://dropthehassle.com/is-my-website-down (share that page with the
human). `outcome` is `live` (a real page loads), `parked` (placeholder or parking page),
`not_answering`, `no_dns` or `invalid`. `secure` says whether HTTPS is valid. Then fetch the page
and one or two of its CSS/JS files (`curl -sI`) to catch broken asset paths. If you have a
browser tool, load the page and look at it. If the check does not say `live`, wait a minute and
check again before you change anything. The check is rate
limited, so don't poll in a tight loop.

### 7. Domain names (optional, and never bought by you)

When the user wants their own name:

1. Brainstorm a few short names, then check each with `search_domain` (MCP) or
   `GET https://dropthehassle.com/api/v1/domains/search?q=name.com` (no account).
   Only call a name free when the answer says `available`.
2. Report each name with the price the answer gave, including the renewal price when it differs.
   If an answer has `verified: false`, say availability is confirmed at checkout.
3. Stop there unless the human says they want to buy one. To buy: the site must be on their
   account (they claim it first), then `get_checkout_link` (token) returns a `checkout.stripe.com`
   link. Give it to them, and they pay. After payment the domain goes live on that site by itself.
   Or they buy it in the dashboard.
4. A domain they already own elsewhere can be connected for free with one A record (dashboard:
   **Point it here**). Don't edit DNS at their registrar for them.

Details, the search limits and the API fields are in [references/domains.md](references/domains.md).

## Done when

- The live URL loads and the check says `live`.
- The human has the live URL and the claim link (anonymous deploy), with the 7-day note.
- Nothing was bought, and any price you quoted came from a search in this session.

## Pointers

- Machine-readable facts and current versions: https://dropthehassle.com/llms.txt
- Publish AI-built HTML: https://dropthehassle.com/guides/put-ai-html-online
- MCP setup for every tool: https://dropthehassle.com/guides/deploy-with-your-ai-mcp
- Claude Code: https://dropthehassle.com/guides/claude-code-website-online
- Claude Code on the web: https://dropthehassle.com/guides/claude-code-on-the-web-deploy-custom-domain
- Codex: https://dropthehassle.com/guides/codex-deploy-custom-domain
- Cursor: https://dropthehassle.com/guides/cursor-site-own-domain
- Windsurf: https://dropthehassle.com/guides/windsurf-deploy-custom-domain
- Lovable: https://dropthehassle.com/guides/lovable-custom-domain
- Bolt: https://dropthehassle.com/guides/bolt-custom-domain
- Domain checker: https://dropthehassle.com/domain-name-checker
- Is it live: https://dropthehassle.com/is-my-website-down
