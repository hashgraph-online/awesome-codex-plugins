# Clean Room

Clean Room is an agent workflow for turning authorized source analysis into clean behavioral specs, clean implementation plans, and clean destination code. When no indexable source code is available, it can use authorized screenshots/images as contaminated fallback evidence for behavior specs.

It is a POC based on ideas from [malus.sh](https://malus.sh/blog.html). It is an engineering risk-reduction workflow, not legal advice, and it does not create a legal safe harbor.

## What This Is / Does

Use this package when you need documented separation between source-reading work and clean implementation work.

It installs:

- Clean-room skills for Codex, Claude Code, and other agent runtime layouts.
- Role-agent prompts for contaminated analysis, clean planning, clean implementation, and final polish.
- JSON schemas and examples for durable workflow artifacts.
- Hook guardrails that help keep source material out of clean artifacts.
- A small CLI for runtime installation, bootstrap folders, preflight contracts, canonical artifact templating and validation, hook smoke tests, and the bounded inner clean-room runner.

The workflow creates clean behavioral spec packages and clean implementation outputs. It does not generate replacement code directly from source.

Core boundary:

- Contaminated roles may read authorized source or fallback visual evidence and write contaminated artifacts.
- Source-denied roles may read only clean artifacts, implementation roots, schemas, and approved public/reference roots.
- Clean implementation code is written only under the clean implementation root.
- Raw source, raw screenshots, source or visual paths, private identifiers, raw diffs, copied comments, copied UI text, and source-shaped pseudocode must not cross into clean handoff artifacts.

![Clean Room Architecture](assets/clean-room-arch.svg)

For the full boundary model, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). For CLI and troubleshooting details, see [docs/REFERENCE.md](docs/REFERENCE.md).

## Install

Requires Node.js `>=22`.

Recommended path:

```bash
npm install -g clean-room-skill
clean-room-skill
```

The first command installs the CLI. The second command starts the interactive installer for runtime files, skills, agents, and hooks.

For a direct global runtime install, pass the runtime flag:

```bash
clean-room-skill --claude --global --yes
clean-room-skill --codex --global --yes
clean-room-skill --opencode --global --yes
clean-room-skill --all --global --yes
```

If you do not want the CLI installed globally, run the same installer once through `npx`:

```bash
npx clean-room-skill@latest --claude --global --yes
npx clean-room-skill@latest --codex --global --yes
npx clean-room-skill@latest --all --global --yes
```

Those `npx` commands install the selected runtime files globally. You do not need to keep running `npx` to use the installed Claude Code, Pi, Codex, or other runtime entry points.

For ccsilo variants, use the collapsed ccsilo shortcut below. For other modified Claude directories, add `--config-dir <path-to-claude-config-root>` to target that Claude config root explicitly. If Claude is launched through a non-ccsilo wrapper, set `CLEAN_ROOM_CLAUDE_EXECUTABLE=/absolute/path/to/wrapper`; the installer runs that exact executable and rejects relative, cwd-local, and `node_modules/.bin` paths.

Claude global installs use Claude's plugin system for skills and agents, so entry points are namespaced as `/clean-room:init`, `/clean-room:preflight`, and `/clean-room`. The installer still manages hook files and migrates older standalone Claude skill copies out of the config root on reinstall or update.

Hook modes:

- `--hooks=safe`: default. Hooks are installed but enforce only during clean-room role sessions with the required environment.
- `--hooks=strict`: fail-closed hook mode for dedicated Codex, Claude, or OpenCode clean-room homes.
- `--hooks=copy-only` or `--no-hooks`: copy hook files without registering runtime hook config.

Verified runtimes are Codex, Claude Code, and OpenCode. OpenCode support uses native skills, commands, and a generated local plugin bridge for hook enforcement. Other runtime layouts are installed on a best-effort basis. See [docs/REFERENCE.md](docs/REFERENCE.md#runtime-support) for the full support table and install roots.

Marketplace install is also supported.

Claude Code:

```text
/plugin marketplace add https://github.com/whit3rabbit/clean-room-skill.git
/plugin install clean-room@clean-room-skill
```

Codex:

```bash
codex plugin marketplace add https://github.com/whit3rabbit/clean-room-skill.git
```

Pi:

```bash
pi install npm:clean-room-skill@latest
npx clean-room-skill@latest --pi --global --yes
```

Pi-native package install is preferred. This package declares `pi.skills: ["./skills"]`, so `pi install npm:clean-room-skill@latest` lets Pi discover the bundled `SKILL.md` entry points directly. Use the `npx ... --pi` installer only when you want this repo's compatibility installer to manage the same files alongside other runtimes. Global Pi compatibility installs target `~/.pi/agent`; local installs target `.pi`.

Both Pi install paths load bundled skills as `/skill:<name>`, for example `/skill:clean-room`. Pi installs do not currently register clean-room hooks. Installer-managed Pi layouts copy the hook scripts to `hooks/clean-room/` for inspection and future bridge work, but those files are not active enforcement in Pi.

Pi hook enforcement would need a Pi extension, not a `settings.json` edit. This package does not ship that extension yet, so clean-room safety in Pi still depends on role separation, path isolation, schema validation, and any supported hook runtime used for enforcement.

<details>
<summary>CCSILO Claude silos</summary>

CCSILO is an optional Claude Code silo wrapper convention, not a standard agent runtime. It is useful when you keep a separate Claude Code home and wrapper for providers such as OpenRouter.

For a ccsilo OpenRouter silo, use the silo wrapper and the silo `configDir` from its `variant.json`:

```bash
SILO=openrouter

clean-room-skill --ccsilo "$SILO" --hooks=safe --yes

clean-room-skill status --ccsilo "$SILO"
clean-room-skill update --ccsilo "$SILO" --yes
clean-room-skill doctor --ccsilo "$SILO" --hooks=safe --coverage
```

When running inside a ccsilo-launched Claude session, `--ccsilo` can auto-detect the variant from `CLAUDE_CONFIG_DIR`, so the variant name can be omitted. The shortcut reads `variant.json`, resolves the silo config and wrapper, and installs Claude support there. If `status` reports an active plugin version or path mismatch, run `clean-room-skill update --ccsilo "$SILO" --yes` before manually deleting old plugin cache folders.

If you want the agent to use the OpenRouter ccsilo path from the start, paste this at the beginning of the session:

```text
Use the ccsilo OpenRouter Claude variant for this clean-room run. Prefer the durable runner, not main-chat role work.

First verify/update the silo:
clean-room-skill status --ccsilo openrouter
clean-room-skill doctor --ccsilo openrouter --hooks=safe --coverage

When running unattended/resume, launch:
clean-room-skill run --task-manifest <task-root>/contaminated/task-manifest.json --ccsilo openrouter

Do not use plain claude, do not search plugin cache paths, and do not pass --schema-dir. Use bundled generated CLI schemas.
Never set ANTHROPIC_AUTH_TOKEN or API keys in ccsilo settings.json, .claude.json, or any settings file.
```

If the agent is already running inside that ccsilo session, the run command may omit the variant name:

```bash
clean-room-skill run --task-manifest <task-root>/contaminated/task-manifest.json --ccsilo
```

</details>

## Workflow

1. Initialize or bootstrap the run.
   Use `clean-room-skill init`, `/clean-room:init`, or `/skill:init` to create neutral external run folders and record run preferences. The active `init-config.json` stays out of the clean implementation repository.

2. Record the goal contract.
   Use `/clean-room:preflight` or `/skill:preflight` for the conversational flow, or `clean-room-skill preflight` for artifact-first CLI setup. This creates or validates `preflight-goal.json` on the contaminated/controller side before source discovery, attended mode, or unattended mode.

3. Start the controller.
   Use `/clean-room:attended` or `/skill:attended` for human review gates. Use `/clean-room:unattended` or `/skill:unattended` only after preflight allows bounded unattended work with finite iteration limits and no open questions.

4. Refocus when state is unclear.
   Use `/clean-room:refocus` or `/skill:refocus` to audit durable artifacts, compare them to declared scope, and route the run back to missed gates without adding scope.

Use `/clean-room` or `/skill:clean-room` when you want the skill to talk through setup, inspect where the run is, and decide whether to continue, refocus, resume, or start over.

The CLI also has a bounded inner-loop runner for already approved unattended spec slices:

```bash
clean-room-skill run \
  --task-manifest ~/Documents/CleanRoom/amber-meadow/tasks/task-1234abcd/contaminated/task-manifest.json \
  --agent-runtime claude \
  --max-iterations 3
```

For CCSILO, prefer the `--ccsilo [variant]` shortcut from the collapsible section above. For other Claude wrappers, set `CLEAN_ROOM_CLAUDE_EXECUTABLE=/absolute/path/to/wrapper` and pass the wrapper config with `--agent-config-dir`. For example, an OpenRouter silo uses the `openrouter` wrapper path, not a separate `claude` command. Never persist `ANTHROPIC_AUTH_TOKEN` or API keys into ccsilo or Claude settings files.

The `run` command is not the normal starting point. It executes one bounded inner clean-room loop after the outer controller has created approved durable artifacts.

You can also list, template, and validate canonical workflow artifacts directly:

```bash
clean-room-skill artifact kinds
clean-room-skill artifact template --kind behavior-spec --output ./behavior-spec.json
clean-room-skill artifact validate --path ./behavior-spec.json
```

`artifact validate` checks JSON schema conformance; pass `--task-manifest <path> --role <role>` to also run leakage and handoff checks under the matching root and role policy.

Claude Code skills use `/clean-room:<name>`. Pi skills use `/skill:<name>`. In Codex, invoke the `clean-room` plugin or bundled skills through `@` or the skills UI.

Useful maintenance commands:

```bash
clean-room-skill doctor --runtime codex --hooks=safe
clean-room-skill status --global
clean-room-skill update --global --yes
```

Reference files:

- [docs/REFERENCE.md](docs/REFERENCE.md): CLI flags, hook modes, troubleshooting, and local verification.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): operating model, roles, environment, guardrails, and flow details.
- [docs/HOOKS.md](docs/HOOKS.md): hook install locations, generated matchers, and per-hook behavior.
- [skills/clean-room/references/PROCESS.md](skills/clean-room/references/PROCESS.md): detailed clean-room process.
- [skills/clean-room/references/LEAKAGE-RULES.md](skills/clean-room/references/LEAKAGE-RULES.md): clean handoff rules.

## Development

Install dependencies:

```bash
npm ci --ignore-scripts
```

Run tests:

```bash
npm test
```

Run installer tests only:

```bash
npm run test:install
```

Run the full local verifier:

```bash
npm run verify
```

Documentation-only changes usually need review plus link/path checks, not the full test suite.

Useful development checks:

```bash
node --check bin/install.js
node --test tests/run.test.js
npm pack --dry-run
```

Python schema validation requires `jsonschema` with format extras:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "jsonschema[format]>=4.18,<5"
.venv/bin/python tests/validate_jsonschema.py
```

Use `st` for repository search.
