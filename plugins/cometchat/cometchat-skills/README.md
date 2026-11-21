# @cometchat/skills (v5)

**Add CometChat chat & calling to your app through your AI coding agent.** Install the skills, then ask your agent *"add chat to my app"* — it has a short conversation with you (framework, intent, placement, credentials), then writes production-grade integration code into the files you already have.

v5 is a **multi-platform** pack: a thin `cometchat` dispatcher + an `onboarding` journey + on-demand, verified skills for six UI Kits — **React v7 · Angular v5 · React Native v5 · iOS v5 · Android v6 · Flutter v6** — plus headless **Calls SDK v5** skills (JavaScript · React Native · iOS · Android · Flutter) and the **Android Chat SDK v5**. It's **docs-maximal** (builds from the official CometChat task guides and verifies against them) and **two-gate tested** (a deterministic reviewer + a black-box acceptance explorer).

> **v5 ships on npm as `@cometchat/skills` (5.x).** It's a multi-platform rewrite of the v4 pack — same package name, new major. Upgrading? `add` removes the old v4 skills for you (see `CHANGELOG.md`).

## Install

Setup is two steps: install the skills, then make sure the CometChat MCP is connected.

### 1. Install the skills

```bash
npx @cometchat/skills add
```

The installer **detects your project automatically** — React (Vite, Next.js, CRA, Astro, React Router), Angular, React Native / Expo, and native iOS (Xcode project), Android (Gradle) and Flutter (`pubspec.yaml`) — and installs the skills for your coding agent: **Claude Code by default**; target another with `--ide` (Cursor, Codex, Cline, Kiro, Replit Agent, Windsurf, Copilot, Gemini, …) or `--ide all`. Use `--family` to force a platform (e.g. from a monorepo root) or to add the headless SDK skills **alongside** a UI Kit — a second `add` never removes the first family's skills:

```bash
npx @cometchat/skills add --family flutter      # force the Flutter v6 UI Kit skills
npx @cometchat/skills add --family js-calls     # add headless JS Calls SDK skills next to the React ones
```

Pin the agent as well (CI / Docker) with `--ide claude|cursor|codex|replit|…` (e.g. `--ide claude` → `.claude/skills/`). The full `--family` list is: `react · angular · react-native · ios · android · flutter` (UI Kits) and `android-sdk · react-native-calls · ios-calls · android-calls · flutter-calls · js-calls` (headless SDKs).

### 2. Connect the CometChat MCP

The skills look up CometChat's APIs in the docs, and the CometChat MCP (`cometchat`, `https://mcp.cometchat.com/mcp`; the docs need no sign-in) is how they read them. Without it they fall back to fetching docs pages from the web, which is slower and can miss pages, so treat this as part of setup.

`add` writes it into the agent's own MCP config for you, in the format that agent expects (skip with `--no-mcp`):

| Agent | Where `add` writes it |
| --- | --- |
| Claude Code | `.mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Codex | `.codex/config.toml` (loads in a trusted project) |
| Gemini CLI | `.gemini/settings.json` |
| VS Code + GitHub Copilot | `.vscode/mcp.json` |
| Kiro | `.kiro/settings/mcp.json` |
| Antigravity | `.agents/mcp_config.json` (the `agy` CLI reads only its user config: `add` prints the `agy mcp add` commands) |
| Continue | `.continue/mcpServers/cometchat.yaml` (MCP works in Agent mode) |
| Windsurf (Devin Desktop), Cline | Their user-level config, if the agent is installed (they have no project file); otherwise `add` prints the steps |
| Replit Agent | No config file: `add` prints the steps and one-click install links |
| Aider | No MCP support yet: the skills use web docs |

Restart the agent, then check it's connected: `npx @cometchat/skills doctor` shows which configs have it and whether its docs and account tools answer. In Claude Code, `claude mcp list` (or `/mcp`) should show `cometchat`; if it's missing, run `claude mcp add --transport http cometchat https://mcp.cometchat.com/mcp`. **Plugin installs** (below) connect it automatically. `npx @cometchat/skills remove --ide <agent>` undoes `add` (your own skills and MCP servers stay).

If it still isn't connected when you start a task, the agent tells you in its first reply, before it writes any code, with the step to connect it. It can carry on with web docs if you'd rather not.

Signing in to your CometChat account is separate and optional: see [Your CometChat account, through the MCP](#your-cometchat-account-through-the-mcp).

### Or install as a plugin

A plugin install bundles every family's skills with the CometChat MCP (`https://mcp.cometchat.com/mcp`), so the skills read current docs without extra setup, and can use your account once you sign in.

```bash
# Claude Code
/plugin marketplace add cometchat/cometchat-skills
/plugin install cometchat-skills@cometchat

# Gemini CLI
gemini extensions install https://github.com/cometchat/cometchat-skills

# Any agent that reads Agent Skills (via skills.sh)
npx skills add cometchat/cometchat-skills
```

The repo root also carries an [Agent Plugins 1.0](https://agent-plugins.org) manifest (`plugin.json` + `mcp.json`), the format Cursor, Codex and GitHub Copilot load.

## Use it

After install, open your project in your agent and say:

```
add chat to my app
```

The `cometchat` dispatcher routes to `cometchat-onboarding` (discover → understand → plan → approve), then hands a scoped build directive to that platform's `-core` skill, pulling in the others as the approved plan needs them (components, placement, theming, features, calls, push). Iterate afterward — *"add reactions" · "switch to dark mode" · "add a details side panel" · "switch to server-minted auth tokens"* (production auth — server-minted `loginWithAuthToken` — is covered inside each family's `-core` credentials/lifecycle guidance, and by the dedicated `-production` skill where one exists).

### Migrating from Sendbird, Stream (GetStream) or Twilio

```
migrate my app to CometChat
```

In a project that uses Sendbird, Stream Chat or Twilio Conversations, this one prompt runs the whole migration, with no plan/approve round-trip. `detect` spots the vendor (`migrate_from`), and `cometchat-migrate-from-sendbird` / `cometchat-migrate-from-getstream` / `cometchat-migrate-from-twilio` then:
- works on a `cometchat-migration` git branch;
- replaces every supported feature with its CometChat equivalent on your platform's UI Kit or SDK (Twilio has no UI Kit, so your own UI stays and its data layer moves to the CometChat SDK);
- **fully removes** the features CometChat doesn't have (code, UI entry points, dependencies);
- rewires your server's token endpoint and webhooks;
- writes a data-migration script for users, groups and message history and runs it for you once you provide the credentials (after the app migration is done);
- uninstalls the vendor and checks that the build passes.

It ends with `COMETCHAT_MIGRATION.md` and prints two lists: what was removed, and what you still need to do (credentials, dashboard toggles, running the import).

**Full step-by-step guide (prerequisites, install, run, data import, go-live):** [MIGRATING.md](MIGRATING.md).

## Your CometChat account, through the MCP

The installer and the plugins connect one **CometChat MCP server**, `cometchat` (`https://mcp.cometchat.com/mcp`):

- **Docs:** work straight away, with no sign-in.
- **Your CometChat account** (credentials, features, users, keys…): the first time your agent needs it, it asks you to sign in to CometChat in the browser. (Claude Code: run `/mcp`, pick `cometchat`, then **Authenticate**.)
- Some changes (creating API keys or login tokens, the OpenAI key, webhooks, app settings, team invites, deletes) also need your OK in the browser: the agent gives you a link, you approve that exact change and pass the code back.

Once you're signed in, the skills fetch your App ID / Region / Auth Key for you, with no copy-paste and no CLI. They can also, with your OK:
- turn features on;
- create test users, groups and API keys;
- set up webhooks;
- check usage.

Account tools never write framework code; the skills do all detection, env-writing and codegen. Changes to existing data or access always ask you first.

Signing in is optional. Without it, the docs tools still work and the skills ask you to paste your App ID, Region and Auth Key (Dashboard → your app → Credentials).

## What's in the pack

A thin `cometchat` router + a `cometchat-onboarding` journey + three competitor-migration skills (`cometchat-migrate-from-sendbird`, `cometchat-migrate-from-getstream`, `cometchat-migrate-from-twilio`, installed for every platform), then a **full skill set per platform**. Every UI-Kit family ships `core` (install · credentials · init→login→render · the golden-path chat surface) plus, as the platform needs them, `components · placement · customization · features · calls · push · migration` and platform extras (`patterns`, `production`, `testing`, `troubleshooting`, `events`, the Android `compose-*` / `kotlin-*` cohorts):

| Family | UI Kit package | Consumption |
|---|---|---|
| **React v7** | `@cometchat/chat-uikit-react@7` | drop-in UI Kit (+ Vite / Next.js / React Router / Astro glue) |
| **Angular v5** | `@cometchat/chat-uikit-angular@5` | drop-in UI Kit |
| **React Native v5** | `@cometchat/chat-uikit-react-native@5` | drop-in UI Kit (bare + Expo) |
| **iOS v5** | `CometChatUIKitSwift` (SPM) | drop-in UI Kit (host-composed screens) |
| **Android v6** | `chatuikit-{compose,kotlin}-android` | drop-in UI Kit (Compose + Kotlin/View) |
| **Flutter v6** | `cometchat_chat_uikit ^6` | drop-in UI Kit |
| **Calls SDK v5** (headless) | JS · React Native · iOS · Android · Flutter | standalone voice/video, no UI Kit |
| **Chat SDK v5** (headless) | Android | headless messaging, no UI Kit |

## Compatibility

- **React v7** — `@cometchat/chat-uikit-react@7` (verified on 7.2.4) + `@cometchat/chat-sdk-javascript@4`; calls `@cometchat/calls-sdk-javascript@5`. React ≥ 18.
- **Angular v5** — `@cometchat/chat-uikit-angular@5` (verified on 5.2.2) + Chat SDK v4 + Calls SDK v5. Angular 17–21.
- **React Native v5** — `@cometchat/chat-uikit-react-native@5` (verified on 5.5.1) + `@cometchat/chat-sdk-react-native@4` + `@cometchat/calls-sdk-react-native@5`.
- **iOS v5** — `CometChatUIKitSwift` 5.2.x (verified on 5.2.3) + `CometChatSDK` 4.1.x + `CometChatCallsSDK` 5.0.x (Swift Package Manager).
- **Android v6** — `chatuikit-{compose,kotlin}-android` 6.1.x (pinned 6.1.1) + `chat-sdk-android` 5.0.x + `calls-sdk-android` 5.0.x.
- **Flutter v6** — `cometchat_chat_uikit ^6` (verified on 6.2.0) + `cometchat_calls_sdk ^5` (calls).

Exact pinned versions per family live in `peers.yaml` and each family's `SKILL.md` frontmatter (both ship in the package).

## Links

- Docs: [cometchat.com/docs](https://www.cometchat.com/docs)
- UI Kits: [`@cometchat/chat-uikit-react`](https://www.npmjs.com/package/@cometchat/chat-uikit-react) · [`-angular`](https://www.npmjs.com/package/@cometchat/chat-uikit-angular) · [`-react-native`](https://www.npmjs.com/package/@cometchat/chat-uikit-react-native)

## License

MIT
