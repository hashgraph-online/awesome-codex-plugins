# Simple Man — Codex plugin bundle

This directory is the packaged plugin: the manifest, the skill, and the assets
that ship with them. It is a build surface, not the source of the policy —
`skills/simple-man/SKILL.md` at the repository root is canonical, and
`scripts/sync_surfaces.py` copies it here.

Do not edit files in this directory by hand. Change the source, then run:

```bash
python3 scripts/sync_surfaces.py --write
python3 scripts/sync_surfaces.py --check
```

## What the plugin does

Simple Man is a communication policy for coding agents. It removes narration,
praise and recap from answers while keeping every fact the reader acts on:
findings carry their location and one-line fix, refusals carry the missing
precondition and the safe procedure, failed checks report the exact failure,
and explicitly requested long-form output is left uncompressed.

## Install

```bash
codex plugin marketplace add Maksim-Burtsev/simple-man --ref v0.3.2
codex plugin add simple-man@simple-man
```

Installing the plugin makes the skill *available* — invoke it with
`$simple-man`, or let the agent activate it from the request. It does **not**
enable the always-on policy; only `install.sh` or a copied
`AGENTS.md.snippet` does that.

## Operational constraints

- The skill adds no tools, no network access and no permissions. It changes how
  an answer is written, nothing else.
- It deliberately does not activate on tutorials, teaching explanations or
  detailed reports, so long-form requests are unaffected.
- Requires an agent that loads Agent Skills. For non-Codex agents see
  [`INSTALL.md`](../../INSTALL.md).

Full documentation, benchmark evidence and raw records:
[github.com/Maksim-Burtsev/simple-man](https://github.com/Maksim-Burtsev/simple-man).
Security policy: [`SECURITY.md`](../../SECURITY.md). MIT licensed.
