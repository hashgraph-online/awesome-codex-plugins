# Source and third-party notices

This is an independent project maintained by KunHcz. It is not affiliated with or endorsed by OpenAI.

## codex-chatgpt-web

Portions of the source are derived from [miuuyy/codex-chatgpt-web](https://github.com/miuuyy/codex-chatgpt-web), licensed under MIT, copyright 2026 codex-chatgpt-web contributors. The source checkout's base commit was `e85e3693fdb4e3e033348c08df0298c20fcdb612`; it contained local modifications and new web-session code, so this release is not a verbatim copy of that upstream commit.

The original license is preserved in [LICENSES/upstream-MIT.txt](LICENSES/upstream-MIT.txt), and the root [LICENSE](LICENSE) retains upstream copyright attribution. [UPSTREAM.json](UPSTREAM.json) lists the extraction provenance. Reused areas include tool gateway/broker, Responses parsing/encoding, shared protocol types and helpers, and associated tests. The web-session implementation and public packaging contain additional changes.

The upstream browser orchestration, browser-worker, prompt assembly application, launcher, user state, old deployment documentation, logs, and Git history are not distributed here. Some protocol-level compaction structures remain as compatibility code; they do not make this bridge manage the web conversation.

## Installed dependencies

MCP SDK and Zod are runtime package dependencies; TypeScript and Bun type declarations are development dependencies. Their packages retain their own license notices. The lockfile records exact resolutions. This source-only release does not bundle node_modules or a compiled dependency distribution.

Codex/Desktop, installed MCP/plugin packages, Bun, and OpenAI tunnel-client are external software installed by the operator. They are not relicensed or distributed by this repository. OpenAI names describe compatibility, not sponsorship.
