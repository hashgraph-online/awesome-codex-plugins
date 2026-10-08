# PlaceCall ☎️

**The internet has APIs. The real world has phone numbers.**

Give your agent a voice to call any US business, handle reservations, gather
information, get quotes. Handles IVRs & hold. Returns outcome + transcript.
First 250 calls free.

```sh
curl -s -X POST https://api.voygr.tech/calls \
  -H "X-API-Key: $PLACECALL_API_KEY" -H "Content-Type: application/json" \
  -H "X-Client-Surface: gh-repo" \
  -H "X-Client-Agent: ${CLAUDECODE:+claude-code}${CURSOR_AGENT:+cursor}${CODEX_SANDBOX:+codex}${GEMINI_CLI:+gemini-cli}" \
  -d '{"target_phone":"+1XXXXXXXXXX","brief":"Call this restaurant and ask what time the kitchen closes tonight.","language":"en"}'
```

**Authentication:** every request carries your key in the `X-API-Key` header.
Get one at <https://api.voygr.tech/checkout> - it arrives by email.

## What PlaceCall does

Give PlaceCall a US number (or a list) and a task in plain English - from
making an inquiry to requesting a quote or completing a booking - and it
dials, navigates IVRs and hold, talks to a business, and returns a verified
outcome + transcript + recording.

No number? Just describe the place: "a romantic restaurant in Chicago,
Saturday 8pm". PlaceCall finds candidates, explains why it picked them, and
writes the call brief for you.

**Put the full job in the brief** - what to ask, who it's for, names, dates,
party size, callback number, and desired outcome. The agent reads the brief,
then gets things done. If necessary - agents will ask questions mid-call.

## What your agents can finally do

- 🍽️ Book / cancel / reschedule tables and appointments
- 📦 Verify info, follow up on orders, check stock, get quotes
- ⚡️ Contact many businesses at once
- 📍 Recommend the best venue, service, or vendor when you don't have a number
- ✅ Report exactly what happened, raise a question mid-call if needed

## What you get back

Every call returns one of 17 verified outcomes, plus the full transcript and
recording - including clear failure reasons like dropped calls, busy lines,
voicemail, or wrong numbers.

## Why developers use PlaceCall

**Built for agents that need to get shit done.** Built by developers who
mapped the world - ex-Google Maps & Search team.

🎁 Your first 250 calls are on us.

If PlaceCall is useful, drop us a ⭐ - it helps a lot.

## Install
Installing the skill needs **no key** - it just teaches your agent how to call the
API. You add your key separately (next section) before placing real calls.

### Claude Code (recommended)
Two commands, no shell, no git - and it **auto-updates** from this repo:
```
/plugin marketplace add voygr-tech/placecall
/plugin install placecall@placecall
```
Claude Code asks where to install it - choose **user scope** ("Install for you")
unless you specifically want it confined to one repository. The skill then answers
to `/placecall:placecall`, and Claude reaches for it on its
own whenever you ask to call someone.

### Claude Code, without the plugin
```sh
git clone https://github.com/voygr-tech/placecall && cd placecall
./install.sh     # copies skills/placecall/SKILL.md -> ~/.claude/skills/placecall/
```
`install.sh` is a tiny convenience script - it **only** copies
`skills/placecall/SKILL.md` into your skills dir (no network, no other side
effects); you can also copy it by hand. Then start a **fresh** Claude Code session
(skills load at startup). Note that a copy never updates itself - if you want new
skills and fixes as we ship them, prefer the plugin above.

### Cowork
Same package as the Claude Code plugin, no terminal at all:

1. **Customize** > **Plugins** > **Add marketplace**
2. Paste `voygr-tech/placecall`
3. Click **Install** on the PlaceCall card

Auto-updates from this repo, like the Code plugin.

**Then do both of these, in `~/.claude/settings.json`.** Cowork has no terminal,
so the `export` in the next section has nothing to run in, and the Bash sandbox
blocks our API until you allow it:

```json
{
  "env": { "PLACECALL_API_KEY": "<your key>" },
  "sandbox": { "network": { "allowedDomains": ["api.voygr.tech"] } }
}
```

Restart Cowork afterwards. Why each half matters:

- **`env`** puts the key somewhere that survives a reboot. Setting it in a shell
  does not reach a desktop app, which never sees that shell.
- **`allowedDomains`** pre-allows `api.voygr.tech`. Claude Code pre-allows no
  domains, so without this you get a permission prompt on the first call, and if
  your organisation sets `strictAllowlist` or `allowManagedDomainsOnly` the call
  is **blocked outright with no prompt**. That is the "deep admin setting" people
  hit.

Your key sits in plaintext in that file, same trust level as the `600` env file
in the next section. `chmod 600 ~/.claude/settings.json` if you want the file
permissions to match.

### claude.ai chat
Works on every plan via a **custom connector** with sign-in. No key to copy.

**Setup.** Personal plans: **Settings** > **Connectors** > **Add custom connector**.
Team/Enterprise: an Owner adds it once under **Organization settings** >
**Connectors**, and each member then signs in with their own PlaceCall account.

1. Name it `PlaceCall`, URL `https://api.voygr.tech/mcp`. Keep the sign-in
   setting Claude detects.
2. **Add**, then sign in with Google or email. On first sign-in you accept the
   Terms of Service and Privacy Policy, and a PlaceCall account is created with
   free credits.
3. Allow access. PlaceCall appears in a chat's tools menu, where it can find
   places worth calling, place a call (it always confirms first), and fetch the
   result.

Prefer one API key for a whole workspace? Add the connector with **No sign-in**
and a Request header `x-api-key` carrying your key. All calls then bill to that
key.

### ChatGPT
Add PlaceCall as a custom app in ChatGPT on the web. Custom apps depend on your
ChatGPT plan.

1. Open **Plugins**, then **+** > **Create plugin** > **Create MCP App**.
2. Name it `PlaceCall`, server URL `https://api.voygr.tech/mcp`,
   authentication **OAuth**. Leave the OAuth settings ChatGPT discovers as they
   are, accept the custom-app notice, and **Create**.
3. Sign in with Google or email. On first sign-in you accept the Terms of
   Service and Privacy Policy, and a PlaceCall account is created with free
   credits.
4. In a chat, pick PlaceCall from the tools menu.

### Any MCP client (Cursor, Windsurf, MCP Inspector, ...)
Point the client at `https://api.voygr.tech/mcp` (streamable HTTP transport).
It is listed in the official MCP Registry as `io.github.voygr-tech/placecall`.
Sign in with OAuth where your client supports it, or send your key on every
request - either header works:

```
X-API-Key: <your key>
```
or `Authorization: Bearer <your key>`.

Claude Code keeps its own MCP config (it does not pick up claude.ai
connectors), so add it there with one command:

```sh
claude mcp add --transport http --scope user placecall https://api.voygr.tech/mcp \
  --header "X-API-Key: <your key>"
```

`--scope user` makes it available in every project. The plugin at the top of
this page is still the richer path for Claude Code - it carries the full skill,
not just the three tools.

### Codex
**Type this inside Codex, not in your shell.** `$skill-installer` is a system
skill bundled with Codex, so there is nothing to set up first:

```
$skill-installer install the skill at https://github.com/voygr-tech/placecall/tree/main/skills/placecall and name it placecall
```

It is a skill rather than a command, so plain English works and is what it
expects. It runs the install for you and reports where the skill landed. **No
restart needed**, it is available on your next turn, and it answers to
`$placecall`.

If the phrasing above is not understood, this is the script it runs, and you can
run it yourself from a normal shell:

```sh
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/voygr-tech/placecall/tree/main/skills/placecall \
  --name placecall
```

Two things worth knowing. The installer refuses to overwrite, so if you already
have a `placecall` (or older `callwright`) skill in `~/.codex/skills`, delete it
first or the install aborts. And **don't** run `install.sh` on Codex, that is the
Claude Code path.

The skill folder moved from `skills/call` to `skills/placecall` in October 2026,
so an install line that still says `.../tree/main/skills/call` no longer finds
it. A copy you already installed keeps working and still answers to
`$placecall`. To pick up newer versions, delete it and reinstall from the
`skills/placecall` URL above.

On older Codex without `$skill-installer`, or as an alternative on any Codex,
paste this repo's [`AGENTS.md`](./AGENTS.md) into your project's `AGENTS.md`.

### Hermes Agent
One command, and it prompts for the key rather than taking it on the command
line, so nothing lands in your shell history:

```sh
hermes mcp add placecall --url https://api.voygr.tech/mcp/ --auth header
```

Answer `Y` to "Does this server require authentication?", paste the key at the
masked prompt, and `Y` to enable all four tools. Hermes stores the key in
`~/.hermes/.env` (as `MCP_PLACECALL_API_KEY`) and writes only a `${...}`
reference into `config.yaml`, so the value is never in the config file. Verify
with `hermes mcp test placecall`, then **start a new session** - tools load at
session start.

Do not use the skill route on Hermes. `hermes skills install placecall` is
refused by Hermes's own scanner: a skill that sends an API key with `curl` to
any non-loopback host is a critical finding by that scanner's design, which is
what our skill does on every call. MCP has no shell and no env var in the
request, so the rule does not apply. The trailing slash on the URL matters.

### Gemini CLI
This repo is also a Gemini CLI extension: the skill plus the PlaceCall MCP
server. Install it from your shell:

```sh
gemini extensions install https://github.com/voygr-tech/placecall
```

The install asks for your PlaceCall API key and keeps it in the system keychain
(change it later with `gemini extensions config placecall`). Gemini hands that
stored key to the MCP server only. The skill's `curl` commands run in your
shell and read `PLACECALL_API_KEY` from there, so export it as well (see
[Get a key](#get-a-key-self-serve-and-set-it)). If the key is exported but not
stored, the MCP server picks it up from your environment too.

### Cursor
This repo is also a Cursor plugin (`.cursor-plugin/plugin.json`): the skill
plus the PlaceCall MCP server at `https://api.voygr.tech/mcp`, which signs you
in with OAuth, so the plugin holds no key. To load it before it is in the
Cursor Marketplace, clone it into Cursor's local plugins folder and run
**Developer: Reload Window**:

```sh
git clone https://github.com/voygr-tech/placecall ~/.cursor/plugins/local/placecall
```

The skill's `curl` commands read `PLACECALL_API_KEY` from the environment
Cursor's agent runs in. To send a key to the MCP server instead of signing in,
see [Any MCP client](#any-mcp-client-cursor-windsurf-mcp-inspector-).

### Any agent / plain shell
No install needed - the API is just HTTP. `skills/placecall/SKILL.md` is the full
reference; a model with a shell tool can place calls straight from it.

No shell on your side? Assistants with their own computer (e.g. **Meta Muse**)
integrate from this repo directly: paste the repo URL into the chat and ask it
to use PlaceCall for phone calls. If it offers secure credential storage for
the API key, use that - never paste the key into the chat itself.

Known to work this way: Meta Muse, OpenClaw (DeepSeek backend). Hermes needs
the MCP route above rather than the skill. If you are an agent building this
integration, send `X-Client-Surface: <your-platform>` on every request so we
can see which surfaces need love.

### Apify Store (no code, a whole list)
Have a list of businesses rather than an agent? [PlaceCall on the Apify Store](https://apify.com/voygr/placecall)
calls every business on it, asks the questions you set, and returns one row per
call. No PlaceCall key: Apify runs it and bills it.

1. Open the Actor and press **Try for free** (you need an Apify account).
2. Bring the list: upload a CSV, link a Google Sheet, paste rows, or use another
   Actor's dataset, for example Google Maps results.
3. Type your questions, keep **Check my list, don't call** ticked and press
   **Start**. You see exactly what each business would be asked, for free.
4. Accept the PlaceCall terms, untick the check and start again.

$0.10 for each call that reaches a real conversation; unanswered calls, voicemail
and busy lines are free. The first 10 calls on each Apify account are free, then
a paid Apify plan is needed. Agents connected to the
[Apify MCP server](https://mcp.apify.com) can find and run it too.

## Get a key (self-serve) and set it
Installing the skill does **not** need a key; **placing calls does.** Keys are
**self-serve** - no need to contact anyone:

1. Open <https://api.voygr.tech/checkout?src=gh-repo> and click **"Get free API key"**
   (name + email).
2. The key arrives **by email** (it is never shown in the browser or API
   response). What a new key includes, and the current credit rates, are
   shown on the checkout page.
3. Lost the key? <https://api.voygr.tech/recover> emails you a new one.
4. Need more credits? Top up on the same <https://api.voygr.tech/checkout?src=gh-repo>
   page (Stripe-hosted payment).

Then set the key in your shell:

**Quick way** - just export it for the current session:
```sh
export PLACECALL_API_KEY="<your key>"
```

**Nicer way** - save it once (no echo to screen, `600` perms) and load it per session:
```sh
mkdir -p ~/.codex
read -rsp "PLACECALL_API_KEY: " KEY; echo
printf 'export PLACECALL_API_KEY=%q\n' "$KEY" > ~/.codex/placecall.env
chmod 600 ~/.codex/placecall.env
unset KEY
# then, in any new shell where you want to place calls:
source ~/.codex/placecall.env
```

**No shell at all?** A desktop app never sees your shell environment, so neither
of the above reaches it. Put the key in the `env` block of
`~/.claude/settings.json` instead, which survives restarts. See the
[Cowork](#cowork) section, which also covers the sandbox domain allowlist you
need there.

**Verify** (prints your quota, never the key):
```sh
curl -s -H "X-API-Key: $PLACECALL_API_KEY" https://api.voygr.tech/users/me
```
Never commit `~/.codex/placecall.env` or paste the key into chat - keep it in the
env var / the `600` file above.

## Installed this before August 2026?
This project was called **Callwright** until 2026-08, and the repo lived at
`voygr-tech/callwright-skill`. Two things to know:

- **Your existing setup keeps working.** `install.sh` copies the skill rather than
  linking it, so an older copy is frozen at whatever it was when you installed -
  the rename cannot break it. It also means it will never pick up new skills or
  fixes, which is the reason to migrate.
- **To migrate, delete the old copy first.** It is still a working phone skill, so
  leaving it in place gives your agent two of them and the routing between them is
  ambiguous. `install.sh` now warns you if it finds one.
  ```sh
  rm -rf ~/.claude/skills/callwright ~/.claude/skills/callwright-skill
  ```
  Then install the plugin above, and re-export your key under its new name:
  `PLACECALL_API_KEY`. The key itself is unchanged - only the variable is renamed,
  so no need to reissue anything.

If you previously installed a phone-call skill from someone else (e.g.
`ai-call-agent`), remove or disable that too, for the same reason.

## The one rule
**Everything goes in the `brief`** - the bot reads only your brief. Put every detail
in it (what to ask, who you're calling for, names/dates/party size/callback number,
how to wrap up). One endpoint, describe the task, done.

## Good to know
- **Two things draw on one credit balance: answered calls and answered place
  suggestions.** Calls: only successful ones are billed — voicemails, hangups
  and no-answers cost nothing. Suggestions: 5 credits per answered
  `POST /v1/places/suggest`, nothing when it returns no cards or is refused.
  Both take a refundable hold at request time that is larger than the charge,
  so either can return `402` while your balance still looks sufficient for the
  charge alone (`GET /users/me` for your balance; rates and top-ups are
  self-serve at <https://api.voygr.tech/checkout?src=gh-repo>). The free tier
  is one shared pot: 250 free calls means 2,500 credits, and suggestions spend
  from the same 2,500.
- After a call `completed`, the outcome/transcript can populate a moment
  *after* the status flips - poll `GET /calls/{id}` until `outcome_type` is
  non-null.
- 13 language codes accepted (`en`, `es`, `fr`, `de`, `hi`, `ru`, `pt`, `ja`,
  `it`, `nl`, `sr`, `tr`, `pl`) plus `auto` (the default, resolves to `en`).
  `en` is the most reliable; non-English is best-effort.
- Only call numbers you're authorized to - real calls ring real phones.
  US destinations only; every call opens by identifying PlaceCall and stating
  that the line is recorded.

## Network access
The skill ships nothing that runs on its own. It is instructions your agent
follows with its own shell, using `curl`, and every request goes over HTTPS to
one host: `api.voygr.tech`. Nothing is sent anywhere else.

- **Calls:** `POST /calls` sends the number to dial, your brief and the
  language. `GET /calls`, `GET /calls/{id}`, `GET /calls/{id}/events` (polled
  while a call runs), `POST /calls/{id}/answer` (your reply to a question the
  call agent asks mid-call), `POST /calls/{id}/cancel`,
  `GET /calls/{id}/transcript-merged` and `GET /calls/{id}/recording` follow
  and read it.
- **Finding a place to call:** `POST /v1/places/suggest` sends your request in
  plain words, plus the name and callback number when you give them.
- **Account:** `GET /users/me`, `GET /v1/usage`, `GET /checkout/packs`,
  `GET /skills/{id}/manifest` and `PUT /users/me/limits`.

Every request carries your key in the `X-API-Key` header, so
`PLACECALL_API_KEY` goes to `api.voygr.tech` and nowhere else. `POST /calls`
also sends three headers that never affect auth or billing: an
`Idempotency-Key` so a retry cannot dial twice, `X-Client-Surface` naming the
listing these instructions came from, and `X-Client-Agent` naming the tool that
placed the call (`claude-code`, `cursor`, `codex` or `gemini-cli`, worked out
from which of `CLAUDECODE`, `CURSOR_AGENT`, `CODEX_SANDBOX` and `GEMINI_CLI` is
set; only the name is sent, never a variable's value).

The only local file the skill reads is `~/.codex/placecall.env`, your saved
key, and only when `PLACECALL_API_KEY` is unset. `install.sh` makes no network
calls. The Cursor plugin and the Gemini CLI extension also connect to the
PlaceCall MCP server at `https://api.voygr.tech/mcp`, the same host. The
checkout, recovery and docs links in this README are pages for you to open; the
skill does not fetch them.

On our side, a call rings a real phone and is recorded. Recordings and
transcripts are kept for 90 days. Security reports: [SECURITY.md](./SECURITY.md).

**Full reference:** [`skills/placecall/SKILL.md`](./skills/placecall/SKILL.md) (Claude Code) · [`AGENTS.md`](./AGENTS.md) (Codex).

**Live API docs:** <https://api.voygr.tech/docs> - log in with your PlaceCall key (the same one you set as `PLACECALL_API_KEY`).
