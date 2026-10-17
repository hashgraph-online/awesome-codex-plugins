# codebase-recon-skill

A coding agent skill that analyzes git history to understand a codebase before reading any code. Reveals project health, risk areas, team structure, and development momentum.

Inspired by ["The Git Commands I Run Before Reading Any Code"](https://piechowski.io/post/git-commands-before-reading-code/) by [Ally Piechowski](https://github.com/grepsedawk).

## Installation

### Via skills.sh (works with 20+ coding agents)

```sh
npx skills add yujiachen-y/codebase-recon-skill
```

Works with Claude Code, Cline, Cursor, GitHub Copilot, Gemini CLI, and any agent supporting the [Agent Skills Specification](https://agentskills.io/specification).

### Via Claude Code plugin system

```
/plugin marketplace add yujiachen-y/codebase-recon-skill
```

Then install the plugin from the marketplace browser via `/plugin`.

### Via Codex plugin system

```sh
codex plugin marketplace add yujiachen-y/codebase-recon-skill
```

Then run `/plugins` in Codex, choose the `Codebase Recon` marketplace, and install `codebase-recon`.

## Usage

In your coding agent, invoke:

```
/codebase-recon
```

The skill will:
1. **Probe** the repo to determine its scale (small / medium / large)
2. **Analyze** 7 dimensions in parallel: code hotspots, bus factor, bug magnets, team momentum, firefighting frequency, recently added files, and active contributors
3. **Cross-reference** hotspots with bug magnets to identify high-risk files
4. **Report** findings with actionable recommendations

## What You'll Learn

| Dimension | Question Answered |
|-----------|-------------------|
| Code Hotspots | Which files change the most? |
| Bug Magnets | Which files attract the most bug fixes? |
| High-Risk Files | Which files are both hot AND buggy? |
| Bus Factor | Who knows what? Is knowledge concentrated? |
| Team Momentum | Is development accelerating, stable, or declining? |
| Firefighting | How often are there emergency fixes and reverts? |
| Recently Added | Where is active development happening? |

## Requirements

- `git` (any version)
- A git repository with commit history

## Attribution

This skill is inspired by ["The Git Commands I Run Before Reading Any Code"](https://piechowski.io/post/git-commands-before-reading-code/) by [Ally Piechowski](https://github.com/grepsedawk). The original article describes 5 git commands for codebase reconnaissance. This skill extends the concept with auto-scaling, cross-referencing, and actionable recommendations.

## License

[MIT](LICENSE)
