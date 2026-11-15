# Security policy

## Reporting a vulnerability

Report privately through GitHub: **Security → Report a vulnerability** on
<https://github.com/hlibsuslov/telegram-bot-ui/security/advisories/new>. Include the file,
the command or input that triggers the problem, and what an attacker gains. Please do not
open a public issue for a vulnerability. If the private form is unavailable, open an issue
that only asks for a private contact, without details.

Fixes land on `main`; there are no maintained older branches.

## What the code in this repository does

The skill itself is Markdown. The scripts and examples are there to check and demonstrate
it, and are built to be safe to run on a developer machine:

Below, `skill/` is short for the skill folder `skills/telegram-bot-ui/`; `scripts/` alone is
the repository's own tooling.

- **Offline by default.** `scripts/` and `skill/scripts/` use the Python standard library
  only and read local files. The checks (`scripts/run_checks.py`) never need a bot token and
  never touch the network.
- **Tokens only from the environment.** Anything that can talk to Telegram takes the bot
  token from a named environment variable (`--token-env`, `TELEGRAM_TEST_BOT_TOKEN`),
  never from a command-line argument or a file in the repository. No token is committed;
  `scripts/validate_skill.py` fails on anything shaped like one.
- **Live modes are opt-in.** Sending needs an explicit flag (`skill/scripts/tg_post.py
  --live`, the agent bridge `--live`) or `TELEGRAM_LIVE=1` with a test-bot token; without it
  the tools do a dry run. Live emoji lookups call read-only Bot API methods only.
- **Other network use**, all explicit: `skill/scripts/sync_bot_api.py` downloads the public
  Bot API pages from `core.telegram.org` (no token); `skill/scripts/preview_widget.py
  --serve` binds to `127.0.0.1` only; `scripts/run_evals.py --execute` runs the agent CLI you
  name, in a temporary project. `scripts/install.py` writes only into the skill folders it prints, and
  `--dry-run` changes nothing.
- **No install hooks.** The `package.json` files define a `test` script only, and every
  dependency is pinned to an exact version.

## Hostile test data

Some fixtures contain attack strings on purpose, so the agent-bridge security code can be
tested against them. They are data, never executed, and nothing in the skill tells an agent
to follow them:

- `skill/examples/fixtures/agent_injection_reply.json` — a prompt-injection reply (tells the agent
  to drop its rules, run a downloaded script from a reserved `.invalid` host and send back a
  secret file); used by the agent-bridge tests and recipe 49.
- `skill/examples/fixtures/agent_commands.json` — a command with a path-traversal argument; same
  consumers.
- `skill/examples/python/agent_bridge/security.py` holds the detection patterns (override
  phrases, role claims, secret file names) that flag such input.
