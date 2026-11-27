# MarginCue for Codex

The same card as in Claude Code, in Codex:
- **Before you send:** how the agent will read the prompt, your names checked against the code, a control for each open choice, and a sketch of the result.
- **While Codex works:** its own choices become switches.
- **After the turn:** a receipt.

## Install

Codex CLI 0.171 or later, and Node 20 or later:

```sh
npx -y github:fus3r/margincue setup
```

Setup does three things:
1. It installs the Codex plugin (`codex plugin marketplace add fus3r/margincue`, then `codex plugin add margincue@margincue`).
2. It asks about your work, your level in the relevant fields, and which decisions you keep.
3. It installs the card's terminal relay (`~/.margincue/bin/margincue-relay`, macOS and Linux) and offers a `codex` alias, so Codex starts with the card under its prompt.

After accepting the alias, open a **new terminal** and run `codex`. The new terminal loads the alias from your shell profile. In VS Code, create a new terminal tab.

Run the command below from your shell if you skipped the alias.

```sh
node "$HOME/.margincue/bin/margincue.mjs" codex
```

In your next Codex session, trust the plugin's hooks when Codex asks (press `t`), or review them first with `/hooks`.

## Use

Write the prompt in Codex as usual. The card sits under Codex's prompt box and follows the draft: how the agent will read it, your names checked against the code, a row for each open choice, and the sketch.

| Key | What it does |
| --- | --- |
| `alt+↑` / `alt+↓` | Next row / change its value (or click an option) |
| `enter` | Send with the configured card choices |
| `ctrl+g` | The full-screen card (below) |
| `ctrl+]` then `c` | Read the draft in `key` mode (relay 0.1.3 or later) |
| `ctrl+]` then `k` | Keep all shown selections (relay 0.1.4 or later). You can also click **Keep all** |
| `ctrl+]` then `d` | Hide the card for this prompt |
| `ctrl+]` then `t` | MarginCue off or on for this session |

While the card has rows, `alt+↑` and `alt+↓` are the card's; otherwise they stay Codex's (edit a queued message, step back through prompts).

**How it works.** `margincue codex` starts Codex in a terminal of its own, a few rows shorter than your window, and draws the card in the rows below it. It reads the prompt box from what Codex draws. It adds the card's decisions and open questions when you press Enter, and can write a change you ask for while Codex works. When a popup (`@` files, `/` commands) or a dialog is open, Enter and every other key go to Codex untouched. If the relay cannot run (Windows, no binary, `MARGINCUE_RELAY=off`), Codex starts as usual and ctrl+g opens the card.

### The full-screen card (ctrl+g)

Press **ctrl+g** in the prompt. Codex hands the draft to MarginCue, which shows the card above it while you edit:

| Key | What it does |
| --- | --- |
| `alt+↑` / `alt+↓` (or `ctrl+↑` / `ctrl+↓`) | Next row / change its value |
| `tab`, then `1`–`9`, `x`, `s`, `p`, `c` | Pick an option, drop a row, show the sketch, attach it, read the draft |
| `tab`, then `k` | Keep all shown selections. Pick hard-to-undo choices individually |
| `enter` | Return to Codex with the configured card choices. Press `enter` there to send |
| `shift+enter` (or `alt+enter`) | New line |
| `ctrl+e` | Your own editor on the draft |
| `esc` | Back to Codex, draft unchanged |

The card's readings use your own Codex login: each is a one-off thread on the lightest model your account offers, at low effort, never saved to your history. MarginCue's own readings skip your hooks.

**While Codex works**, the choices the agent made for you show under the empty prompt as switches. Switch one with `alt+↓` and MarginCue writes the amendment in Codex's prompt box; `enter` sends it into the running turn. **After the turn**, the same keys write the follow-up prompt, and the receipt line lists who decided what. In the full-screen card, ctrl+g in the empty prompt lists the same switches.

## Codex in the ChatGPT desktop app

On a new task, Codex opens the card at Enter and waits. In `auto` mode the card fills in as MarginCue reads. In `key` mode click **Read prompt** to start. Click an underlined choice to change it. A missing name's menu lists the closest names in the code. If a name matches several files, pick the file from its menu. The preview redraws when you change a choice.

**Keep all** sets the shown selections as your decisions. Pick hard-to-undo choices individually. **Go ahead** sends the choices according to your `send` setting, along with your note and the preview if it is ready for those choices. **Use as written** sends the original prompt alone. The card shows what was sent, and the receipt follows the work. If the card tool is unavailable, `auto` falls back to a text card and `key` continues with the original prompt.

### Test from this checkout

From the repo root, with Node 20 or later and the Codex CLI on your path, build the package and add its local marketplace.

```sh
npm --prefix mods/codex run build
codex plugin marketplace add "$PWD/mods/codex"
codex plugin add margincue@margincue-local
```

After a rebuild, run `codex plugin add margincue@margincue-local` again to install the new build. If the GitHub copy is also enabled, disable it in Codex's plugin settings during the test.

Open the Codex CLI and run `/hooks`. Review and trust the three hooks listed for `margincue@margincue-local`. Codex skips new or changed hooks until you review them, even when the MarginCue MCP server is already connected. A card needs the `UserPromptSubmit` hook. Start a fresh local Codex thread in ChatGPT Desktop after reviewing the hooks.

Open a new Codex thread in a project and send a creation prompt such as `Build a weekly activity report for team owners with a CSV download.` Confirm that the card appears before work starts, and fills in within a few seconds. Change a choice, wait for the preview to update, add a short note, and press **Go ahead**. Check that Codex works on the original prompt, shows the receipt, and opens no second card. In a fresh thread, change a choice, press **Use as written**, and confirm that the follow-up contains only `Go ahead with my prompt as written.`

## The IDE extension, and the CLI without the relay

The IDE extension and the CLI without either card show a text card at the start of the reply in `auto` mode. `key` skips that automatic card. The IDE extension exposes neither a pre-send card for `send` nor a shortcut to read on demand. In the CLI, use `ctrl+g`, then `tab`, then `c` for a reading without the relay. Marked choices and receipts still work in the IDE.

## Settings and removal

Edit `~/.margincue/settings.json`. Start a new CLI to pick up relay settings. `margincue status` shows the current values.

| Setting | What it does |
| --- | --- |
| `"send": "open"` (default) | Send your picks, saved choices and written step order as decisions. Codex settles the other rows as questions with unmarked options and says what it chose. |
| `"send": "all"` | Also send ordinary defaults as decisions. |
| `"send": "picked"` | Send your picks, saved choices and written step order. |
| `"read": "auto"` (default) | Read automatically. |
| `"read": "key"` | Wait for `ctrl+]`, then `c` in the relay, `tab`, then `c` in the full-screen card, or **Read prompt** in the desktop card. |

Hard-to-undo choices stay open until you pick an option. An unanswered file choice can also list its candidate paths under `Where things are`.

Other settings include `"mode": "off" | "quiet" | "auto"`, `"sketch": false`, `"blanks": false`, and `"relay": false`. `MARGINCUE_RELAY=off` skips the relay for one launch.

To update a stated level, run `margincue level <profile> <learning|practitioner|expert>`. The profiles are `general`, `ml-research`, `product`, and `system-design`. The copy installed by setup also works directly.

```sh
node "$HOME/.margincue/bin/margincue.mjs" level ml-research expert
```

Relaunch Codex to apply the change in a running terminal session. The desktop reader checks settings on each reading.

To remove MarginCue:
1. Run `codex plugin remove margincue@margincue`.
2. Delete the `codex` alias from your shell profile.
3. Delete `~/.margincue`.

## Development

```sh
cd mods/codex
npm run build                      # bundles dist/margincue.mjs and the inline dist/card.html
node --test ../../spec/codex.unit.ts ../../spec/codex-band.unit.ts
```

The relay is Rust, in `crates/margincue-relay`. Its live test runs the installed Codex in a fresh home with inert credentials:

```sh
cargo test --release --manifest-path ../../crates/margincue-relay/Cargo.toml
cargo test --release --manifest-path ../../crates/margincue-relay/Cargo.toml --test live -- --ignored --test-threads=1
```

The composer shares its core, layout and prompts with the Claude Code mod in `../claude-code`.
