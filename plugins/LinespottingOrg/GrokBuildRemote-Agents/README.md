# Build Remote Agent — desktop (`gbr-agent`)

**Product brand:** Build Remote Agent  
**Binary:** `gbr-agent` **v0.6.2**  
**License:** **MIT** (open source)  
**Org:** LinespottingOrg / Linespotting AB  

### Docs (humans + AIs)

| Read this | When |
|-----------|------|
| **[INSTALL.md](INSTALL.md)** | AIs first: install, pair, `mcp add`, Bot API `:8788` |
| **[AGENTS.md](AGENTS.md)** | You are an AI installing or debugging |
| **[mcp/gbr-mcp/INSTALL.md](mcp/gbr-mcp/INSTALL.md)** | Claude / Grok CLI / Cursor / Hermes / OpenClaw |
| **[FAQ.md](FAQ.md)** | Same FAQ as the website (humans + AIs + schema) |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Something failed (401, empty sessions, stale names) |
| **[SESSION-NAMES.md](SESSION-NAMES.md)** | Six identical titles / rename / 255 sessions |
| **[NETWORK.md](NETWORK.md)** | Firewall / netcheck |
| **[docs/BOT-API.md](docs/BOT-API.md)** | Grok bot / HTTP API (localhost + relay) |
| **[llms.txt](llms.txt)** | Short machine summary |
| **[COMPATIBILITY.md](COMPATIBILITY.md)** | What the phone sees; plugins |
| **[plugins/README.md](plugins/README.md)** | Our plugin registry (not someone else’s) |
| **[docs/PINNED-INSTALL.md](docs/PINNED-INSTALL.md)** | GitHub Release + SHA-256 |
| **[docs/WHAT-THE-PHONE-SEES.md](docs/WHAT-THE-PHONE-SEES.md)** | Terminals vs headless |
| **[SECURITY.md](SECURITY.md)** | Mailbox = machine roster |
| https://grokbuildremote.com/support | End-user playbook |  

Desktop agents for **Windows**, **macOS**, and **Linux**. They discover local terminal / **Grok Build** sessions, inject input, capture output, and exchange **protocol `gbr/1`** envelopes over HTTPS — your phone and PC never open ports to each other.

This agent pairs with the paid **Build Remote Agent** mobile apps ($13 one-time). The mobile clients are **not** open source; this desktop agent **is**.

| App | Link |
|-----|------|
| **Website** | https://grokbuildremote.com/ |
| **iOS / iPad / Mac / Vision** | https://apps.apple.com/app/id6791293726 |
| **Android (Google Play)** | https://play.google.com/store/apps/details?id=com.grokbuildremote.app |

### Why it exists

Grok Build (SpaceX / xAI agentic coding CLI) gained a new interface and API surface around **16 July 2026**. That made remote control of *local* Grok Build sessions practical. This open-source agent + paid mobile remote implements that workflow. Independent product — not affiliated with SpaceX or xAI except as a client of public APIs / open tooling.

---


## Independence & trademarks

**Build Remote Agent is an independent, third-party product from Linespotting AB.**
It is **not** affiliated with, endorsed by, or sponsored by **xAI** or **SpaceX**, and it is
**not** covered by the **Grok** trademark or brand. "Grok" and "Grok Build" are used solely to
describe compatibility with the user's own locally installed Grok Build CLI.

- **Desktop agent (this repo): 100% open source** under the MIT license.
- **Mobile apps ("Build Remote Agent" on iOS / Android): separate commercial products**, closed source (private repository), sold by Linespotting AB.

## Open source

| What | Policy |
|------|--------|
| Source (`cmd/`, `internal/`, this repo) | **Public · MIT** |
| Official binaries | Free for end users |
| Mobile apps | Separate private repo; paid $13 |

**Repo:** https://github.com/LinespottingOrg/GrokBuildRemote-Agents  
**Website:** https://grokbuildremote.com/

---

## Free download

- **Website:** https://grokbuildremote.com/#download  
- **GitHub Releases:** tagged `v*` assets  
- **Clone & build:** see below  

| File | Platform |
|------|----------|
| `gbr-agent-windows-amd64.exe` | Windows x64 |
| `gbr-agent-darwin-amd64` | macOS Intel |
| `gbr-agent-darwin-arm64` | macOS Apple Silicon |
| `gbr-agent-linux-amd64` | Linux x64 |
| `gbr-agent-linux-arm64` | Linux ARM64 |

---

## Quick install

**Preferred:** checksum **the installer**, then the binary — [docs/PINNED-INSTALL.md](docs/PINNED-INSTALL.md).

`curl https://grokbuildremote.com/install.sh | bash` is a **mutable remote install**. Do not paste it into other projects’ official docs.

### macOS / Linux (pinned)

```bash
VER=v0.6.2
BASE=https://github.com/LinespottingOrg/GrokBuildRemote-Agents/releases/download/$VER
SHA=0a7963dc668750bfcb907bb72f6f6f8db30881b02636e417e08e102352309301
curl -fsSL -o /tmp/gbr-install.sh "$BASE/install.sh"
echo "$SHA  /tmp/gbr-install.sh" | shasum -a 256 -c -
bash /tmp/gbr-install.sh
```

### Windows PowerShell (pinned)

```powershell
$ver = "v0.6.2"
$sha = "b604a21b5dae5a874487a597778d15742b3c2afb2470c93a8e8ba0a76e486cdf"
$base = "https://github.com/LinespottingOrg/GrokBuildRemote-Agents/releases/download/$ver"
$i = Join-Path $env:TEMP "gbr-install.ps1"
Invoke-WebRequest "$base/install.ps1" -OutFile $i -UseBasicParsing
if ((Get-FileHash $i -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha) { throw "installer SHA-256 mismatch" }
& $i
```

### From source

```bash
git clone --branch v0.6.2 --depth 1 https://github.com/LinespottingOrg/GrokBuildRemote-Agents.git
cd GrokBuildRemote-Agents
# build per Makefile / go build in cmd/
```

Default install locations:

| OS | Directory |
|----|-----------|
| macOS / Linux | `~/.local/bin/gbr-agent` |
| Windows (user) | `%LOCALAPPDATA%\GrokBuildRemote\gbr-agent.exe` |

### Typical flow

```bash
gbr-agent pair
# opens browser QR — scan with the phone camera
# legacy: gbr-agent pair -code YOURCODE

# Firewall / VPN / ports (no inbound ports — outbound HTTPS 443 only)
gbr-agent netcheck
gbr-agent netcheck -doc
# See NETWORK.md
gbr-agent run

# Optional: start at login in background (after pair)
gbr-agent service install
gbr-agent service status

# Fleet remote (this machine is driven by another hub, no phone):
gbr-agent pair-as-mailbox -name mac
gbr-agent service install
# On the hub, later: gbr-agent fleet add -name mac -os darwin
```

### Self-hosted relay

Optional — most users keep the production Worker. See **[SELF-HOSTED-RELAY.md](SELF-HOSTED-RELAY.md)**.

```bash
export GBR_RELAY_URL=https://your-worker.workers.dev
gbr-agent pair && gbr-agent run
# same URL in phone Settings → Relay
```

### What’s new in 0.5.1

- Dynamic session roster: pushed `list` with `replace: true` + `reason: "snapshot"`, and `heartbeat.payload.sessions[]` (`session_id` + `title`)
- No six-session cap — soft max **255** (extras dropped with a log, never crash); Grok Build is sorted first
- `gbr-agent rename -session ID -name "Phone title"` updates the live title without restart
- Later `register` envelopes update the title for an existing id
- Relay 0.5.1 latest-wins (one register per session, one list, one heartbeat)

### What’s new in 0.5.0

- Richer heartbeat (`agent_version`, `relay`, `os`) for phone session health  
- `service install` messaging + embed `GBR_RELAY_URL` into LaunchAgent / systemd when set  
- Service working directory = user home (avoids synthetic `dist` sessions)  
- Feedback peeks (0.4.5+) unchanged; inject/pair protocol still `gbr/1`  

Optional: `sessions`, `status`, `version`, `rename -name MyPC`.

### Session names

The phone shows a **title**, not the raw `conhost` / folder slug. See **[SESSION-NAMES.md](SESSION-NAMES.md)**.

```text
/rename Phone Grok                  # in Grok Build (slash command)
gbr-agent sessions                  # list grok-build-… ids
gbr-agent rename -session grok-build-40a22 -name "Phone Grok"
```

Soft max 255 advertised sessions; Grok is first. The app must apply `list.replace` / `heartbeat.sessions` (issue #3).

### API key

Agent may read relay / model API credentials from env (`GBR_API_KEY`, `XAI_API_KEY`, etc.) or local config under `~/.gbr/` — see support docs on the website.

---

## Contributing

Issues and PRs welcome on GitHub. Please keep protocol `gbr/1` compatibility stable unless versioned intentionally.

## Licensing note

This desktop agent is MIT-licensed and free. The companion **mobile apps**
("Build Remote Agent") are separate commercial products and are not covered
by this repository's MIT license.
