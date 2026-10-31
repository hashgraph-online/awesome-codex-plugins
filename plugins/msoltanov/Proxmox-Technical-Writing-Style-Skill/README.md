# Proxmox Writing Style Skill

This project is an AI-agent skill for the Proxmox Technical Writing Style Guide.

Use it to write, edit, or review Proxmox technical documentation with Claude, Codex, ChatGPT, opencode, Cline, Kilo Code, Aider, or another AI tool that reads instruction files.

## Status

This project is unofficial. Proxmox Server Solutions GmbH does not sponsor, endorse, or review this project. Proxmox, Proxmox VE, and related names are trademarks of their owner. For details, read [NOTICE](NOTICE).

## Install

Claude Code:

```bash
claude plugin marketplace add msoltanov/Proxmox-Technical-Writing-Style-Skill
```

```bash
claude plugin install proxmox-writing-style@proxmox-writing-style
```

Codex:

```bash
codex plugin marketplace add msoltanov/Proxmox-Technical-Writing-Style-Skill
```

```bash
codex plugin add proxmox-writing-style@proxmox-writing-style
```

For the Claude apps, ChatGPT, and other tools, read [docs/install.md](docs/install.md).

## The Skill

The skill is [skills/proxmox-writing-style/SKILL.md](skills/proxmox-writing-style/SKILL.md). It is a Markdown file with YAML frontmatter. It needs no build and no dependencies.

The folder also contains these files:

- [references/examples.md](skills/proxmox-writing-style/references/examples.md): before and after rewrites for each rule group
- [agents/openai.yaml](skills/proxmox-writing-style/agents/openai.yaml): the display name and the default prompt for Codex

## Tests

[evals/evals.json](evals/evals.json) contains test prompts and the expected results. Run each prompt with the skill installed, and compare the output with the expected result.

## Source

The rules come from the Proxmox Technical Writing Style Guide:

https://pve.proxmox.com/wiki/Technical_Writing_Style_Guide

The recorded revision is `12596`, last edited 2026-05-27 09:17.

## Support

To report a problem or to ask for a change, open an issue:

https://github.com/msoltanov/Proxmox-Technical-Writing-Style-Skill/issues

To change the skill, read [CONTRIBUTING.md](CONTRIBUTING.md). To report a security problem, read [SECURITY.md](SECURITY.md).

## License

MIT. Read [LICENSE](LICENSE).
