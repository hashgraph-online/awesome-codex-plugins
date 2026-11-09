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

## Project configuration

`--config <file.json>` points the detector at one project configuration document, validated against `assets/detector-config.schema.json`. The file is optional; without it the detector behaves exactly as before.

```json
{
  "version": 1,
  "rules": { "surface.radial-glow": "off", "copy.cliche": "P1" },
  "allowFonts": ["BrandMono"],
  "allowEasings": ["cubic-bezier(0.2, 0.6, 0.2, 1)"],
  "designTokens": { "--brand-mono": "BrandMono" }
}
```

- `rules` maps a rule id to `off`, `P1`, `P2`, or `P3`. `off` removes the rule from the scan; a severity value replaces the registry default in the report.
- `--rules <id,id>` narrows one run to the named rule ids and exits 2 on an unknown id; it selects, it never re-enables a rule the config turned `off`. The catalogue's Static column decides which ids exist: only `yes` and `partial` rows are registered (`references/anti-pattern-catalog.md`).
- `motion.missing-reduced-motion` is a project-wide rule the detector evaluates across the whole scan rather than per file; it is selected, disabled, and severity-overridden like any other id.
- `allowFonts`, `allowEasings`, and `designTokens` are allowlists. A finding whose matched excerpt contains an allowlisted value moves to the skipped count instead of the findings list.
- `data-detect-ignore="<rule-id>"` (or `*`) on a markup element exempts that element's span for the named rule. Its hits move to the skipped count, so exemptions stay visible.
- The JSON report carries a top-level `skipped` count only when `--config` was used.
- An invalid configuration exits 2 with a schema error and runs no rule. A missing or malformed file exits 2 the same way.

Config is not a waiver: it changes what the project asked for, while a waiver documents one sanctioned exception with a source and a reason. A configuration file never suppresses P0, hides a protected-contract failure, or replaces a user decision.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Per-rule severity overrides, font and easing allowlists, design-token allowlists, and a per-element ignore attribute for a slop detector | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |
| The baseline and waiver rules, the `off\|P1\|P2\|P3` value set, and the `skipped` report field | this package's own contract for its bundled detector and waiver validator |

### Evidence grade

The mechanism idea is drawn from an unlicensed reference and was re-implemented here; no text or code was reused. The schema, the value set, and the `skipped` field are this package's own contract and are exercised by `assets/evals/detector-cases.jsonl`.
