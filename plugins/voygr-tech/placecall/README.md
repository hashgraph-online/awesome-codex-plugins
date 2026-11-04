# PlaceCall

PlaceCall lets your agent call US businesses to handle reservations, gather
information and get quotes. You get back the outcome and a transcript. First
250 calls free. Built by ex-Google Maps and Search developers.

```sh
curl -s -X POST https://api.voygr.tech/calls \
  -H "X-API-Key: $PLACECALL_API_KEY" -H "Content-Type: application/json" \
  -H "X-Client-Surface: gh-repo" \
  -H "X-Client-Agent: ${CLAUDECODE:+claude-code}${CURSOR_AGENT:+cursor}${CODEX_SANDBOX:+codex}${GEMINI_CLI:+gemini-cli}" \
  -d '{"target_phone":"+1XXXXXXXXXX","brief":"Call this restaurant and ask what time the kitchen closes tonight.","language":"en"}'
```

The raw API takes your key in the `X-API-Key` header. Get one at
<https://api.voygr.tech/checkout>; it arrives by email. The plugins and MCP
connectors below sign you in through a browser instead. An agent with no
browser can [sign you up by email code](#sign-up-by-email-code).

## What PlaceCall does

Give PlaceCall a US number (or a list) and a task in plain English: an
inquiry, a quote request or a booking. It dials, navigates IVRs and hold, and
talks to the business.

No number? Describe the place instead, for example "a romantic restaurant in
Chicago, Saturday 8pm". PlaceCall finds candidates, explains its picks and
writes the call brief.

The bot reads only the `brief`. Put the full job in it: what to ask, who it's
for, names, dates, party size, callback number, the outcome you want and how
to wrap up.

## What it handles

- Book, cancel or reschedule tables and appointments
- Verify info, follow up on orders, check stock, get quotes
- Contact many businesses at once
- Recommend the best venue, service or vendor when you don't have a number
- Report what happened, and raise a question mid-call if needed

## What you get back

Every call returns a labelled outcome, the full transcript and the recording.
A failed call comes back with its reason: dropped, busy, voicemail or a wrong
number.

## Install
The Claude Code, Codex and Cursor plugins carry the skill and the PlaceCall
MCP server (`https://api.voygr.tech/mcp`). You sign in once in a browser; the
first sign-in creates a PlaceCall account with free credits, so there is no key
to copy. The claude.ai and ChatGPT connectors work the same way. The skill-only
routes (a copied skill, the Codex skill installer, OpenClaw) call the API with a
key; see [Get a key](#get-a-key-self-serve-and-set-it). A few options need a
key on every route: switching off recording, changing the opening notice,
canceling a call, and listing your calls.

### Claude Code (recommended)
The plugin updates itself from this repo. Two commands install it, with no
shell or git:
```
/plugin marketplace add voygr-tech/placecall
/plugin install placecall@placecall
```
Choose user scope ("Install for you") unless you want it confined to one
repository. Then run `/mcp`, pick the `placecall` server and sign in. The
skill answers to `/placecall:placecall`, and Claude uses it on its own when
you ask to call someone.

Installed the plugin before 6.1.0? Run `/plugin marketplace update placecall`
and restart Claude Code. A key you already exported keeps working with its
account and credits; without one, sign in with `/mcp`.

### Claude Code, without the plugin
```sh
git clone https://github.com/voygr-tech/placecall && cd placecall
./install.sh     # copies skills/placecall/SKILL.md -> ~/.claude/skills/placecall/
```
`install.sh` only copies `skills/placecall/SKILL.md` into your skills dir (no
network, no other side effects); copying by hand works too. Skills load at
startup, so start a new Claude Code session. A copy never updates itself; the
plugin does.

### Cowork
Use the Claude connector. Add it once as in [claude.ai chat](#claudeai-chat)
below, and it is there in Claude chat, Cowork and Claude Desktop. No key, no
terminal.

The plugin also installs in Cowork (**Customize** > **Plugins** > **Add
marketplace**, paste `voygr-tech/placecall`, **Install**). It adds the skill
and connects the same server. Install one or the other; with both, your agent
sees two PlaceCall servers offering the same tools.

Need one of the key-only options? Install the plugin instead of the connector
and give the skill a key. Cowork has no terminal for the `export` in
[Get a key](#get-a-key-self-serve-and-set-it), and its Bash sandbox blocks our
API until allowed, so put both in `~/.claude/settings.json` and restart
Cowork:

```json
{
  "env": { "PLACECALL_API_KEY": "<your key>" },
  "sandbox": { "network": { "allowedDomains": ["api.voygr.tech"] } }
}
```

`env` keeps the key across reboots; a desktop app never sees your shell.
`allowedDomains` pre-allows `api.voygr.tech`; Claude Code pre-allows none, so
without it the first call prompts for permission. If your organization sets
`strictAllowlist` or `allowManagedDomainsOnly`, the call is blocked with no
prompt (the "deep admin setting" people report).

The key sits in plaintext in that file, like the `600` env file in
[Get a key](#get-a-key-self-serve-and-set-it).
`chmod 600 ~/.claude/settings.json` if you want matching permissions.

### claude.ai chat
Works on every plan through a custom connector with sign-in.

Personal plans: **Settings** > **Connectors** > **Add custom connector**.
Team/Enterprise: an Owner adds it once under **Organization settings** >
**Connectors**, and each member signs in with their own PlaceCall account.

1. Name it `PlaceCall`, URL `https://api.voygr.tech/mcp`. Keep the sign-in
   setting Claude detects.
2. **Add**, then sign in with Google or email. The first sign-in accepts the
   Terms of Service and Privacy Policy and creates your account with free
   credits.
3. Allow access. PlaceCall appears in the chat's tools menu and always
   confirms before placing a call.

One API key for a whole workspace? Add the connector with **No sign-in** and a
Request header `x-api-key` carrying your key. All calls then bill to that key.

### ChatGPT
Add PlaceCall as a custom app in ChatGPT on the web. Custom apps depend on your
ChatGPT plan.

1. Open **Plugins**, then **+** > **Create plugin** > **Create MCP App**.
2. Name it `PlaceCall`, server URL `https://api.voygr.tech/mcp`,
   authentication **OAuth**. Leave the OAuth settings ChatGPT discovers as they
   are, accept the custom-app notice, and **Create**.
3. Sign in with Google or email. The first sign-in accepts the terms and
   creates your account with free credits.
4. In a chat, pick PlaceCall from the tools menu.

### Any MCP client (Cursor, Windsurf, MCP Inspector, ...)
Point the client at `https://api.voygr.tech/mcp` (streamable HTTP transport).
It is in the official MCP Registry as `io.github.voygr-tech/placecall`. Sign
in with OAuth where your client supports it, or send your key on every request
in either header:

```
X-API-Key: <your key>
```
or `Authorization: Bearer <your key>`.

Claude Code keeps its own MCP config (claude.ai connectors do not carry
over), so add it there:

```sh
claude mcp add --transport http --scope user placecall https://api.voygr.tech/mcp
```

Then run `/mcp`, pick `placecall` and sign in. To use a key instead, add
`--header "X-API-Key: <your key>"`. `--scope user` makes it available in every
project. The plugin above is still the richer path for Claude Code: it adds
the full skill to the four tools.

### Codex
The same plugin as Claude Code. Run these in your shell:

```sh
codex plugin marketplace add voygr-tech/placecall
codex plugin add placecall@placecall
codex mcp login placecall
```

The last command opens the browser sign-in. If your Codex has no `plugin`
command, update Codex or use the skill installer below.

To install only the skill and use a key, type this inside Codex (not your
shell); `$skill-installer` is bundled with Codex:

```
$skill-installer install the skill at https://github.com/voygr-tech/placecall/tree/main/skills/placecall and name it placecall
```

It expects plain English, installs the skill and reports where it landed. No
restart: `$placecall` works from your next turn.

If Codex does not understand the phrasing above, run the installer's script
from a normal shell:

```sh
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/voygr-tech/placecall/tree/main/skills/placecall \
  --name placecall
```

The installer refuses to overwrite: delete any existing `placecall` (or older
`callwright`) skill in `~/.codex/skills` first. Don't run `install.sh` on
Codex; that script is for Claude Code.

The skill folder moved from `skills/call` to `skills/placecall` in October 2026;
an install line that still says `.../tree/main/skills/call` finds nothing. An
installed copy keeps working as `$placecall`. For newer versions, delete it
and reinstall from the `skills/placecall` URL above.

On older Codex without `$skill-installer`, or on any Codex, paste this repo's
[`AGENTS.md`](./AGENTS.md) into your project's `AGENTS.md`.

### Hermes Agent
One command. It prompts for the key, so nothing lands in your shell history:

```sh
hermes mcp add placecall --url https://api.voygr.tech/mcp/ --auth header
```

Keep the trailing slash on the URL. Answer `Y` to "Does this server require
authentication?", paste the key at the masked prompt, and `Y` to enable all
four tools. Hermes stores the key in `~/.hermes/.env` (as
`MCP_PLACECALL_API_KEY`) and writes only a `${...}` reference into
`config.yaml`. Verify with `hermes mcp test placecall`, then start a new
session; tools load at session start.

Do not use the skill route on Hermes. Its scanner refuses
`hermes skills install placecall`, because the skill sends an API key with
`curl` to a non-loopback host; the MCP route has no shell and no env var in
the request.

### Gemini CLI
This repo is also a Gemini CLI extension: the skill plus the PlaceCall MCP
server. Install it from your shell:

```sh
gemini extensions install https://github.com/voygr-tech/placecall
```

The install asks for your PlaceCall API key and keeps it in the system keychain
(change it later with `gemini extensions config placecall`). Gemini hands that
key to the MCP server only. The skill's `curl` commands read
`PLACECALL_API_KEY` from your shell, so export it as well (see
[Get a key](#get-a-key-self-serve-and-set-it)). A key that is exported but not
stored reaches the MCP server too.

### Cursor
This repo is also a Cursor plugin (`.cursor-plugin/plugin.json`): the skill
plus the PlaceCall MCP server at `https://api.voygr.tech/mcp`. The server signs
you in with OAuth, so the plugin holds no key. Until it is in the Cursor
Marketplace, clone it into Cursor's local plugins folder and run
**Developer: Reload Window**:

```sh
git clone https://github.com/voygr-tech/placecall ~/.cursor/plugins/local/placecall
```

The skill's `curl` commands read `PLACECALL_API_KEY` from the environment
Cursor's agent runs in. To send a key to the MCP server instead of signing in,
see [Any MCP client](#any-mcp-client-cursor-windsurf-mcp-inspector-).

### Any agent / plain shell
Nothing to install: the API is plain HTTP. `skills/placecall/SKILL.md` is the
full reference, and a model with a shell tool can place calls straight from it.

No shell on your side? Assistants with their own computer (e.g. Meta Muse)
integrate from this repo: paste the repo URL into the chat and ask it to use
PlaceCall for phone calls. Put the API key in its secure credential storage,
never in the chat.

Known to work this way: Meta Muse, OpenClaw (DeepSeek backend). Hermes needs
the MCP route above. If you are an agent building this integration, send
`X-Client-Surface: <your-platform>` on every request so we can see which
surfaces need love.

### Apify Store (no code, a whole list)
Have a list of businesses rather than an agent? [PlaceCall on the Apify Store](https://apify.com/voygr/placecall)
calls every business on it, asks your questions and returns one row per call.
No PlaceCall key: Apify runs it and bills it.

1. Open the Actor and press **Try for free** (you need an Apify account).
2. Bring the list: upload a CSV, link a Google Sheet, paste rows, or use another
   Actor's dataset, for example Google Maps results.
3. Type your questions, keep **Check my list, don't call** ticked and press
   **Start**. You see what each business would be asked, for free.
4. Accept the PlaceCall terms, untick the check and start again.

$0.10 per call that reaches a real conversation; unanswered calls, voicemail
and busy lines are free. The first 10 calls on each Apify account are free,
then you need a paid Apify plan. Agents connected to the
[Apify MCP server](https://mcp.apify.com) can find and run it too.

## Get a key (self-serve) and set it
Signed in through a plugin or connector? You need a key only for the
key-only options under [Install](#install). The skill-only routes and the raw
API need one for every call. No browser? Your agent can
[sign you up by email code](#sign-up-by-email-code). Otherwise:

1. Open <https://api.voygr.tech/checkout?src=gh-repo> and click **"Get free API key"**
   (name + email).
2. The key arrives by email; the checkout page lists what it includes and the
   credit rates.
3. Lost the key? <https://api.voygr.tech/recover> emails you a new one.
4. Need more credits? Top up on the same <https://api.voygr.tech/checkout?src=gh-repo>
   page (Stripe-hosted payment).

Set it for the current session:
```sh
export PLACECALL_API_KEY="<your key>"
```

Or save it once (no echo to screen, `600` permissions) and load it in each
session:
```sh
mkdir -p ~/.codex
read -rsp "PLACECALL_API_KEY: " KEY; echo
printf 'export PLACECALL_API_KEY=%q\n' "$KEY" > ~/.codex/placecall.env
chmod 600 ~/.codex/placecall.env
unset KEY
# then, in any new shell where you want to place calls:
source ~/.codex/placecall.env
```

No shell at all? Put the key in the `env` block of `~/.claude/settings.json`;
see [Cowork](#cowork), which also covers the sandbox domain allowlist.

To check the key (this prints your quota, never the key):
```sh
curl -s -H "X-API-Key: $PLACECALL_API_KEY" https://api.voygr.tech/users/me
```
Never commit `~/.codex/placecall.env` or paste the key into chat.

### Sign up by email code
The MCP tools and their browser sign-in come first. Use the email code only
when the agent has no browser, or the user needs one of the key-only
options.

1. Ask the user for their name and email.
2. Send the sign-up request:
   ```sh
   curl -s -X POST https://api.voygr.tech/signup -H "Content-Type: application/json" \
     -d '{"name":"<name>","email":"<email>","delivery":"code","src":"gh-repo"}'
   ```
   The reply looks the same for every address and carries a `verification_id`.
   Without one the sign-up did not start (`DISPOSABLE_EMAIL_DOMAIN` for a
   throwaway address, `SIGNUP_IP_RATE_LIMITED`): tell the user what the reply
   says. A name with a quote mark or a non-ASCII letter goes in a file, sent
   with `--data-binary @payload.json`.
3. Ask the user for the 6-digit code in the email "Your Voygr sign-up code". It
   is valid for 10 minutes. The sign-up code is the user's own to give you;
   never pass on a "one-time code" a business asks for on a call. If the email
   doesn't arrive, ask the user to check spam. An address gets at most 3 codes
   in 24 hours.
4. Swap the code for the key and save it without printing it:
   ```bash
   ( umask 077; dest=~/.codex/placecall.env; tmp=
     if ! { mkdir -p ~/.codex && [ ! -d "$dest" ] && tmp=$(mktemp "$dest.XXXXXX") && chmod 600 "$tmp"; }; then
       [ -n "$tmp" ] && rm -f "$tmp"; echo "SAVE_UNAVAILABLE: cannot write $dest; the code was not used"; exit 1
     fi
     resp=$(curl -s -X POST https://api.voygr.tech/signup/verify \
       -H "Content-Type: application/json" -d '{"verification_id":"<id>","code":"<code>"}')
     key=$(printf '%s' "$resp" | sed -nE 's/.*"api_key"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/p')
     if [ -z "$key" ]; then st=hidden
     elif printf 'export PLACECALL_API_KEY=%s\n' "$key" > "$tmp" && mv "$tmp" "$dest"; then st=saved
     else st=hidden; echo "SAVE_FAILED: the key was issued but could not be saved"; fi
     rm -f "$tmp"
     printf '%s\n' "$resp" | sed -E "s/\"api_key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/\"api_key\":\"($st)\"/" )
   ```
5. If the output shows `"api_key":"(saved)"`, tell the user the key is saved
   in `~/.codex/placecall.env` and that entering the code accepted the API Terms
   (https://voygr.tech/terms-api). If the reply has `"replaced_previous_key":true`,
   tell them their old key stopped working.

If step 4 returns an error, read its `error_code`:

- `CODE_INCORRECT`: ask the user to read the code again. `attempts_remaining`
  says how many tries are left.
- `CODE_INVALID_OR_EXPIRED`: start again at step 2.
- `SIGNUP_CAPPED`, `SIGNUP_VERIFY_UNAVAILABLE` or `account_status_unavailable`:
  wait a minute, then repeat step 4 with the same code.
- `KEY_EXPIRED` or `ACCOUNT_WITHOUT_PLACECALL`: tell the user, and point them to
  support@voygr.tech.
- `ROTATION_FAILED`, or anything else: tell the user what the reply says.

If step 4 prints a `SAVE_` line instead, the key is not saved:

- `SAVE_UNAVAILABLE`: the code was not used. Fix the folder or disk, then repeat
  step 4 with the same code.
- `SAVE_FAILED`: the key was issued but could not be saved. Tell the user, and
  add that their old key stopped working if the reply has
  `"replaced_previous_key":true`. Fix the problem, then start again at step 2;
  the new code replaces the lost key.

## Installed this before August 2026?
This project was called Callwright until 2026-08, and the repo lived at
`voygr-tech/callwright-skill`.

- Your existing setup keeps working: `install.sh` copies the skill, so the
  rename cannot break an older copy. That copy never gets fixes, which is the
  reason to migrate.
- To migrate, delete the old copy first, or your agent has two phone skills
  and ambiguous routing. `install.sh` warns if it finds one.
  ```sh
  rm -rf ~/.claude/skills/callwright ~/.claude/skills/callwright-skill
  ```
  Then install the plugin above and re-export your key under its new name,
  `PLACECALL_API_KEY`. The key itself is unchanged.

If you installed a phone-call skill from someone else (e.g. `ai-call-agent`),
remove or disable that too, for the same reason.

## Good to know
- A call costs 10 credits when it obtains something (an answer, a refusal or
  a booking), otherwise nothing. It holds 30 credits while it runs and
  releases the rest when it ends. A cancel is free within 30 seconds of the
  callee answering and charged from 30 seconds on. An answered
  `POST /v1/places/suggest` costs 5 credits (15 held), nothing when refused or
  empty, from the same balance. Holds exceed charges, so `402` can come back
  while the balance still covers the charge alone. `GET /users/me` shows your
  balance; rates and top-ups are at <https://api.voygr.tech/checkout?src=gh-repo>.
  The free tier is one pot: 250 free calls is 2,500 credits, and suggestions
  spend from the same 2,500.
- After a call reaches `completed`, the outcome and transcript can land a
  moment after the status flips, so poll `GET /calls/{id}` until
  `outcome_type` is non-null. The transcript is complete once
  `transcript_status` reads `final`, usually a minute or two later.
- 13 language codes are accepted: `en`, `es`, `fr`, `de`, `hi`, `ru`, `pt`,
  `ja`, `it`, `nl`, `sr`, `tr`, `pl`. The default, `auto`, runs the call in
  English and does not switch mid-call; send `es` for a call in Spanish. `en`
  is the most reliable; non-English is best-effort.
- Only call numbers you're authorized to call; every call rings a real phone.
  US destinations only, except IN, LA, MN, MT, NE. By default every call opens
  with a notice that the line is recorded (in English and Spanish it also names
  PlaceCall). The optional `disclosure` and `record_call` fields change or
  switch off that opening; see the skill's "Opening notice" section.

## Network access
The skill is instructions your agent follows, through the MCP tools or
`curl`; nothing runs on its own. Every request goes over HTTPS to one host,
`api.voygr.tech`, and nothing is sent anywhere else.

- MCP server: the Claude Code, Codex and Cursor plugins and the Gemini CLI
  extension register `https://api.voygr.tech/mcp`. `suggest_places` sends your
  request and an optional location. `place_call` sends the number, brief,
  language and, if set, how the agent may reach you mid-call.
  `get_call_result` sends a call id. `answer_question` sends a call id, a
  question id and your answer.
- Calls: `POST /calls` sends the number, your brief and the language.
  `GET /calls`, `GET /calls/{id}`, `GET /calls/{id}/events`,
  `POST /calls/{id}/answer`, `POST /calls/{id}/cancel` and
  `GET /calls/{id}/recording` follow and read it.
- Finding a place: `POST /v1/places/suggest` sends your request, plus the name
  and callback number when you give them.
- Account: `GET /users/me`, `GET /v1/usage`, `GET /checkout/packs`,
  `GET /skills/{id}/manifest` and `PUT /users/me/limits`.
- Sign-up by email code: `POST /signup` sends your name and email;
  `POST /signup/verify` sends the code from the email.

The plugins sign in to the MCP server with OAuth, so your client sends an
access token, not a key; the Gemini CLI extension sends your key in
`X-API-Key`. Every `curl` request carries the key in `X-API-Key`, except the
two sign-up calls, which send none (`POST /signup/verify` returns one).
`PLACECALL_API_KEY` goes only to `api.voygr.tech`.

`POST /calls` also sends three headers that never affect auth or billing.
`Idempotency-Key` stops a retry dialing twice. `X-Client-Surface` names the
listing these instructions came from. `X-Client-Agent` names the tool that
placed the call (`claude-code`, `cursor`, `codex` or `gemini-cli`), worked out
from which of `CLAUDECODE`, `CURSOR_AGENT`, `CODEX_SANDBOX` and `GEMINI_CLI`
is set. Only the name is sent, never a variable's value.

The skill reads one local file, `~/.codex/placecall.env`, only when
`PLACECALL_API_KEY` is unset; the email-code sign-up writes it. `install.sh`
makes no network calls, and the skill never fetches the checkout, recovery or
docs links in this README.

On our side, a call rings a real phone and is recorded. Recordings and
transcripts are kept for 90 days. Security reports: [SECURITY.md](./SECURITY.md).

Full reference: [`skills/placecall/SKILL.md`](./skills/placecall/SKILL.md) (Claude Code) · [`AGENTS.md`](./AGENTS.md) (Codex).

Live API docs: <https://api.voygr.tech/docs>.

If PlaceCall is useful, star this repo. It helps a lot.
