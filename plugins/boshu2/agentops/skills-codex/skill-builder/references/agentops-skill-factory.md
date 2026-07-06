# AgentOps Skill Factory Productization

This reference captures the local Codex `agentops-skill-factory` prototype as a
repo workflow. The goal is not to ship the local prototype verbatim; the goal is
to fold its proven behavior into the existing `skill-builder` and
`skill-auditor` pair.

## Clean-room Inputs

Use only AgentOps-owned artifacts:

- `docs/reference/skill-quality-rubric.md`
- `skills/standards/references/skill-structure.md`
- `skills/standards/references/external-source-attribution.md`

Do not copy protected third-party skill prose, prompts, scripts, names, or
examples into AgentOps skills. Extract reusable structure and quality signals
only.

## Factory Loop

1. Start with the built-in Codex skill-creator shape: a short `SKILL.md` kernel,
   progressive disclosure through `references/`, reusable `scripts/`, optional
   `assets/`, and validation evidence.
2. Score the target skill:

   ```bash
   python3 skills/heal-skill/scripts/score_agentops_skill.py skills/<name> --markdown
   ```

3. Pick the smallest score-improving patch, usually one of:
   - add or link `SELF-TEST.md`;
   - move bulky context into `references/`;
   - add a focused validation script;
   - add an output contract or explicit quality rubric;
   - tighten trigger language in frontmatter and body.
4. Re-run `skill-auditor`, `heal-skill --check --strict`, and any target-specific
   validation by exit code, not by grepping output text.
5. Mirror behavior into `skills-codex/<name>/` or
   `skills-codex-overrides/<name>/` when the Codex runtime needs different
   phrasing or execution instructions.

## Scale Run Discipline

When authoring multiple skills, protect file ownership before parallelism:

- One skill equals one worker equals one source directory plus its Codex mirror.
- Run create-only work first; mutate existing skills only after the source corpus
  is settled.
- Use deterministic scripts or NTM/Agent Mail lanes for batch work. Do not use
  the Workflow tool as the skill factory.
- Trust `git status`, generated hashes, final file contents, and gate exit codes
  over worker self-reports.
- Clean-room review includes exact names. Rename third-party-derived labels into
  AgentOps-owned names before source skills, Codex mirrors, or wrappers are keyed.

## Productization Rule

Local prototype skills may guide the workflow, but PRs should land durable
AgentOps artifacts:

- source skill changes under `skills/`;
- Codex runtime changes under `skills-codex/` or `skills-codex-overrides/`;
- reusable scoring/audit scripts under `skills/heal-skill/scripts/`;
- clean-room standards under `docs/reference/` and `skills/standards/`.

Avoid adding a duplicate top-level skill when an existing AgentOps skill already
owns the domain. Extend `skill-builder`, `skill-auditor`, `rpi`, or `evolve`
instead.
