# codex-discord-bridge

Control Codex CLI from Discord. A Rust bridge (serenity) that connects a
Discord bot to the Codex app-server over WebSocket, so you can run coding
tasks from your phone.

```
Discord thread  <->  bridge (serenity)  <->  JSON-RPC over WebSocket  <->  codex app-server
```

## How it works

- Message the bot: it starts a Codex thread and streams the agent's output
  back into one live Discord message per turn.
- One Discord thread per Codex conversation. Follow-ups inside the thread
  continue the same conversation instead of starting a new one.
- Approval requests (command execution, patches) arrive as buttons with a
  configurable TTL, so Codex can ask permission mid-task while you are away
  from the desk.
- Autothread mode: each conversation gets its own Discord thread under a
  category you choose, titled from the first message.
- A 20s JSON-RPC keepalive and a bounded supervisor (readiness timeout, backoff
  capped at 4s) reconnect the app-server without dropping your Discord session
  or the thread mappings.

Access is single-controller: only the Discord user id set in
`DISCORD_CONTROLLER_USER_ID` can talk to the bot.

## Requirements

- Rust stable
- A Discord application with a bot token (enable the Message Content intent)
- Codex CLI installed and authenticated (`codex login status`)

## Setup

1. Clone the repo, copy `.env.example` to `.env`, and fill it in:

   ```
   DISCORD_BOT_TOKEN=          # from the Discord developer portal
   DISCORD_APPLICATION_ID=     # your application id
   DISCORD_GUILD_ID=           # your server id
   DISCORD_CONTROLLER_USER_ID= # your Discord user id
   CODEX_COMMAND=codex
   CODEX_APP_SERVER_LISTEN_URL=ws://127.0.0.1:8837
   RUST_LOG=info
   ```

2. Copy `bridge.json.example` to `bridge.json`. The defaults are fine to
   start. Turn on `autoThread.enabled` and set `autoThread.categoryId` if you
   want each conversation in its own thread.

3. Build and run:

   ```
   cargo build --release
   ./target/release/codex-discord-bridge
   ```

4. Invite the bot to your server and send it a message.

## State and logs

- Thread mappings live in `data/state.json`. Stop the bridge before editing
  that file by hand.
- The bridge logs to stdout. `RUST_LOG=debug` in `.env` for verbose output.

## Install as a Codex plugin

This repo ships a plugin manifest (`.codex-plugin/plugin.json`), a setup
skill (`skills/codex-discord-bridge-setup`), and its own marketplace file, so
Codex can install it directly:

```
codex plugin marketplace add yaffalhakim1/codex-discord-bridge
codex plugin add codex-discord-bridge@codex-discord-bridge
```

## Development

- `cargo test` runs the full suite, including reconnect, routing, and stream
  regression tests. State-touching tests use temp dirs via
  `BridgeState::with_path`, and a guard test fails if any test writes the
  production state file.
- `cargo clippy --all-targets -- -D warnings` is kept clean.

## License

MIT
