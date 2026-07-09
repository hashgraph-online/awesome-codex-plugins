# Standards Skill Self-Test

## Trigger Cases

- User says: "audit this skill against AgentOps skill structure standards."
  - Expected: load `standards` as a library skill and use `references/skill-structure.md`.

- User says: "validate this Go change against repo standards."
  - Expected: load `standards` and use `references/go.md`.

- User says: "check whether this skill can absorb an external corpus safely."
  - Expected: load `references/external-source-attribution.md` and apply its clean-room policy when applicable.

## Non-Trigger Cases

- User asks to implement a feature with no files or language context.
  - Expected: do not load every standards reference; wait until file types or risk patterns are known.

- User asks for general product strategy.
  - Expected: use product/discovery skills, not `standards`, unless code or skill standards become relevant.

## Behavior Checks

- `standards` stays a library skill and writes no artifacts by itself.
- Language standards load on demand by file type rather than all at once.
- Domain checklists load only when matching risk patterns are present.
- External-source absorption follows `references/external-source-attribution.md`.
- Skill authoring and export guidance points to `references/skill-structure.md`.

## Validation Commands

Run from the repo root:

```bash
bash skills/standards/scripts/validate.sh
bash skills/heal-skill/scripts/heal.sh --strict
bash scripts/validate-skill-frontmatter.sh --strict
```

## Failure Cases

- Missing reference file: fail skill validation and restore the missing file or remove the link from `SKILL.md`.
- Wrong standard selected: identify the file type or risk detector that selected it and update the relevant loading rule.
- External corpus content copied verbatim: stop, remove copied content, and keep only pattern-level observations with attribution.
