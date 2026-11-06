# Public Install Guidance

Read this file only when the user asks how to install, update, or subset the
Suede pack. It changes nothing about how work is routed or executed.

## Claude Code

Add the marketplace and install the pack:

```bash
/plugin marketplace add JasonColapietro/suede-creator-skills
/plugin install suede-skills@suede
```

`suede-skills` installs every skill. Smaller subsets:
`/plugin install suede-agent-workflows@suede` (orchestration, workflows,
evals) or `/plugin install suede-code@suede` (review, grade, ship-gate).

Prefer a clone? `install.sh` copies every skill into `~/.claude/skills/`:

```bash
git clone https://github.com/JasonColapietro/suede-creator-skills.git && bash suede-creator-skills/install.sh
```

## Codex

Install the umbrella skill alone:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo JasonColapietro/suede-creator-skills \
  --path skills/suede-workflow-skills
```

That path is the umbrella-only configuration: the individual specialists are
absent, so the umbrella falls back to `references/condensed-workflows.md`.
Install the individual skills whenever direct triggering matters: pass any
number of `skills/<name>` paths after `--path`:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo JasonColapietro/suede-creator-skills \
  --path skills/suede-copy \
  skills/suede-deslop \
  skills/suede-ship-copy \
  skills/suede-design \
  skills/suede-component-lab \
  skills/suede-interface-explain \
  skills/suede-code \
  skills/suede-ci-gate \
  skills/suede-agent-teams \
  skills/suede-graph-flo-xr \
  skills/suede-ai-eval \
  skills/suede-parity-contract \
  skills/suede-seo-audit \
  skills/suede-visibility-grader \
  skills/suede-site-alchemy \
  skills/suede-launch-packaging \
  skills/site-to-ios-app \
  skills/android-app-factory
```

Growth, marketing, and creator
skills install the same way: substitute their directory names from
[the repository skill index](https://github.com/JasonColapietro/suede-creator-skills/tree/main/skills),
which is the current source of truth for the full list.

Restart Codex after installing new skills.

Keeping a skill under this repository's `skills/` directory prepares it for
future full-pack distribution. Editing those files does not activate the skill
globally or copy it into an agent's installed skill directory. Installation is
a separate, explicitly requested action.
