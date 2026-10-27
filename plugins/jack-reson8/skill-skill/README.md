# skill-skill

![skill health](https://img.shields.io/badge/skill%20health-100%2F100-brightgreen)

A Claude skill for writing skills that **actually change what gets generated**, not piles of notes.

> **New: [I audited 899 public Claude skills](reports/2026-10/README.md)** ([中文](reports/2026-10/README.zh-CN.md)). Many never tell the model when to use them; fixes were sent upstream.
>
> [![Claude skill health](reports/2026-10/chart.png)](reports/2026-10/README.md)

一个用来写 skill 的 skill：让 skill 在实际生成时真正起作用，而不是堆资料。

## What it does

- **Distil from real work.** Turns the user's corrections, rejections and accepted outputs into rules and checks.
- **Forcing functions over advice.** Uses required artifacts, gates, scripts, checklists run at a named moment, and templates. References only count when a step points to them.
- **Descriptions and names that trigger.** Covers trigger phrases (including Chinese), the 1024-char limit, and collision checks.
- **Static audit** (`scripts/skill_audit.py`). Catches bad names, missing trigger clauses, name collisions, orphan reference files that nothing points to, dangling paths, oversized bodies and ALL-CAPS overuse.
- **Quick effect test.** For 2–3 real prompts, writes 3 observable effects each, then checks them with and without the skill.

## Install

In Claude Code:

```
/plugin marketplace add jack-reson8/skill-skill
/plugin install skill-skill@skill-skill
```

Or as a plain skill folder:

```bash
git clone https://github.com/jack-reson8/skill-skill /tmp/skill-skill && cp -R /tmp/skill-skill/plugins/skill-skill/skills/skill-skill ~/.claude/skills/
```

**Codex** (CLI or the ChatGPT desktop app):

```bash
codex plugin marketplace add jack-reson8/skill-skill
codex plugin add skill-skill@skill-skill
```

Or copy `plugins/skill-skill/skills/skill-skill` into `~/.codex/skills/`. The skill follows the open [Agent Skills](https://agentskills.io) standard, so it works in Claude Code, Codex and any agent that reads SKILL.md.

## Audit any skill and get a health score

```bash
python3 ~/.claude/skills/skill-skill/scripts/skill_audit.py path/to/skill   # or --all for ~/.claude/skills, --badge for a README badge
```

```
== bad-skill   15/100  ★☆☆☆☆
  ✗ name "Bad_Skill" must be lowercase-hyphen
  ✗ description has no "Use when…" trigger clause
  ✗ orphan: references/orphan.md is never mentioned in SKILL.md
  ✗ dangling path: references/missing.md
  · warn: 4 ALL-CAPS commands — explain the why instead

== pro-motion   100/100  ★★★★★
  ✓ no blocking issues

Average skill health: 92/100 across 6 skills
```

Audit any public repo into a report with a chart: `python3 scripts/skill_report.py owner/repo`.

Got a score? Put the badge in your skill's README and share it (`--badge` prints the markdown).

No dependencies beyond Python 3. For full eval benchmarks and description optimisation, pair it with Anthropic's `skill-creator`.

## FAQ

**Why doesn't Claude use my skill?** Claude decides from the `description` alone. Say what the skill does *and when to use it*, using the phrases your users actually type, and stay under 1,024 characters. `skill_audit.py` flags descriptions that miss this.

**What are the SKILL.md name rules?** A name is 1–64 lowercase letters, numbers and single hyphens, and it must match the parent folder ([Agent Skills spec](https://agentskills.io/specification)).

**How is this different from Anthropic's skill-creator?** skill-creator runs full evals and description optimisation. skill-skill is the fast path: it distils real work into forcing functions and gives a static lint in seconds. Use both.

Project page: https://jack-reson8.github.io/skill-skill/

## License

MIT
