# Cross-Harness Skill Parity

A skill must carry the same **intent, knowledge, BDD/Gherkin acceptance,
and observable behavior** across Claude Code and Codex. Only the
*implementation* adapts to each harness (tools, APIs, self-perpetuation
primitive). A "trimmed variant" in `skills-codex/` is a parity defect,
not a legitimate baseline.

`scripts/audit-codex-parity.sh` passing is **necessary, not sufficient.**
It checks structural drift against the established baseline — but if that
baseline itself was a trimmed copy (9 of 19 reference files, missing
whole mechanisms), the audit silently approves the gap.

## When This Fires

| Signal | Action |
|---|---|
| Editing `skills/<n>/SKILL.md` and there's a Codex twin at `skills-codex/<n>/` | Verify knowledge parity by diffing references/ — not just the audit script |
| Adding a new `references/*.md` to the Claude-side skill | Decide: port (harness-adapted) or omit-with-justification |
| `audit-codex-parity.sh` green after a substantial Claude-side edit | Audit is satisfied; knowledge parity is a separate question |
| Need to add metadata (e.g. `practices:`, `metadata:`) to `skills-codex/<n>/SKILL.md` | Stop — codex frontmatter is strict |

## The Strict-Frontmatter Rule (Codex Twins)

`skills-codex/*/SKILL.md` files are enforced to have **ONLY two
frontmatter keys: `name` and `description`.** Adding any other key
(`practices:`, `metadata:`, `hexagonal_role:`, etc.) fails
`scripts/validate-codex-generated-artifacts.sh` with:

```
<skill> has non-Codex frontmatter fields: <key>
```

The check is regex-driven on the frontmatter block, not config-driven —
you can't override it per-skill.

### How to extend Claude-side metadata without breaking Codex

1. Edit `skills/<n>/SKILL.md` only (Claude side).
2. Run `scripts/regen-codex-hashes.sh`. This updates
   `skills-codex/<n>/.agentops-generated.json` markers (specifically
   `source_hash`) **WITHOUT** touching `skills-codex/<n>/SKILL.md`
   content.
3. The marker's `source_hash` records that Claude-side content drifted;
   codex content stays stable.

The pre-push gate `agentops-core.distribution-install-update` canary
will fail with N errors (one per affected twin) if you violate this.

## Evidence (anchored)

> "**`audit-codex-parity.sh` passing is NOT knowledge parity.** It checks
> structural drift against the *established baseline* — and the codex
> evolve skill's baseline was a trimmed 9-of-19-reference-files variant.
> A green parity audit silently accepted a skill that omitted whole
> mechanisms (convergence, healing-first classifier, hypothesis
> tracking)."
— `.agents/learnings/2026-05-16-cross-harness-skill-parity.md`
(soc-y5vh.8 retro)

> "a skill must carry the same intent, knowledge, BDD/Gherkin, and
> behavior across Claude Code and Codex. Only the *implementation*
> adapts to each harness (tools, APIs, self-perpetuation primitive —
> e.g. Claude `ScheduleWakeup` non-re-arm vs Codex Step 7 `while`-loop
> break). A 'trimmed variant' is a parity defect, not a legitimate
> baseline."
— `.agents/learnings/2026-05-16-cross-harness-skill-parity.md`

> "Initially mirrored `practices:` into all 13 codex twins; pre-push
> gate's `agentops-core.distribution-install-update` canary failed with
> 13 `non-Codex frontmatter fields: practices` errors. Reverted codex
> twins; re-ran regen; gate passed."
— `.agents/learnings/2026-05-10-codex-frontmatter-is-strict-name-description.md`
(soc-hdot pass-1)

## How To Apply

### When editing a Claude-side skill

1. **Make the edit on the Claude side first.** `skills/<n>/SKILL.md` and
   `skills/<n>/references/`.
2. **Diff the references/ directory** against the Codex sibling:
   ```bash
   diff <(ls skills/<n>/references/) <(ls skills-codex/<n>/references/ 2>/dev/null)
   ```
3. **For each file in the Claude-side but not the Codex-side:** decide
   to port (with harness adaptation) or omit (with a comment in
   `skills-codex-overrides/<n>/` explaining why).
4. **Regenerate codex hashes:** `scripts/regen-codex-hashes.sh`.
5. **Verify both gates:**
   ```bash
   bash scripts/audit-codex-parity.sh --skill <n>
   bash tests/skills/lint-skills.sh
   ```

### When adding a NEW reference file Claude-side

Default: port to the Codex side as a harness-adapted copy. Justify
omission only when the reference is fundamentally Claude-specific (e.g.,
`ScheduleWakeup` mechanics, `Skill()` tool semantics). Document the
justification in `skills-codex-overrides/<n>/.parity-omissions.md` if
one exists, or as a comment in the relevant `skills-codex/<n>/...` file.

### When tempted to add frontmatter to a Codex twin

Don't. Edit Claude-side only; let `regen-codex-hashes.sh` track drift.
If you genuinely need Codex-specific metadata, put it in
`skills-codex-overrides/<n>/` as a separate file, not in the SKILL.md
frontmatter.

## Implementation Adaptations That Are Legitimate

These are NOT parity defects — they're the *implementation* layer
adapting to each harness:

| Concept | Claude Code | Codex |
|---|---|---|
| Self-perpetuation | `ScheduleWakeup` (non-re-arm) | Step 7 `while`-loop break |
| Tool invocation | `Skill(skill="x")`, `Agent(...)` | inline shell + filesystem |
| Background work | `Bash(run_in_background=true)` + `Monitor` | nohup / disown |
| File state | `Read`/`Edit`/`Write` tools | direct filesystem |
| Memory loop | `~/.claude/projects/.../memory/` | session JSONL parse |

What MUST be the same: intent (what the skill is for), knowledge (the
references that explain the mechanism), Gherkin acceptance (the BDD
scenarios), and observable behavior (the final artifact a session
produces).

## Why The Audit Alone Isn't Enough

`audit-codex-parity.sh` enforces:
- `skills-codex/<n>/SKILL.md` exists if `skills/<n>/SKILL.md` exists
- The `name` field matches
- The `source_hash` in `.agentops-generated.json` matches the current
  Claude-side hash (when codex was last regenerated)

It does NOT enforce:
- That the `description` captures the same intent
- That the `references/` directory has structurally-equivalent files
- That the Codex twin actually implements the same workflow

The trimmed-baseline failure mode is invisible to the audit. The fix is
a **knowledge-parity check** — read both sides, confirm same intent,
same references (or justified omissions), same Gherkin. Broader
reconciliation tracked in `[[soc-an3v]]` (per the retro).

## See Also

- `scripts/audit-codex-parity.sh` — the structural audit
- `scripts/regen-codex-hashes.sh` — drift marker regenerator
- `scripts/validate-codex-generated-artifacts.sh` — the strict-frontmatter
  enforcer
- `skills-codex-overrides/<n>/` — where genuine Codex-side deviations live
- `docs/contracts/claude-bot-delegation.md` — the bot-permissions parity
  layer (orthogonal to skill parity)
