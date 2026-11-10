---
name: desk-setup
description: "Install and verify the option desk command line tools so the option_* MCP tools and the optiondesk commands actually work. Use when a desk skill reports that no fresh figures can be produced, when optiondesk is not found, when the MCP tools are missing or failing, when the plugin was installed but nothing runs, or when the user asks how to set this up. Not for analysing options; it only gets the tools working."
---

# Getting the desk working

The skills in this plugin describe a set of local tools. Installing the
plugin gives you the instructions; it does not install the tools. This
skill closes that gap.

## First, find out what is actually missing

```
optiondesk doctor
```

If that runs, read its output: it reports whether the analytics engine is
present, which providers can answer, which credentials are configured
without printing them, and where artifacts are written. Fix what it names
and stop here.

If the shell says `command not found`, continue.

## Install

```
curl -fsSL https://raw.githubusercontent.com/Iman/agent-driven-options-desk-and-skills/main/install.sh | bash
```

That creates a virtualenv at `~/.optiondesk`, installs the analytics engine
and the shell, links `optiondesk` and `optiondesk-mcp` into `~/.local/bin`,
copies the skills into both `~/.claude/skills` and `~/.agents/skills`, and
registers the MCP server with every agent runtime it finds. Re-running is
safe, and `./install.sh --uninstall` removes only what it created.

Python 3.11 or newer is required. Yahoo needs no API key, but it remains
disabled until the user accepts its local personal-use boundary. Use
`--accept-yahoo-terms` only after the user reads Yahoo's terms. The flag does
not permit hosting, business use, public display, or redistribution.

The acknowledgement is recorded as one line in `~/.optiondesk/config.env`,
and that is where the provider gate reads it from. Nothing needs exporting
into a shell profile. Remove the line to withdraw it.

## Run the demo from a checkout

This workflow installs the tools and runs analytics, including a paper position.
Use it when the user requests the demo.
For installation alone, use the installer described above.

If Yahoo access is already acknowledged, run:

```
./run.sh
```

For a first run, obtain the user's acknowledgement after they read Yahoo's terms.
Then run `./run.sh --accept-yahoo-terms`.
Without that flag, the runner leaves acknowledgement to the installer's interactive prompt or the existing configuration.
Never add the flag merely because the user asked to install the tools.

From a checkout, this installs anything missing, repairs a virtualenv built
for the wrong CPU architecture, pulls live chains for SPY and QQQ, runs the
Greek ladder, dealer positioning, the structure comparison, a simulation and
a backtest per structure, opens a paper position, then serves the dashboard
and opens a browser. `./run.sh --help` lists the options; `--dry-run` prints
every command without running one.

## When the tools are installed but nothing imports

On Apple silicon, a script whose shebang is `/usr/bin/env bash` picks up a
Homebrew bash under `/usr/local` when one is installed, and that binary is
x86_64. Everything it installs is x86_64 too, so the virtualenv imports
cleanly from that shell and fails from every native one:

```
ImportError: ... incompatible architecture (have 'x86_64', need 'arm64')
```

The installer refuses to build under translation now and repairs wheels that
are already wrong. If a user is stuck on this before updating, re-running the
installer fixes it, and `arch -arm64 ./install.sh` forces the point.

## The failure almost everyone hits

`~/.local/bin` is not on the PATH. The installer creates the two commands
there and warns rather than editing your shell profile, because editing
somebody's profile without asking is worse than a warning.

Check:

```
echo $PATH | tr ':' '\n' | grep -c "$HOME/.local/bin"
```

If that prints 0, add it to your shell profile:

```
export PATH="$HOME/.local/bin:$PATH"
```

Then open a new shell. This also matters to the MCP server, whose plugin
entry names the bare command `optiondesk-mcp` and resolves it through PATH.

## Verify, in this order

```
optiondesk doctor                 engine, providers, credentials, paths
optiondesk expiries SPY           reaches the network and lists expiries
optiondesk chain SPY              writes the first artifact
optiondesk greeks --band 0.06     computes from it
```

If `doctor` works and `expiries` does not, the problem is network or
provider, not installation. If `chain` works and `greeks` reports the
engine is unavailable, the engine did not install; re-run the installer
without `--no-engine`.

## What to tell the user when it still will not work

Say plainly that no fresh figures can be produced, and why. Do not
substitute remembered or example numbers for a chain that was never
pulled, and do not present a model value as a quote. A skill with no tools
is a skill that explains the desk; it is not a desk.

## What this cannot fix

In ChatGPT on the web or on a phone, there is no local process to install
and nothing here will make local tools run. Do not ask the user to install a
local process in that session. Use an attached remote MCP server when one is
present. Without one, the skills can analyse user-provided data only.

Hosted deployments must set `PUBLIC_DATA_MODE=demo` or `licensed`. Demo mode
blocks all external providers. Licensed mode permits only a provider that has
an explicit approval for public display, derived outputs, storage, and MCP
delivery. Never change this mode to work around a provider refusal.

## Reporting rules

They apply here too, briefly. Never present a remembered or example figure
as a fresh one, and say plainly when the tools are absent rather than
working around it. Never recommend a trade.

The full terms are in DISCLAIMER.md, which ships beside this skill when it
is installed from a package and sits at the repository root otherwise.
