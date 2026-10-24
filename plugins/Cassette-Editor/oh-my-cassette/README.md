<p align="center">
  <img src="https://raw.githubusercontent.com/Cassette-Editor/oh-my-cassette/main/assets/banner.jpg" width="80%" alt="Oh My Cassette" />
</p>

<h1 align="center">Oh My Cassette</h1>

<p align="center">
  Edit video by talking to the <a href="https://trycassette.online">Cassette</a> agent from Claude Code, Codex, OpenCode or Hermes.<br />
  <sub>A small MCP bridge on PyPI. The editing tools come from the Cassette MCP service, so they stay current without a plugin update.</sub>
</p>

<p align="center">
  <a href="https://pypi.org/project/oh-my-cassette/"><img alt="PyPI" src="https://img.shields.io/pypi/v/oh-my-cassette?label=oh-my-cassette" /></a>
  <a href="https://github.com/Cassette-Editor/oh-my-cassette/blob/main/LICENSE"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-blue" /></a>
  <a href="https://discord.gg/qd9NY4k8d7"><img alt="Discord" src="https://img.shields.io/discord/1514649803626250452?logo=discord&logoColor=white&label=Discord&color=5865F2" /></a>
  <a href="https://github.com/Cassette-Editor/oh-my-cassette/blob/main/README.zh-cn.md">中文</a>
</p>

---

<p align="center">
  <img src="https://raw.githubusercontent.com/Cassette-Editor/oh-my-cassette/main/assets/demo-claude-code.gif" width="100%" alt="One Claude Code session: import five 4K films and a song, ask for a 30-second teaser, revise it, export it" />
</p>

**One Claude Code session, typed as you see it.** Five 4K travel films (10½ minutes of footage) and a song go in, a
four-sentence brief and a one-line revision go to the Cassette agent word for word, and a 30-second 1080p MP4 lands in
`cassette-exports/`. Waits are fast-forwarded: in real time the import took 4½ minutes, the first cut 9½, the revision
3½ and the export 1.

> *Cut a 30-second teaser for Turkey from these five films, on the beat of Pamgaea.mp3. Open on a hot-air balloon
> lighting up at dawn in Cappadocia, travel from the ancient ruins to the sea, name each place when it first appears,
> and end on the misty lake with the title TURKEY.*
>
> *The ruins part drags. Keep only the two best Ephesus shots, and put the camel right after the balloons.*

<p align="center">
  <a href="https://github.com/Cassette-Editor/oh-my-cassette/releases/download/v0.5.0/turkey-teaser.mp4"><img src="https://raw.githubusercontent.com/Cassette-Editor/oh-my-cassette/main/assets/turkey-teaser.jpg" width="100%" alt="Frames of the teaser it made: the balloon at dawn, the camel, two Ephesus shots, the Datça coast, the misty lake with the title TURKEY" /></a>
  <br /><sub><a href="https://github.com/Cassette-Editor/oh-my-cassette/releases/download/v0.5.0/turkey-teaser.mp4">Watch the teaser it made (MP4, 30 s, with sound)</a>. Footage and music credits are <a href="#credits">below</a>.</sub>
</p>

## Install in 30 seconds

You need [uv](https://docs.astral.sh/uv/) (it fetches Python and the package on first start) and
[ffmpeg](https://ffmpeg.org/download.html) to import video.

```bash
# Claude Code
claude plugin marketplace add Cassette-Editor/oh-my-cassette
claude plugin install oh-my-cassette@cassette-editor
```

```bash
# Codex
codex plugin marketplace add https://github.com/Cassette-Editor/oh-my-cassette.git
codex plugin add oh-my-cassette@cassette-editor
```

```bash
# Hermes
hermes mcp add cassette --command uvx --args oh-my-cassette==0.5.1
```

OpenCode and any other MCP host: see [Install](#install) below. Run `uvx oh-my-cassette==0.5.1 login` and complete the
email-code sign-in in your browser. Then restart your agent if it cannot refresh its tool list, and say:

> *Start a new Cassette project and import the clips in ./footage, then cut a 30-second travel video with a title at the start.*

## Upgrading from 0.4

0.5 is a rewrite. The 0.4 plugin carried its own editing runtime, music search and Hermes gateway; 0.5 is a thin bridge
to the Cassette MCP service, and the tools your agent sees are the service's.

- **Sign in again** with `uvx oh-my-cassette==0.5.1 login`. 0.4 passwords and tokens are not used.
- **Tools are new.** Projects, editing turns, questions, plans, undo, media, analysis and export come from the service,
  with their own descriptions; the 0.4 tool names (`cassette_run_job`, `cassette_ingest_media`, `cassette_match_bgm`, …)
  are gone. Reinstall the plugin, or point your host config at `uvx oh-my-cassette==0.5.1`.
- **Projects live in your Cassette account**, the same ones you open on the web or in Cassette for Mac, and the editor
  link each answer carries opens the project you are working on. 0.4 sessions do not carry over.
- **Hermes** is a plain MCP host now; remove the 0.4 gateway plugin.

## Projects and retention

A project the bridge starts is a cloud project that Cassette deletes, with its media, after three idle days; every use
pushes that back, and each answer says when it is due (`retention_expires_at`). Exported files are already on your
machine in `cassette-exports/` and stay there. A project made in Cassette for Mac is kept, and the bridge can open, edit
and export it while that Mac is online, but its media are imported in the app.

## Overview

Oh My Cassette connects your coding agent to the Cassette editing agent. It is a local stdio MCP server
that relays to the Cassette MCP service (`CASSETTE_MCP_URL`), which in turn calls the Cassette backend:

```text
Claude Code / Codex / OpenCode / Hermes  ──stdio──▶  oh-my-cassette  ──HTTP──▶  Cassette MCP service  ──▶  Cassette backend
```

- **The tools are the service's.** Whatever it lists (projects, editing turns, questions, undo,
  export) is what your agent sees, with the service's own descriptions and workflow instructions.
  When Cassette changes, the tools change with it; the plugin does not need a release.
- **The bridge adds only what needs your machine.** Local files named in a call are prepared and
  uploaded first (only from the workspace, media types only): video is transcoded with ffmpeg into the
  renditions the service declares, and audio or images it does not take as they are get converted.
  Each file uploads while the next one is prepared, in parts, four transfers at a time; a file whose
  upload was interrupted picks up its earlier import when you import it again.
  Exported files are downloaded into `cassette-exports/`. The workspace identity travels with each
  call so the service can remember a project per directory.
- **Long work never times out the host.** Every call waits a bounded time; slow local preparation
  answers `preparing` and keeps going in the background, and the next identical call picks it up.
- **It survives deploys.** It reconnects on its own, sends a call that names its request again when
  the connection drops or the service turns it away, resumes interrupted downloads, reports `bridge.*`
  errors with a `retryable` flag (and `retry_after_seconds` when the service said when), and, while
  the service is unreachable or refuses the token, lists a single `cassette_bridge_status` tool that
  says why.

The rules between the plugin and the service are defined in
[`src/oh_my_cassette/contract.py`](https://github.com/Cassette-Editor/oh-my-cassette/blob/main/src/oh_my_cassette/contract.py); `oh-my-cassette check` verifies a
service against them.

## Requirements

- An invited Cassette account and a Cassette MCP service that implements contract v1. Check it with `uvx oh-my-cassette==0.5.1 check --url <endpoint>`. While the
  service is unreachable or refuses the token, only `cassette_bridge_status` is listed.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.5 or newer. `uvx oh-my-cassette==0.5.1` resolves Python 3.11 or newer by itself.
- [ffmpeg](https://ffmpeg.org/download.html) (with ffprobe) to import video: `brew install ffmpeg`,
  `sudo apt install ffmpeg` or `winget install ffmpeg`. Video is transcoded on your machine before it
  uploads. A build with `zscale` also tone-maps HDR footage properly.

Which formats a tool accepts, and how files are prepared before upload, is declared by the service
(video, audio and image types at most).

## Configuration

Sign in once with `oh-my-cassette login`, using the Cassette account of your projects: the browser asks for the emailed code and your consent. One sign-in reaches every project of the account, whether it was made on the web or in Cassette for Mac. A project whose media lie on a Mac opens in the app on that Mac; reading its pictures or sound and exporting it need that Mac online, and its media are imported there. Login, status and logout use your operating-system keyring; no token needs to be copied. Environment variables below are optional overrides.

| Variable | Default | Meaning |
| --- | --- | --- |
| `CASSETTE_MCP_URL` | the saved connection, otherwise `https://mcp.trycassette.online/mcp` | Explicit MCP endpoint override. |
| `CASSETTE_AUTH_TOKEN` | unset | Advanced bearer-token override. Normally use `login`; the same account, scope and resource checks apply. Never place it in shared configuration. |
| `CASSETTE_WORKSPACE` | the directory the host starts the server in | Where relative paths resolve, where local files may come from, and the directory the service may remember a project for. A host that starts the server in the whole disk or your home folder gives it no files to read until you set this, or `CASSETTE_ALLOWED_ROOTS`. |
| `CASSETTE_ALLOWED_ROOTS` | unset | Extra directories local files may come from (`:`-separated; `;` on Windows). |
| `CASSETTE_DOWNLOAD_DIR` | `<workspace>/cassette-exports` | Where exported files are saved. The default must stay inside the workspace: a `cassette-exports` symlink leading elsewhere is refused. |
| `CASSETTE_MAX_UPLOAD_MB` / `CASSETTE_MAX_DOWNLOAD_MB` | `4096` / `16384` | Size limits per file. |
| `CASSETTE_UPLOAD_ANY_TYPE` | off | Allow non-media uploads when a tool accepts them. |
| `CASSETTE_LOCAL_WAIT_SEC` | `240` | How long one call waits for local preparation and upload before it answers `preparing`. |
| `CASSETTE_FFMPEG` / `CASSETTE_FFPROBE` | from `PATH` | The ffmpeg and ffprobe programs used to prepare local media. |
| `CASSETTE_TEMP_DIR` | the system temp directory | Where each upload makes its own private directory (`oh-my-cassette-job-*`) for prepared files until they are uploaded. |
| `CASSETTE_CONNECT_TIMEOUT_SEC` | `10` | How long to wait for the service when connecting. |
| `CASSETTE_MCP_HOST` | unset | The host name sent to the service when the host does not identify itself. |
| `OH_MY_CASSETTE_LOG` | `WARNING` | Log level on stderr. |

## Install

### Claude Code

Plugin (recommended): the two commands at the top. The plugin uses the connection saved by `oh-my-cassette login` and starts `uvx oh-my-cassette==0.5.1` with a 10-minute tool timeout.

Project scope without the plugin: copy [`.mcp.json`](https://github.com/Cassette-Editor/oh-my-cassette/blob/main/.mcp.json) into your project, or run:

```bash
claude mcp add --transport stdio cassette -- uvx oh-my-cassette==0.5.1
```

The skill lives in [`skills/cassette-video-edit/SKILL.md`](https://github.com/Cassette-Editor/oh-my-cassette/blob/main/skills/cassette-video-edit/SKILL.md) and ships with the plugin.

### Codex

Plugin: the two commands at the top ([`.codex-plugin/plugin.json`](https://github.com/Cassette-Editor/oh-my-cassette/blob/main/.codex-plugin/plugin.json) declares the server inline with `tool_timeout_sec: 600` and passes the `CASSETTE_*` variables through from your shell). Or add the server directly:

```bash
codex mcp add cassette -- uvx oh-my-cassette==0.5.1
```

### OpenCode

Add to `opencode.json` (project or `~/.config/opencode/opencode.json`):

```json
{
  "mcp": {
    "cassette": {
      "type": "local",
      "command": ["uvx", "oh-my-cassette==0.5.1"],
      "timeout": 600000
    }
  }
}
```

Then copy the skill so OpenCode loads it:

```bash
mkdir -p ~/.config/opencode/skills/cassette-video-edit
curl -fsSL https://raw.githubusercontent.com/Cassette-Editor/oh-my-cassette/v0.5.1/skills/cassette-video-edit/SKILL.md \
  -o ~/.config/opencode/skills/cassette-video-edit/SKILL.md
```

OpenCode has no MCP elicitation, which is fine: the editing agent's questions come back as ordinary tool results, and the service's tools say how to answer them.

### Hermes

```bash
hermes mcp add cassette --command uvx --args oh-my-cassette==0.5.1

mkdir -p ~/.hermes/skills/cassette-video-edit
curl -fsSL https://raw.githubusercontent.com/Cassette-Editor/oh-my-cassette/v0.5.1/skills/cassette-video-edit/SKILL.md \
  -o ~/.hermes/skills/cassette-video-edit/SKILL.md
```

Set `mcp_servers.cassette.timeout: 600` in `~/.hermes/config.yaml` so a call's bounded waits fit. Hermes is a plain MCP host here: the 0.4 gateway/plugin layer is gone.

### Any other MCP host

Command `uvx`, args `["oh-my-cassette==0.5.1"]`, stdio transport, a tool timeout of 10 minutes, and the environment variables above. No uv? `pipx run oh-my-cassette==0.5.1` works too.

## How a turn looks

```text
you:    Import intro.mp4 and beach.mov, then make a 20-second cut with the title "Kota Kinabalu".
agent:  (calls the service's import tool with ["intro.mp4", "beach.mov"])
        bridge: transcodes both videos, uploads them, passes the service media references
        (calls the service's editing tool with your sentence, verbatim; progress streams while it runs)
        "Done. Added a 20 s cut from both clips with the title at the start (v0→v3). Open it: <editor link>"
you:    Export it.
agent:  (calls the service's export tool)
        bridge: downloads the MP4 to cassette-exports/kota-kinabalu.mp4
```

The editor link comes from the service: open it in a browser to watch the run live and take over by hand.

## Check a service

```bash
uvx oh-my-cassette==0.5.1 check --url http://127.0.0.1:8790/mcp --upload \
  --arguments '{"project_id": "<a test project>"}'
```

Prints one line per check (transport and token, contract declaration, instructions, tool schemas,
local-file and `prepare` declarations, and with `--upload` a real upload round trip; `--arguments`
are the file tool's other arguments for it) and exits 1 on any failure. `--json` gives
machine-readable output for the service's CI. The service must speak MCP 2026-07-28; one that only
answers the handshake-era `initialize` fails the transport check, and the bridge refuses it with
`bridge.protocol_unsupported`.

## Update

Bump the pin in your host config (`oh-my-cassette==<new version>`) or reinstall the plugin; `uvx` fetches the new wheel on next start. Releases: [CHANGELOG.md](https://github.com/Cassette-Editor/oh-my-cassette/blob/main/CHANGELOG.md).

## Development

```bash
git clone https://github.com/Cassette-Editor/oh-my-cassette && cd oh-my-cassette
uv sync --group dev
uv run pytest -q                                   # reference service on loopback, no network; needs ffmpeg
uv run oh-my-cassette                              # the bridge itself (stdio)
uv run oh-my-cassette check --url <endpoint>       # conformance check
```

`tests/reference_remote.py` is an executable reference service for the contract;
[RELEASING.md](https://github.com/Cassette-Editor/oh-my-cassette/blob/main/RELEASING.md) has the PyPI release flow.

## Credits

The demo footage is by [yasin ilcebay](https://vimeo.com/yasinilcebay), licensed
[CC BY 3.0](https://creativecommons.org/licenses/by/3.0/), from Wikimedia Commons:
[Aizanoi Temple of Zeus](https://commons.wikimedia.org/wiki/File:Aizonai_Temple_of_Zeus_(4K)_-_TURKEY.webm),
[Cappadocia](https://commons.wikimedia.org/wiki/File:Cappadocia_4K_-_TURKEY.webm),
[Datça](https://commons.wikimedia.org/wiki/File:Dat%C3%A7a_-_TURKEY_4K.webm),
[Ephesus](https://commons.wikimedia.org/wiki/File:Ephesus_Ancient_City_-_Celsus_Library_4K.webm) and
[Gölcük Lake](https://commons.wikimedia.org/wiki/File:G%C3%B6lc%C3%BCk_Natural_Park_4K_-_Turkey.webm). The teaser
trims and reorders it, and adds place names, a title and music.

The music is "Pamgaea" by Kevin MacLeod (incompetech.com)<br />
Licensed under Creative Commons: By Attribution 4.0<br />
https://creativecommons.org/licenses/by/4.0/<br />
The teaser uses an excerpt of it.

## License

The code is MIT. Oh My Cassette is the client; the Cassette service has its own terms.

The demo recording (`assets/demo-claude-code.gif`), the teaser frames (`assets/turkey-teaser.jpg`)
and the teaser video attached to the release contain the works credited above. They are not covered
by the MIT license and remain under their own licenses (CC BY 3.0 for the footage, CC BY 4.0 for
the music).

<sub>MCP registry: `mcp-name: io.github.Cassette-Editor/oh-my-cassette`</sub>
