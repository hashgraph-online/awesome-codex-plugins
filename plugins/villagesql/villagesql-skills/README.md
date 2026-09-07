# villagesql-skills

Agent skills for working with [VillageSQL](https://villagesql.com). Skills run
in Claude Code, agy, Codex, Cursor, Amp, Kiro, OpenCode, and OpenClaw.

## Skills

| Skill | What it does |
|---|---|
| [`vsql-install-server`](skills/vsql-install-server/) | Gets a working VillageSQL server on your machine — install, start, connect, load an extension, verify. Start here if you do not have a server yet. |
| [`vsql-extension-builder`](skills/vsql-extension-builder/) | Builds a VillageSQL extension end-to-end through a 7-phase persona-driven workflow. Discovers the current VEF API from live SDK headers — no hardcoded API names. |

More skills will be added here over time.

## Prerequisites

The skills drive a live VillageSQL server on your machine. Install one as a
prebuilt binary or a source build via the server installer:

```bash
curl -fsSL https://install.villagesql.com | bash
```

The `villagesql/server` Docker image carries the extension SDK, a C++
toolchain, and a `vsql-build-extension.sh` helper, so you can build and
install an extension inside a container. What it does not carry is
`mysql-test-run.pl`, the MTR orchestrator, so `vsql-extension-builder` cannot
complete its test phase there — that phase needs an installer or source build
on the host. See each skill's README for its full requirements.

## Installing

### Quick install

```bash
curl -sSL https://villagesql.com/skills | bash
```

Detects which agents are installed and configures each one. Supports Claude
Code, agy, Codex, Cursor, Amp, Kiro, OpenCode, and OpenClaw.
Re-running updates in place.

Override locations with env vars:

```bash
VILLAGESQL_SKILLS_SRC=~/code/villagesql-skills \
CLAUDE_SKILLS_DIR=~/.claude/skills \
  curl -sSL https://villagesql.com/skills | bash
```

### Manual install (recommended for contributors)

#### Claude Code

```bash
git clone https://github.com/villagesql/villagesql-skills.git ~/code/villagesql-skills
mkdir -p ~/.claude/skills
ln -s ~/code/villagesql-skills/skills/vsql-extension-builder ~/.claude/skills/vsql-extension-builder
```

Verify the skill is loaded by typing `/` in Claude Code — the skill name
should appear in the slash command list.

#### agy

```bash
git clone https://github.com/villagesql/villagesql-skills.git ~/code/villagesql-skills
mkdir -p ~/.gemini/antigravity-cli/plugins
ln -s ~/code/villagesql-skills ~/.gemini/antigravity-cli/plugins/villagesql
```

agy reads `plugin.json` and discovers skills from the `skills/` subdirectory.

#### OpenCode

```bash
git clone https://github.com/villagesql/villagesql-skills.git ~/code/villagesql-skills
mkdir -p ~/.config/opencode/skills
ln -s ~/code/villagesql-skills/skills/vsql-extension-builder ~/.config/opencode/skills/vsql-extension-builder
```

#### OpenClaw

```bash
git clone https://github.com/villagesql/villagesql-skills.git ~/code/villagesql-skills
mkdir -p ~/.openclaw/workspace/skills
ln -s ~/code/villagesql-skills/skills/vsql-extension-builder ~/.openclaw/workspace/skills/vsql-extension-builder
```

To update later (all agents share the same clone):

```bash
git -C ~/code/villagesql-skills pull
```

## Skill layout

Each skill follows the standard Agent Skills directory layout:

```
skills/
└── <skill-name>/
    ├── SKILL.md           # entry point — frontmatter, workflow, gates
    └── references/        # detailed material loaded on demand
        └── *.md
```

`SKILL.md` is loaded eagerly when the skill triggers and stays thin and
procedural. Detail-heavy material (standards, checklists, environment
commands) lives in `references/` and is read by the agent only when the
relevant phase needs it.

## Contributing

Issues and pull requests welcome. For substantive changes — new skills,
workflow restructuring, new references — open an issue first to discuss the
shape before writing the skill.

A few conventions:

- Keep `SKILL.md` thin. If a section exceeds a screen, ask whether it
  belongs in `references/` instead.
- Reference files describe **process and principles**, not specific API
  names — names should be discovered from live sources during the
  workflow, not hardcoded in the skill.
- Match the voice of existing skills: terse, imperative, no marketing
  language.

### Testing changes locally

The quick installer clones the repo to `~/.local/share/villagesql-skills/` and
symlinks skills from there into your agent directories — not from your working
clone. If you used the quick installer, your agent reads that managed copy, not
your working branch.

To test local changes, re-point the Claude Code symlink directly to your clone:

```bash
rm ~/.claude/skills/vsql-extension-builder
ln -s ~/code/villagesql-skills/skills/vsql-extension-builder ~/.claude/skills/vsql-extension-builder
```

Branch switches are then live immediately. When you're done, re-running the
quick installer restores the managed copy.

If you add a new file to `references/`, call it out in your PR description —
a maintainer will update the quick-install script to include it.

## License

Apache-2.0 — see [`LICENSE`](LICENSE).

## Links

- VillageSQL: <https://villagesql.com>
- Documentation: <https://villagesql.com/docs>
- Discord: <https://discord.gg/KSr6whd3Fr>
