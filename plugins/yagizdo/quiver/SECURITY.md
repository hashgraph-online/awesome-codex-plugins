# Security Policy

## Supported Versions

Only the latest release receives fixes. Quiver is installed from this repository, so the fix path is a new release plus a plugin update or a `git pull` -- there are no backport branches.

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Anything older | No -- update first, then report if it still reproduces |

## Reporting a Vulnerability

Use GitHub's private vulnerability reporting: open a [draft advisory](https://github.com/yagizdo/quiver/security/advisories/new). The report stays private until a fix ships.

Do not open a public issue for a vulnerability.

Include:

- The file and line you believe is at fault (`hooks/scripts/...`, `install.sh`, a shell block in a `SKILL.md`)
- Steps that reproduce it, and what an attacker gains
- Your OS, your shell, and the version from `.claude-plugin/plugin.json`

Expect a first reply within 7 days. If a fix is warranted it ships in the next release, and you are credited in the advisory unless you ask otherwise.

## Scope

Quiver ships bash that runs on your machine and markdown prompts that an AI CLI executes. In scope:

- `hooks/scripts/` -- the PreToolUse guard and the PreCompact handover hook, both invoked automatically by the CLI
- `install.sh` -- symlink creation and `--uninstall` removal
- Inline shell blocks in `skills/**/SKILL.md`
- The MCP server entries in the plugin manifests

## Known Non-Issue

`hooks/scripts/pre-tool-use-guard.sh` is an accident brake, not a security boundary. It reads the literal command string before the shell ever sees it, so shell escapes, variable expansion, aliases, base64, and deliberate obfuscation are outside its threat model by construction. A report demonstrating a bypass of that kind describes documented behavior, not a vulnerability.

The guard denying a safe command, or failing in a way that breaks the hook, is an ordinary bug -- open a public issue for it.
