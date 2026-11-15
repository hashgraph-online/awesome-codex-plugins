<p align="center">
  <img alt="" src="assets/icon.svg" width="96" height="96">
</p>
<h1 align="center">Telegram Bot UI</h1>

<a href="https://github.com/hlibsuslov/telegram-bot-ui">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/hero-dark.png">
    <img alt="telegram-bot-ui — Telegram bots that feel like real products. A skill that teaches your coding agent to design, build, publish and operate Telegram bots." src="docs/assets/hero-light.png" width="100%">
  </picture>
</a>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <a href="https://github.com/hlibsuslov/telegram-bot-ui/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/hlibsuslov/telegram-bot-ui?color=3B82F6"></a>
  <a href="https://github.com/hlibsuslov/telegram-bot-ui/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/hlibsuslov/telegram-bot-ui?style=flat&color=22C55E"></a>
  <a href="https://github.com/anthropics/skills"><img alt="Format: Agent Skills" src="https://img.shields.io/badge/format-Agent%20Skills-8A2BE2.svg"></a>
  <a href="https://core.telegram.org/bots/api-changelog"><img alt="Telegram Bot API 10.4, verified 2026-11-15" src="https://img.shields.io/badge/Bot%20API-10.4%20verified%202026--11--15-26A5E4.svg"></a>
  <a href="https://github.com/hlibsuslov/telegram-bot-ui/actions/workflows/checks.yml"><img alt="checks" src="https://github.com/hlibsuslov/telegram-bot-ui/actions/workflows/checks.yml/badge.svg"></a>
  <img alt="Tools: Python standard library, no token" src="https://img.shields.io/badge/tools-stdlib%20%C2%B7%20offline%20%C2%B7%20no%20token-2ea44f.svg">
</p>

<p align="center">
  <b>An Agent Skill that makes your Telegram bot look, feel and run like a well-designed product.</b><br>
  Bot screens and keyboards · streaming AI answers · HTML widgets · channel publishing · agent-operated bots · premium emoji · the whole Bot API, offline.
</p>

<p align="center">
  <a href="https://telegram-bot-ui-site.vercel.app">Website</a> ·
  <a href="#-quick-start">Quick start</a> ·
  <a href="#-what-your-agent-can-do">Capabilities</a> ·
  <a href="#-html-widgets">Widgets</a> ·
  <a href="#-install">Install</a> ·
  <a href="#-recipes-and-examples">Recipes</a> ·
  <a href="#-tools-you-can-use-without-an-agent">Tools</a> ·
  <a href="#-faq">FAQ</a>
</p>

<p align="center">
  🌐 <b>English</b> · <a href="README.ru.md">Русский</a> · <a href="README.uk.md">Українська</a>
</p>

---

<p align="center">
  <a href="https://telegram-bot-ui-site.vercel.app"><img alt="Demo: one sentence to the coding agent turns a cluttered bot menu into a clean screen with colored buttons, then a streaming reply with Stop and an approval notification" src="docs/assets/demo.gif" width="720"></a>
</p>

## ⚡ Quick start

**Claude Code** (2.1.275 or later) — skill plus five subagents, in one line inside a session:

```
/plugin install telegram-bot-ui --marketplace hlibsuslov/telegram-bot-ui
```

**Any agent, with the GitHub CLI** (gh 2.96 or later) — it asks which agents to install for:

```bash
gh skill install hlibsuslov/telegram-bot-ui
```

**Without the GitHub CLI** — clone once and let the installer place the files (standard library Python;
on Windows use `py -3` instead of `python`):

```bash
git clone https://github.com/hlibsuslov/telegram-bot-ui.git && cd telegram-bot-ui
```

```bash
python scripts/install.py --host all --scope user
```

Then open your bot's repository and just ask: *"Improve the UX of this Telegram bot."*
The skill activates on its own — no API names needed. More hosts and options: [Install](#-install).

## ✨ What changes in your bot

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/before-after-dark.png">
  <img alt="Side by side: a cluttered settings menu with cut-off labels and a duplicated order, versus a clean settings screen with a danger-styled delete button and a single order card marked as paid." src="docs/assets/before-after-light.png" width="100%">
</picture>

| Situation | Without the skill | With the skill |
|---|---|---|
| AI answer takes 20 s | "typing…" then a wall of text | streamed draft with real stages, a **Stop** button, a clear "stopped — incomplete" ending |
| A form | "Send your phone" with no way back | buttons **and** a reply field in one step, Back keeps answers, **Submit** disabled until valid, no double orders |
| "My balance" in a group | posted for everyone to see | shown **only to the person who tapped**; never leaks on errors |
| Order status | four new messages per update | **one live card** (widget) that updates in place |
| Channel post timed out | posted again, now twice | outcome treated as unknown, checked before any retry |
| "Ignore your rules" in a message to an agent bot | the agent obeys | quoted as data; the operator is told |
| Old SDK | new features silently dropped | the gap is detected and bridged with an isolated adapter |

## 🧠 What your agent can do

| Capability | What the agent gets right |
|---|---|
| 🎛 **Build bot interfaces** | texts, menus, inline and reply keyboards, colored and disabled buttons, forms, navigation, streaming AI answers with Stop, private replies in groups, Rich Messages and tables, formatting, localization |
| 🛒 **Product flows** | shops, support, bookings, AI assistants, trackers: no stale "Pay" buttons, no double orders, no personal data leaking into groups (15 product recipes) |
| 📣 **Publish to channels** | compose, validate, preview, approve and schedule channel posts; never post twice after a timeout (`skills/telegram-bot-ui/scripts/tg_post.py`, 10 recipes) |
| 🤖 **Operate as an agent through a bot** | drive an agent from Telegram with an operator allowlist, approval buttons bound to one action, and inbound messages treated as data, not instructions (`agent_bridge` CLI, MCP server, Claude Code and Codex hooks, 10 recipes) |
| 🧩 **Build HTML widgets** | Bot API 10.4 widgets inside messages: size limit, production context, caption and text fallback, live cards, shared polls, wallet flows (18 ready widgets, build and preview tools, 7 recipes) |
| 💎 **Premium emoji** | one custom emoji pack across buttons, texts, rich messages and posts: real ids resolved from the pack, all-or-nothing fallback when the bot is not eligible (6 recipes) |
| 📚 **Look up the whole Bot API** | methods, types and fields from a local catalog; validate a payload before sending; refuse to invent a field (193 methods, 425 types, refreshable from the official docs) |

It also knows **when not to** use something: no widget for a three-button menu, no table for two
facts, no group widgets in production (they are test-server only today), no publishing without a
human's yes.

## 🧩 HTML widgets

Eighteen ready widgets with light and dark themes, three languages, server handlers and a
caption fallback — plus a kit to build your own, a size check that follows the server's algorithm,
and a local preview.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/widgets-dark.png">
  <img alt="Seven widgets from the gallery: a monitoring dashboard with charts, an order tracker, a slot booking calendar, a shopping cart with checkout, a quiz, a CSV export progress card and a price alert." src="docs/assets/widgets-light.png" width="100%">
</picture>

<sub>Rendered from <code>skills/telegram-bot-ui/examples/widgets/</code> with <code>skills/telegram-bot-ui/scripts/preview_widget.py --gallery</code>.
That is a mock of the widget runtime in a desktop browser, not a Telegram client — real apps may draw them differently.</sub>

```bash
python skills/telegram-bot-ui/scripts/build_widget.py skills/telegram-bot-ui/examples/widgets/src/order-tracker.html \
  --demo skills/telegram-bot-ui/examples/widgets/demo/order-tracker.json --strict   # build from the kit, check size and caption
python skills/telegram-bot-ui/scripts/preview_widget.py --gallery -o preview.html   # every widget and state, light and dark
```

## 💬 Ask your agent

No API names needed. In your bot's repository:

| Area | Try saying |
|---|---|
| Interfaces | *"Improve the UX of this Telegram bot."* · *"The main menu is a mess — restructure it and make the main action stand out."* · *"Add a Stop button to the AI answers."* · *"Fix `can't parse entities`."* |
| Product flows | *"People double-tap 'Place order' and get two orders."* · *"In our group, 'My orders' must show each person only their own orders."* · *"Design a booking bot: service, time, confirmation."* |
| Channels | *"Post this release note to our channel tomorrow at 9:00 — show me the preview first."* · *"Every Monday, publish a digest of last week's releases without duplicates."* |
| Agent through a bot | *"Let me drive my coding agent from Telegram, and only me."* · *"Make the agent ask for approval with buttons before anything risky."* |
| Widgets | *"Turn the order status into one card that updates."* · *"Our widget is too big to send — make it fit."* |
| Bot API lookup | *"Which update tells my bot that the user stopped the answer?"* · *"Can a bot delete a message for just one user?"* |

You can also call it by name: `/telegram-bot-ui` (Claude Code), `$telegram-bot-ui` (Codex), the
`/` menu (Cursor, Antigravity).

## 📦 Install

The skill is one folder whose entry point is [`SKILL.md`](skills/telegram-bot-ui/SKILL.md). Every path below is checked
against that host's documentation in [`docs/hosts.md`](docs/hosts.md).

<details open>
<summary><b>Claude Code — plugin (skill + five subagents)</b></summary>

In a Claude Code session (2.1.275 or later):

```
/plugin install telegram-bot-ui --marketplace hlibsuslov/telegram-bot-ui
```

Or from your shell, in two steps:

```bash
claude plugin marketplace add hlibsuslov/telegram-bot-ui
```

```bash
claude plugin install telegram-bot-ui@telegram-bot-ui
```

The skill is then `/telegram-bot-ui:telegram-bot-ui` and the subagents are
`telegram-bot-ui:telegram-bot-designer` and so on. Update with `claude plugin update telegram-bot-ui`.

</details>

<details>
<summary><b>Claude Code — plain skill folder</b></summary>

```bash
git clone https://github.com/hlibsuslov/telegram-bot-ui.git && cp -r telegram-bot-ui/skills/telegram-bot-ui ~/.claude/skills/
```

One project only: copy the folder into `<your-repo>/.claude/skills/telegram-bot-ui`. To add the subagents
too, use the installer below.

</details>

<details>
<summary><b>Any host — GitHub CLI (<code>gh skill</code>, gh 2.96 or later)</b></summary>

```bash
gh skill install hlibsuslov/telegram-bot-ui telegram-bot-ui --agent claude-code --scope user
```

`--agent` takes `claude-code`, `codex`, `cursor`, `gemini-cli`, `github-copilot`, `antigravity`,
`cline`, `opencode` and dozens more (`gh skill install --help`); without `--scope user` the skill goes into
the current repository. You get the latest tagged release; pin one with `--pin v2.1.0` and update with
`gh skill update`. Subagents are not included: use the Claude Code plugin or the installer below for them.

</details>

<details>
<summary><b>Any host — the installer (Codex, Cursor, Gemini CLI, Copilot, Devin…)</b></summary>

```bash
git clone https://github.com/hlibsuslov/telegram-bot-ui.git && cd telegram-bot-ui
```

```bash
python scripts/install.py --host all --scope user --dry-run
```

| Option | Meaning |
|---|---|
| `--host claude\|codex\|cursor\|gemini\|copilot\|all` | which agents to install for |
| `--scope user\|project` | your home folder, or one repository (`--project <path>` for another one) |
| `--with-instructions` | adds a short pointer block to `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md` or a Cursor rule (project scope only) |
| `--link` | symlinks to the clone instead of copying, so `git pull` is the whole update |
| `--uninstall` | removes only what the installer created |
| `--dry-run` | prints the plan and changes nothing |

Anything already there that the installer did not create is first moved to `<name>.bak-<time>`.
Update: `git pull` in the clone and run the same install command again.

</details>

| Host | Skill folder (user / project) | Extras |
|---|---|---|
| Claude Code | `~/.claude/skills/` / `.claude/skills/` | subagents in `.claude/agents/` |
| Codex CLI | `~/.agents/skills/` / `.agents/skills/` | custom agents in `.codex/agents/*.toml`; call the skill with `$telegram-bot-ui` |
| Cursor | `~/.agents/skills/` / `.agents/skills/` | optional rule `.cursor/rules/telegram-bot-ui.mdc` |
| Gemini CLI / Antigravity | `~/.gemini/skills/` / `.agents/skills/` | or `gemini skills install https://github.com/hlibsuslov/telegram-bot-ui`; optional `GEMINI.md` block |
| GitHub Copilot | `~/.agents/skills/` / `.agents/skills/` | optional `.github/copilot-instructions.md` block |
| Devin (formerly Windsurf) | reads `~/.agents/skills/` / `.agents/skills/` | install with `--host codex` |
| Cline and other `AGENTS.md` readers | — | paste [`adapters/agents-md/AGENTS.snippet.md`](adapters/agents-md/AGENTS.snippet.md) and keep the folder in the repo |
| Your own agent on a model API | — | system prompt: [`adapters/portable/telegram-bot-ui.prompt.md`](adapters/portable/telegram-bot-ui.prompt.md); with a file tool: [`llms.txt`](llms.txt) |

## 👥 Subagents

Five roles that route into the skill instead of copying it. Claude Code: [`agents/claude/`](agents/claude/)
(installed by the plugin or the installer). Codex: [`agents/codex/`](agents/codex/) as custom
agents (*"Have telegram_bot_reviewer review this diff"*).

| Role | Does | Edits code? |
|---|---|:---:|
| `telegram-bot-designer` | screen and state map, real UX defects, exact texts and keyboards | — |
| `telegram-bot-builder` | implements from recipes, validates payloads, adds tests | ✓ |
| `telegram-publisher` | composes, validates, previews and publishes channel posts — only after your explicit yes | ✓ |
| `telegram-widget-builder` | designs and builds HTML widgets, checks size and fallback | ✓ |
| `telegram-bot-reviewer` | reviews a diff against the skill's invariants with `file:line` findings | — |

On hosts without subagents, ask for the role in words: *"Act as a reviewer of this diff using the
telegram-bot-ui skill."*

## 🍳 Recipes and examples

65 numbered recipes plus mini-recipes. The eight new product journeys (R80–R87) are
Python offline models with callback demos; their production integrations are explicitly pending.

Agents search a catalog of 40 product families (`skills/telegram-bot-ui/recipes/use-cases.json`), reuse or compose
existing helpers, and write only the missing behavior in the user's project
([extension guide](skills/telegram-bot-ui/references/example-library.md), [contributing](CONTRIBUTING.md)).

```bash
python skills/telegram-bot-ui/scripts/example_library.py --query "event waitlist" --json
python skills/telegram-bot-ui/examples/python/recipes/r80_87_product_journeys.py --scenario R81
```

New journeys cover lead intake, events/waitlists, reminders, file jobs, moderation review,
feedback, loyalty points and service queues. The catalog marks each family as an existing
example, a composition or planned work.

| Recipe | You get |
|---|---|
| [AI assistant with Stop](skills/telegram-bot-ui/recipes/01-ai-assistant.md) | rich streaming, real stages, Stop, race-safe single final message |
| [Interactive document](skills/telegram-bot-ui/recipes/02-interactive-document.md) | compact table, collapsible quote, attached file, buttons in text |
| [Multi-step form](skills/telegram-bot-ui/recipes/03-multi-step-form.md) | buttons + reply field, disabled Submit, Back, no duplicates |
| [Shared card + personal panel](skills/telegram-bot-ui/recipes/04-shared-card-personal-panel.md) | per-user private views in a group |
| [Private widget](skills/telegram-bot-ui/recipes/05-private-widget.md) | an order card that updates in place |
| [Shared widget](skills/telegram-bot-ui/recipes/06-shared-widget.md) | one live poll in many chats |
| [Wallet](skills/telegram-bot-ui/recipes/07-wallet.md) | pay and sign from a widget, honest payment states |
| [Multi-topic bot](skills/telegram-bot-ui/recipes/08-multi-topic-bot.md) | parallel conversations, topic links |
| [Tracker bot upgrade](skills/telegram-bot-ui/recipes/09-tracker-bot.md) | a real bot moved to the new API |
| [Mini-recipes](skills/telegram-bot-ui/recipes/mini-recipes.md) | gifts, communities, share themes, managed bots, verification |

| Range | You get |
|---|---|
| [20–29, 60–64 · Products](skills/telegram-bot-ui/references/use-case-playbooks.md) | shop with Stars, support desk, booking, onboarding, settings, subscription, learning, assistant, expense split, community, inline mode, business account, alerts, search, delivery tracker |
| [30–39 · Channel publishing](skills/telegram-bot-ui/references/publishing-pipeline.md) | autoposter, long read, album, poll, pinned digest, editorial approval, cross-posting, mailing, comments, corrections |
| [40–49 · Agent through its bot](skills/telegram-bot-ui/references/agent-operated-bots.md) | deploy approval, live build status, nightly digest, ask and continue, streamed research with Stop, job topics, team group, incident alerts, coding-agent hooks |
| [50–56 · Widgets](skills/telegram-bot-ui/references/widget-patterns.md) | monitoring dashboard, booking, shop card, shared quiz, job progress, design a widget from words, REST data browser |
| [70–75 · Premium emoji](skills/telegram-bot-ui/references/emoji-packs.md) | restyle to one pack, icons from zero, channel series, mixed eligibility, Premium lapse, pack migration |

Full index by task, API symbol, version and context: [`recipes/README.md`](skills/telegram-bot-ui/recipes/README.md).

**Code:** Python ([`examples/python/tgkit`](skills/telegram-bot-ui/examples/python/tgkit), standard library) and TypeScript
([`examples/ts`](skills/telegram-bot-ui/examples/ts), no dependencies), plus adapters for **aiogram 3.31** and **grammY 1.46**.

```bash
python skills/telegram-bot-ui/examples/python/recipes/r01_ai_assistant.py
```

## 🛠 Tools you can use without an agent

All offline, standard library, and none of them needs a bot token.

| Check before you ship | |
|---|---|
| `python skills/telegram-bot-ui/scripts/validate_keyboard.py keyboard.json` | button and keyboard payload rules |
| `python skills/telegram-bot-ui/scripts/validate_rich.py message.json` | Rich Message limits and rules |
| `python skills/telegram-bot-ui/scripts/validate_widget.py widget.html` | widget size (server algorithm) and sandbox gaps |
| `python skills/telegram-bot-ui/scripts/validate_payload.py request.json` | structural check against the Bot API catalog |
| `python skills/telegram-bot-ui/scripts/audit_icons.py icon-map.json` | one icon family? animated mixed in? |
| `python skills/telegram-bot-ui/scripts/audit_copy.py strings.json` | translations: placeholders, symbols, label length |

| Build and explore | |
|---|---|
| `python skills/telegram-bot-ui/scripts/tg_api_lookup.py show sendWidget` | any method or type, offline |
| `python skills/telegram-bot-ui/scripts/tg_post.py preview post.json` | render a channel post (publishing is opt-in) |
| `python skills/telegram-bot-ui/scripts/build_widget.py src.html --strict` | build a widget from the kit, report its size |
| `python skills/telegram-bot-ui/scripts/preview_widget.py widget.html` | mock preview page (not a real client) |
| `python skills/telegram-bot-ui/scripts/emoji_packs.py capture` | how to collect real custom emoji ids |
| `python scripts/install.py --host all --dry-run` | where the skill would be installed |
| `python scripts/run_checks.py` | every check in this repository |

## ✅ Quality and honesty

| | |
|---|---|
| **Bot API** | verified against the official **Bot API 10.4** docs on **2026-11-15** — sources and dates in [`references/official-sources.md`](skills/telegram-bot-ui/references/official-sources.md) |
| **Hosts** | skill paths, subagent and plugin manifests and rule files verified against each host's docs on **2026-11-15** ([`docs/hosts.md`](docs/hosts.md)); the Claude Code plugin passes `claude plugin validate --strict` |
| **Tests** | **414 Python** and **31 TypeScript** tests run offline on Linux and Windows in CI, plus contract tests against the real aiogram and grammY packages |
| **Drift** | host entry files are generated from `skills/telegram-bot-ui/SKILL.md` and one routing table by `scripts/build_adapters.py`; CI fails when they drift |

What is **not** verified yet, said plainly:

- **Agent evals are prepared, not yet run.** [`evals/`](evals/) holds activation prompts (English and
  Russian, with and without API names) and behavioural tasks with pass criteria for every
  capability; `scripts/run_evals.py` validates them and can run the activation set against the
  Claude Code or Codex CLI. No agent run has been recorded yet.
- Cursor, Antigravity, Copilot, Devin and Cline were checked by documentation only, not by running them.
- Live calls to Telegram and rendering in the Telegram apps. The skill tells the agent to say which
  level of evidence it has — a JSON check is not a client test.

## ❓ FAQ

<details>
<summary><b>Does it change my bot?</b></summary>

No. It is knowledge and tools for your agent; the agent edits your bot when you ask.
</details>

<details>
<summary><b>Does it send messages or need my token?</b></summary>

The checks never do. Publishing and agent operation need a bot token from an environment
variable, and the skill requires your explicit approval before anything is published.
</details>

<details>
<summary><b>Do I need Telegram Premium?</b></summary>

Only for custom emoji icons in a regular bot (or Fragment usernames).
</details>

<details>
<summary><b>My bot uses an old SDK.</b></summary>

The skill checks what your SDK supports and either suggests an upgrade or adds a small, isolated
adapter with a "remove when" note.
</details>

<details>
<summary><b>Which language or framework does my bot need to use?</b></summary>

Any. The skill is SDK-agnostic: it reasons in Bot API payloads, and ships runnable examples in
Python and TypeScript plus adapters for aiogram and grammY.
</details>

## 🗂 Repository layout

```
skills/telegram-bot-ui/   the skill; installers copy only this folder
  SKILL.md          entry point the agent reads first (routing, rules, invariants)
  references/       focused guides, loaded only when a task needs them
  recipes/          end-to-end recipes, registry.json, manifest.json
  examples/         runnable Python/TS code, widgets, fixtures, payloads, SDK adapters
  scripts/          validators and tools the skill runs (offline)
  data/             offline Bot API catalog, emoji pack registry
  agents/           Codex metadata (openai.yaml)
scripts/            installer, adapter generator, eval runner, check runner (offline)
agents/             Claude subagents, Codex custom agents
adapters/           routing table and generated entry files for other hosts
.claude-plugin/     Claude Code plugin and marketplace manifests
llms.txt            index of every document for agents that read files on demand
docs/hosts.md       how each agent host discovers skills, with sources
tests/, evals/      offline tests; activation and behavioural evals
```

## 🤝 Contributing

Issues and pull requests are welcome — especially screenshots from real Telegram clients, new
recipes, SDK support updates and eval runs on more hosts.

1. Cite official Telegram docs for capability claims and mark anything unverified.
2. Keep `skills/telegram-bot-ui/SKILL.md` compact.
3. After editing `skills/telegram-bot-ui/SKILL.md` or `adapters/`, run `python scripts/build_adapters.py`.
4. Run `python scripts/run_checks.py` before opening the PR.

## License

[MIT](LICENSE).

<sub>Community project; not affiliated with or endorsed by Telegram. Telegram changes the Bot API
often — verify current behavior against the [official docs](https://core.telegram.org/bots/api)
before relying on a capability.</sub>
