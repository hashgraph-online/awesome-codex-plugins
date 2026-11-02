# Keep Mac Awake plugin for AI agents

This plugin teaches an AI agent to use Keep Mac Awake, a macOS app that keeps a MacBook with Apple silicon awake with the lid closed during a session. It needs the app, which is installed separately and is a paid app with a free trial ([keepmacawake.com](https://keepmacawake.com)). With it, the agent starts a timed session before long work, stops it when the work is done, and tells you when the app needs something from you, such as AC power or a purchase after the trial.

It has two parts:

- **A skill** (`skills/keepmacawake/SKILL.md`, in the Agent Skills format): when to start and stop a session, what to ask you first, and what to do when the command refuses.
- **A session-start hook** (`hooks/session-start.sh`): when an agent session begins, it runs `keepmacawake status --json` once and adds a few sentences of its own to the agent's context, built from a few fields of the reply (whether a session runs, its time left, the trial, a newer version), so the agent knows the app is there without being reminded. It never passes on the app's text or the Mac ID. It is read only: it makes no network connection and never starts, stops or changes anything.

The agent starts timed sessions on its own and tells you in one line. It always asks before a session without a time limit, battery use, installing the app and buying.

## What it runs

- **The hook** runs `keepmacawake status --json` on this Mac, with a 2-second timeout, and reads its fields with `plutil`; nothing else.
- **The skill** has the agent run the `keepmacawake` command (`status`, `start`, `stop`, `config`, `buy`, `restore`, `capabilities`), and `sysctl` and `sw_vers` to check that the Mac fits. `keepmacawake buy` opens the purchase page on keepmacawake.com in your browser, and `keepmacawake restore`, when you ask for it, sends this Mac's ID to keepmacawake.com to find an earlier purchase. When a task you asked for needs the app and it is missing, the agent offers it once and gives you the download link; you download and open the installer yourself.
- The plugin never downloads or runs an installer or a script, never uses `sudo` and never pays.
- It works where the agent's commands run on your Mac itself (Claude Code, Codex, Cursor, Copilot CLI). On anything else, such as a cloud container, the hook stays silent and the agent says the app is out of reach.
- Codex runs commands in a sandbox that cannot reach the app's background service, and so do Cursor and Claude Code when sandboxing is on. The agent then asks to run `keepmacawake` outside the sandbox; approve it.

## Examples

- "Run the full test suite and fix what fails. I'm closing the lid and will check back from my phone."
- "Keep the Mac awake for the next 2 hours while this migration runs."
- "Is Keep Mac Awake on, and how much time is left?"

## Install

Claude Code:

```sh
claude plugin install keep-mac-awake --marketplace bartdudzic/keepmacawake
```

Codex (it asks you once, in `/hooks`, to trust the plugin's hook):

```sh
codex plugin marketplace add bartdudzic/keepmacawake
codex plugin add keep-mac-awake@keepmacawake
```

GitHub Copilot CLI:

```sh
copilot plugin marketplace add bartdudzic/keepmacawake
copilot plugin install keep-mac-awake@keepmacawake
```

Gemini CLI (the skill as the extension's context, without the hook):

```sh
gemini extensions install https://github.com/bartdudzic/keepmacawake
```

Antigravity (the skill only, without the hook), from a clone of this repository:

```sh
git clone https://github.com/bartdudzic/keepmacawake
agy plugin install keepmacawake/plugins/keep-mac-awake
```

Any agent that reads Agent Skills (the skill only, without the hook):

```sh
npx skills add bartdudzic/keepmacawake -g
```

The plugin needs the Keep Mac Awake app (any Mac with Apple silicon and macOS 26 or later): <https://keepmacawake.com>.

## Privacy

The plugin itself sends nothing anywhere; of the commands it runs, only `keepmacawake restore` goes online, with this Mac's ID, and `keepmacawake buy` opens a page in your browser, both only when you ask. keepmacawake.com stores nothing about these requests: it looks the Mac ID up with Stripe, and its host (Cloudflare) and Stripe keep request records under their own policies. The hook's lines become part of the agent's conversation, so the agent's provider receives them: whether a session runs, its time left, the trial's time left and a newer version. They do not include this Mac's ID. When the agent runs `keepmacawake status --json`, its output also enters the conversation; it includes the Mac ID that a purchase is tied to (`access.mac_id`). The app's own data use is in its [privacy description](https://keepmacawake.com/privacy.md).

## Troubleshooting

- `keepmacawake: command not found`: the app is not installed, or its command is missing from `/usr/local/bin`. Install the app from <https://keepmacawake.com>.
- Exit code 6: the app's background service is off. Open Keep Mac Awake from Applications, or run `keepmacawake app launch`.
- A session refused on battery: plug in AC power, or allow battery use in the menu bar panel.
- To stop using the plugin, disable or uninstall it in your agent (for Claude Code: `claude plugin uninstall keep-mac-awake`). To remove the app, open the uninstall package from the app's release.

## Support

Write to hi@keepmacawake.com. Security issues: see [SECURITY.md](https://github.com/bartdudzic/keepmacawake/blob/main/SECURITY.md). Keep Mac Awake is not affiliated with Apple.

## License

The plugin is under the [MIT License](LICENSE). The Keep Mac Awake app it controls is not: buying it after the free trial is covered by its own terms.
