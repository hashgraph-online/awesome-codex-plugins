# Waivers and Baselines

Read this rule when using detector baseline output, interpreting a waiver, or documenting report-only CI.

## Baselines

- A baseline is a saved `detect-slop.sh` v2 JSON result used only to compare known static findings with a later scan.
- Run `--only-new` only with an explicit `--baseline <result.json>`; malformed or incompatible baselines block the comparison.
- A baseline is debt visibility, not approval. It does not turn an existing finding into a visual, accessibility, or remediation pass.
- The detector never creates, rewrites, or broadens a baseline. Consumer projects own their local baseline file.

Example report-only command, run from this skill's folder:

```bash
bash scripts/detect-slop.sh \
  --target <project>/src --baseline <project>/.ai-slop-remover-baseline.json --only-new --json
```

Do not make this command block CI, install dependencies, or mutate project configuration unless the user or project authority explicitly requires that effect.

## Narrow waivers

An optional `.ai-slop-remover.json` may document one sanctioned value or one rule in one file. Validate it with `scripts/validate-waivers.sh` before relying on it.

Every waiver requires a known `ruleId`, exactly one of `value` or `file`, a non-empty reason, and a source: `user-confirmed`, `documented-brand`, `fixture`, or `generated-output`. `reviewAfter`, when present, uses an absolute `YYYY-MM-DD` date.

Waivers never:

- create or modify configuration automatically
- suppress every rule across a project
- hide a P0, protected-contract failure, or unresolved source/behavior defect
- replace a user decision when the exception is not documented

Prefer a value waiver for an explicit brand font/gradient and a file waiver only for generated, exported, or deliberate demonstration files. A source-local `ai-slop-disable-next-line <rule> -- <reason>` marker is documentation-only guidance for portable generated output; this skill does not write markers automatically.

## Sources

> Claims checked 2026-09-21. No external source was used in this file.

The baseline and waiver rules are this package's own contract for its bundled detector and waiver validator. The `ai-slop-disable-next-line` marker shape is documented package guidance, not an external standard.
