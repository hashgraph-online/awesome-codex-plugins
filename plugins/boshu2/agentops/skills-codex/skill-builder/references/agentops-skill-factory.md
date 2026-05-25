# AgentOps Skill Factory Productization

This reference captures the local Codex `agentops-skill-factory` prototype as a
repo workflow. Productize the behavior through the existing `skill-builder` and
`skill-auditor` surfaces rather than shipping the local prototype verbatim.

## Clean-room Inputs

Use only AgentOps-owned artifacts:

- `docs/reference/skill-quality-rubric.md`
- `skills/standards/references/skill-structure.md`
- `skills/standards/references/external-source-attribution.md`

Do not copy protected third-party skill prose, prompts, scripts, names, or
examples into AgentOps skills. Extract reusable structure and quality signals
only.

## Factory Loop

1. Start with the Codex skill-creator shape: short kernel, progressive
   disclosure through `references/`, reusable `scripts/`, optional `assets/`,
   and validation evidence.
2. Score the target skill:

   ```bash
   python3 skills-codex/skill-auditor/scripts/score_agentops_skill.py skills/<name> --markdown
   ```

3. Pick the smallest score-improving patch: `SELF-TEST.md`, linked references,
   focused scripts, output contracts, quality rubric, or clearer triggers.
4. Re-run `skill-auditor`, `heal-skill`, and target validation.
5. Mirror runtime-specific behavior into `skills-codex/` or
   `skills-codex-overrides/`.

## Productization Rule

Local prototype skills may guide the workflow, but PRs should land durable repo
artifacts. Avoid adding a duplicate top-level skill when an existing AgentOps
skill already owns the domain.
