<p align="center">
  <a href="https://callmemcp.com/go/readme"><img src="assets/logo-rounded.png" width="180" alt="/call-me app icon"></a>
</p>

<div align="center">

# callme — your AI can call you

</div>

<p align="center">
  <a href="https://callmemcp.com/go/readme"><img src="assets/app-store-badge.svg" height="60" alt="Download on the App Store"></a>
  <br>
  <a href="https://mcpservers.org/servers/radres/call-me"><img src="https://mcpservers.org/badge.svg" alt="Listed on mcpservers.org"></a>
</p>

Your AI agents ring your actual iPhone, read you a question, an update or
your day ahead, and get your spoken reply back as text — or just text you. Works from any AI that
speaks MCP; nothing to install.

Call Me is not a voice assistant: your agent does all the thinking. Call Me
carries its words to your phone and your answer back, once or, with `keep_open`,
back and forth on the same call, so you can keep it working while you drive,
train or walk. Calls speak and understand 90+ languages.

## 1. Get the app

**[callme on the App Store](https://callmemcp.com/go/readme)**.
No registration, no email. Open it, tap *Agree & Continue*, and it shows your
personal **callme number**: 10 digits, and all an agent needs to reach you.

## 2. Connect your AI (MCP)

Pairing is stored locally in `~/.aiphone/config.json`. An MCP server running on
this computer can read that file automatically; the hosted HTTP endpoint cannot
read files on your computer and therefore needs the number supplied separately.

One server, every MCP client — no API key, no OAuth:

```
https://callmemcp.com/mcp
```

**Claude Code**

```bash
claude mcp add --transport http call-me https://callmemcp.com/mcp
```

**opencode** — add to `opencode.json` (or `~/.config/opencode/opencode.json`):

```json
{
  "mcp": {
    "call-me": {
      "type": "remote",
      "url": "https://callmemcp.com/mcp",
      "enabled": true
    }
  }
}
```

**Codex CLI — use the local paired MCP server**

```bash
cd /absolute/path/to/call-me
codex mcp remove call-me  # only if the hosted entry is already configured
codex mcp add callme -- node "$PWD/codex/mcp.mjs"
codex mcp list
```

The local `callme` MCP server reads `~/.aiphone/config.json` for every call and
text, so no number needs to be typed into the Codex conversation. Use its
`identity` tool to verify the paired phone.

**Gemini CLI**

```bash
gemini extensions install https://github.com/radres/call-me
```

or, for the MCP server alone:

```bash
gemini mcp add --transport http call-me https://callmemcp.com/mcp
```

**Grok**

In the Grok app: [grok.com/connectors](https://grok.com/connectors) → New
Connector → Custom → `https://callmemcp.com/mcp`. In Grok Build:

```bash
grok plugin install radres/call-me#grok
```

**Cline** — add to Cline's MCP settings (MCP Servers → Configure; CLI:
`~/.cline/data/settings/cline_mcp_settings.json`). Full agent-readable steps are
in [llms-install.md](llms-install.md).

```json
{
  "mcpServers": {
    "call-me": {
      "type": "streamableHttp",
      "url": "https://callmemcp.com/mcp",
      "timeout": 120
    }
  }
}
```

**Cursor** — add to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project):

```json
{
  "mcpServers": {
    "call-me": { "url": "https://callmemcp.com/mcp" }
  }
}
```

Or install the plugin in [`plugin/`](plugin/), which adds a skill telling the
agent when to call and when to text. It is a standard
[Agent Plugin](https://agent-plugins.org) with a Cursor manifest, so any client
that loads Agent Plugins can use it too.

**ChatGPT** — Settings → Apps → Advanced → Developer mode → add a connector
with the URL above (no authentication).

**claude.ai** — Settings → Connectors → Add custom connector → the URL above.

Anything else that speaks MCP — add a streamable-HTTP server pointing at the
URL above, then provide the recipient number through that client's pairing or
configuration flow. A hosted MCP connection cannot see this computer's
`~/.aiphone/config.json`.

For the local Codex/Claude integrations, pairing once writes the shared local
config and the MCP tools use it automatically. For hosted clients, tell the AI
the number or use that client's explicit pairing flow; never guess it.

| Tool | What it does |
|---|---|
| `call` | Rings your iPhone, reads your text aloud (a question, an update, a summary of the day ahead), returns your spoken reply as text. Holds ~30s, then hands the AI a `call_id` to poll. `keep_open: true` keeps the line up after your answer for `say`; `language` ("tr", "de", "pt-BR"...) is the language the AI speaks |
| `say` | Next line in a `keep_open` call; returns your next answer. While the AI thinks you hear a soft keyboard sound, and anything you say meanwhile comes back as `said_while_waiting` |
| `hang_up` | Ends a `keep_open` call, with an optional goodbye |
| `poll_result` | Finishes a call that was still ringing |
| `text` | Push-notification message, no ring |
| `wait_for_reply` | Delivers your replies and voicemails back to the AI |
| `set_thread_title` | Names the conversation thread on your phone |

Repeat calls from the same AI land in one titled thread on your phone; each
agent/session gets its own number and thread. Blocking a thread in the app
silences that sender for good.

## 3. Or just curl it

No MCP client, no plugin, no token. Anything that can POST JSON can ring your
phone, and these two endpoints are the whole product.

**Ring and wait for the spoken answer** (blocks until you answer or it gives up):

```bash
curl -sS https://callmemcp.com/ring \
  -H 'content-type: application/json' \
  -d '{"to":"<YOUR_10_DIGITS>","text":"Deploy to prod?","from":"Claude on my laptop"}'
```

```json
{"status":"completed","transcript":"Yes, ship it",
 "session_token":"curl_1a2b...","from":"<CALLER_NUMBER>"}
```

`status` is one of `completed`, `missed`, `declined`, `timeout`, `failed`.
`transcript` is what you said, already turned into text.

**Keep the line open** for a back-and-forth: add `"keep_open":true` to `/ring`.
The answer comes back with `"open":true` and a `call_id`. Speak again on the same
call and wait for the next answer, until you hang up (or the phone does):

```bash
curl -sS https://callmemcp.com/aiphone/calls/<call_id>/say \
  -H 'content-type: application/json' \
  -d '{"session_token":"curl_...","text":"Reverted it. Anything else?"}'

curl -sS https://callmemcp.com/aiphone/calls/<call_id>/hangup \
  -H 'content-type: application/json' \
  -d '{"session_token":"curl_...","text":"Thanks, talk later."}'
```

A conversation hangs up after 2 minutes of silence, 15 minutes in total or 60 turns.

**Text only**, no ring:

```bash
curl -sS https://callmemcp.com/text \
  -H 'content-type: application/json' \
  -d '{"to":"<YOUR_10_DIGITS>","body":"Migration finished.","from":"Claude on my laptop"}'
```

Returns `{"ok":true,"message_id":42,"delivered":true}`. A `delivered:false` means
the text is in your history but no notification was shown (notifications are off
for /call-me on that phone); the response spells that out in `notice`.

| Field | |
|---|---|
| `to` | your 10-digit /call-me number. Required |
| `text` / `body` | what to say / send. Up to 2000 chars for either; a call reads that out in about two minutes |
| `from` | sender name shown on your phone. Defaults to "Someone's AI" |
| `timeout_s` | `/ring` only: seconds to wait, 30 to 300. Default 300 |
| `keep_open` | `/ring` only: keep the line up after the answer for `say`. Default false |
| `language` | `/ring` and `say`: the language you write `text` in, e.g. `"tr"`. Default English |

### Anything else

Both responses hand back a `session_token`, and that is a real session: the same
caller can use the rest of the API with it, all landing in one thread on your
phone.

```bash
# name the thread
curl -sS https://callmemcp.com/aiphone/sessions/label \
  -H 'content-type: application/json' \
  -d '{"session_token":"curl_...","label":"nightly deploy"}'

# long-poll for replies, voicemails and missed calls
curl -sS "https://callmemcp.com/aiphone/sessions/events?session_token=curl_...&cursor=0&wait=25"
```

The token is derived from `to` + `from` + your IP, so repeat curls from the same
machine reuse one thread instead of showing up as a new stranger every time.

Limits: 20 rings/hour and 60/day per IP, 10 calls/hour and 40/day to any one
number. A sender you have blocked in the app gets `missed` with an empty
transcript, indistinguishable from a phone nobody picked up. On purpose.

## 4. Optional: Claude Code plugin

On Claude Code, the plugin adds what MCP alone can't: replies you send from
the phone land in the **live session**, and if Claude ends a turn with a
question parked on you, a `Stop` hook + answer waiter wake it up to call or
text you instead of going to sleep.

```sh
claude plugin marketplace add radres/call-me
claude plugin install call-me@call-me
claude plugin enable call-me@call-me   # REQUIRED — install leaves it disabled
claude plugin list                     # expect: call-me@call-me   ✔ enabled
```

Then restart Claude Code and say *"set up /call-me for me"* — it does the rest.

## 5. Optional: DeepSeek Harness plugin

On DSH, [dsh-plugin-call-me](https://github.com/radres/dsh-plugin-call-me) adds
what MCP alone can't there either: a turn ending or a tool waiting for approval
can ring your phone on its own, and because DSH lets a plugin wake an idle run,
the answer you speak picks the run back up.

```sh
dsh plugin --profile web add github:radres/dsh-plugin-call-me
```

## 6. Optional: herdr plugin

[herdr](https://herdr.dev) is a terminal workspace manager that watches every
pane and marks an agent `blocked` the moment it puts a real approval or question
on screen. [herdr-plugin-call-me](https://github.com/radres/herdr-plugin-call-me)
turns that moment into a call — and then puts your spoken answer back into the
pane as the keypress the agent was waiting for. It works for whichever of herdr's
~20 supported agents happens to be in that pane, so it needs nothing from the
agent itself.

```sh
herdr plugin install radres/herdr-plugin-call-me
herdr plugin pane open --plugin radres.call-me --entrypoint pair
```

## 7. Optional: Omarchy plugin

The Omarchy setup panel lives in its own repository so the marketplace installs
only the panel: [radres/omarchy-plugin-call-me](https://github.com/radres/omarchy-plugin-call-me).

```bash
omarchy plugin add https://github.com/radres/omarchy-plugin-call-me.git --enable
bash ~/.config/omarchy/plugins/radres.call-me/install-launcher.sh
```

Remove with `omarchy plugin remove radres.call-me`. Details, requirements and
what the panel sends over the network are in that repository's README.

## How it works

- `call` creates a VoIP call (LiveKit WebRTC — no real telephony); your
  iPhone rings through CallKit like a real call, TTS reads your text,
  your spoken reply is transcribed and returned to the agent.
- Your number is a bearer capability: anyone who knows it can reach you,
  nobody who doesn't can. Rate limits and per-number caps apply server-side;
  block any thread in the app to mute it permanently.
