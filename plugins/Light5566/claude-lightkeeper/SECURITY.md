# Security

## Reporting a vulnerability

Please report it privately, not in a public issue.

- Use **Report a vulnerability** on this repository's [Security tab](https://github.com/Light5566/claude-lightkeeper/security/advisories/new).
- If that button isn't there, open an issue titled "Security contact" with no details in it, and a private channel will be set up.

Say which version you ran (`vault doctor` prints it), which agent (Claude Code, Hermes Agent or Codex), and how to reproduce it. You should get a first answer within a week.

Fixes land on `main` and in the next release; the release notes credit the reporter unless asked not to.

## Supported versions

The latest release. Older versions are not patched: update the plugin.

## What Lightkeeper does on your machine

Knowing this helps judge whether something is a vulnerability.

- **Hooks run local Python.** Each hook starts `python3` on the plugin's own scripts, with a 10 to 15 second timeout. They only add context to the agent; they never block or change a tool call, and they exit 0 on any error.
- **They run read-only git commands** in your checkout and in the vault folder (`rev-parse`, `remote get-url`, `status`, `log`, `ls-tree`, `symbolic-ref`, `merge-base`, `cat-file`).
- **They read** the vault registry `~/.claude/vaults` and the vault folders it lists.
- **They write** the vault's own `_meta/index.json`, a per-session state file in the system temp folder, and two small per-machine files beside the registry (`vaults-branches.json`, `vaults-hinted.json`).
- **No network calls, no telemetry, no credentials.** The one exception is the HTML map from `vault export --html`, which loads d3 from cdnjs when you open it in a browser.
- **Setup commands change more, and only when you run them:** `vault init` creates the vault folder, adds it to the registry and copies a launcher to `~/.local/bin`; `--git-hook` installs report-only git hooks; `--backup-remote` adds a hook that pushes the vault. `vault init --forget` undoes the registration and removes those git hooks.
- **Notes are text the agent reads.** A vault you clone from someone else is input to your agent, so treat a shared vault with the same care as shared instructions files.

Python 3.9 or newer, standard library only: there are no third-party dependencies to audit.
