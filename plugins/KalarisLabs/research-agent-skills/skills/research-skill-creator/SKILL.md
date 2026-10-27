---
name: research-skill-creator
description: Create, improve and test agent skills for research workflows (paper writing, lab protocols, analysis pipelines, domain databases) that meet the Agent Skills specification and this repository's quality and security bar. Use when turning a repeated research task into a reusable skill, contributing a new skill to Research Agent Skills, rewriting an existing skill, writing trigger-accurate descriptions, or adding evals. Works alongside Anthropic's official skill-creator.
license: MIT
compatibility: Python 3.9+ for the scaffold script. Repository validators need uv. Anthropic's skill-creator (optional) provides the eval loop.
metadata:
  version: "1.0"
  category: research-automation
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: skill authoring, agent skills, SKILL.md, evals, contributing
---

# Research Skill Creator

A good research skill packages *procedural knowledge an expert would otherwise
have to explain every time*: the order of steps, the checks that catch mistakes,
the venue- or instrument-specific rules. It is not a textbook chapter and not a
wrapper around one API call.

## 0. Install the official tooling (once)

Anthropic's `skill-creator` supplies the eval loop, description optimizer and
packager. In Claude Code:

```text
/plugin marketplace add anthropics/skills
/plugin install example-skills@anthropic-agent-skills
```

Use it to run evals (`run_eval.py`, `run_loop.py`) and to tune the description
(`improve_description.py`). This skill adds the research-specific conventions.

## 1. Decide whether it should be a skill

Create a skill when **all** hold:
- The task recurs across projects or people (not a one-off script).
- Doing it well requires non-obvious steps, checks or domain rules.
- An agent would plausibly get it wrong without guidance (test this: ask without the skill first).

Otherwise write a note or a script instead. Check `catalog/skills.json` for overlap and
extend an existing skill rather than creating a near-duplicate.

## 2. Scaffold

```bash
python skills/research-skill-creator/scripts/new_skill.py rebuttal-letter \
  --category research-writing \
  --description "Draft point-by-point responses to peer reviewers. Use when ..." \
  --scripts --references
```

This writes `skills/<name>/SKILL.md` with spec-compliant frontmatter and `evals/<name>/evals.json`.

## 3. Write the description (it decides whether the skill is ever used)

- Say **what it does** and **when to use it**, with the words users actually type:
  "journal cover letter", "response to reviewers", "PRISMA flow diagram".
- Name concrete artifacts, tools and venues ("BibTeX", "Nature", "pgvector").
- At most 1024 characters, third person, no angle brackets, no marketing adjectives.
- Add "Use when ..." clauses for the 3-6 most common triggers, plus distinguishing
  cues vs. sibling skills (e.g. "for systems venues use systems-paper-writing").

## 4. Write the body

| Principle | Practice |
|---|---|
| Procedure over prose | Numbered workflows, decision tables, checklists |
| Progressive disclosure | SKILL.md under 500 lines; long material in `references/*.md`, linked with one-line "read when" hints |
| Deterministic work in code | Parsing, validation and conversion go in `scripts/`, which the agent runs rather than re-implements |
| Verify-first for facts that change | Venue limits, API versions, guidelines: tell the agent to fetch the official source and cite it |
| Honesty rules | Explicit "never fabricate data, citations or results; say when unverifiable" |
| Handoffs | End with related skills and when to switch |

## 5. Scripts: the repository contract

- Python 3.9+ **standard library** unless a dependency is essential. Declare it in `compatibility`.
- `argparse` CLI with `--help`, a docstring with usage, exit codes `0` ok, `1` findings, `2` bad input.
- UTF-8 console setup (the scaffold includes it) so Windows terminals don't crash.
- Network calls only to documented APIs. Every new domain must be added to
  `security/allowed-domains.txt` with a reviewer's approval. Set a descriptive `User-Agent`.
- Never read credentials beyond the env var the user configures for that service. Never
  exfiltrate environment data. No `eval`/`exec` of fetched content. Never pipe downloaded scripts into a shell.

## 6. Test

1. `uv run tools/validate.py skills/<name>`: spec + repo policy.
2. `uv run tools/lint_injection.py skills/<name>`: prompt-injection and payload lint.
3. Fill `evals/<name>/evals.json` with 3-10 realistic prompts, including near-misses that
   should **not** trigger, and run them with skill-creator's eval loop. Compare with/without the skill.
4. Run each script on real sample inputs, including malformed ones, on Windows and Unix if possible.
5. `uv run tools/build_catalog.py` to regenerate the marketplace, catalog and README tables.

## 7. Rewriting an adapted skill

Skills listed in `third_party/upstream-manifest.json` with `rewrite_status: imported`
are adaptations. A rewrite must be written from scratch (new structure, new
wording, re-verified facts), not paraphrased line by line. When it merges, set
`rewrite_status: original` for that skill in the manifest. The notices generator then
drops it from `THIRD_PARTY_NOTICES.md` and the importer stops overwriting it.

## Related skills

`research-agent-skills` repository docs (`CONTRIBUTING.md`), Anthropic `skill-creator`,
`autoskill` (detects repeated workflows worth turning into skills).
