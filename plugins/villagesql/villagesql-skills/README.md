# villagesql-skills

Agent skills for working with [VillageSQL](https://villagesql.com). Skills run
in Claude Code, Gemini CLI, agy, Codex, Cursor, Amp, and Kiro.

## Skills

| Skill | What it does |
|---|---|
| [`vsql-extension-builder`](skills/vsql-extension-builder/) | Builds a VillageSQL extension end-to-end through a 7-phase persona-driven workflow. Discovers the current VEF API from live SDK headers — no hardcoded API names. |

More skills will be added here over time.

## Installing

### Quick install

```bash
curl -sSL https://villagesql.com/skills | bash
```

Detects which agents are installed and configures each one. Supports Claude
Code, Gemini CLI, agy, Codex, Cursor, Amp, and Kiro. Re-running updates
in place.

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

#### Gemini CLI

```bash
git clone https://github.com/villagesql/villagesql-skills.git ~/code/villagesql-skills
mkdir -p ~/.gemini/extensions
ln -s ~/code/villagesql-skills ~/.gemini/extensions/villagesql
```

Gemini CLI reads `gemini-extension.json` and loads `GEMINI.md` as context.

#### agy

```bash
git clone https://github.com/villagesql/villagesql-skills.git ~/code/villagesql-skills
mkdir -p ~/.gemini/antigravity-cli/plugins
ln -s ~/code/villagesql-skills ~/.gemini/antigravity-cli/plugins/villagesql
```

agy reads `plugin.json` and discovers skills from the `skills/` subdirectory.

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

If you add a new file to `references/`, also update the install script in
`villagesql-website/src/skills` so it gets included for users of the quick
installer.

## License

Apache-2.0 — see [`LICENSE`](LICENSE).

## Links

- VillageSQL: <https://villagesql.com>
- Documentation: <https://villagesql.com/docs>
- Discord: <https://discord.gg/KSr6whd3Fr>
