# New-Skill Landing — the six derived surfaces

Adding or modifying a skill regenerates **six derived surfaces**, each gated by CI. Regenerating them piecemeal is the dominant fix-and-repush cause (the 2026-05-29 `/crank` re-land needed 3 rounds; the codex-desc-budget fix needed 1). Regenerate them in **one shot** before opening the PR.

## The shortcut

`scripts/regen-all.sh` covers surfaces 1–3 + the CLI reference in one pass — prefer it over running the generators individually. Then run the codex + count steps below.

## Live skill edits

When an agent edits an existing live skill at `skills/<slug>/SKILL.md`, seal the
edit before the next cycle hands off:

```bash
ao skills edit seal --skill <slug> --actor "${AGENT_NAME:-agent}"
```

That command stages the skill's source directory and any matching Codex skill
directory, creates a git rollback point, and records `Skill-Edit` trailers in
the commit body. Critical skills listed in
`docs/contracts/critical-skills.txt` reject unattended edits; rerun with
`--allow-critical` only for a human-supervised critical edit.

Daily operator review uses:

```bash
ao skills edit digest --since "24 hours ago"
```

The digest is the lightweight immune-system surface for "what did agents teach
the runtime today?" A live edit seal does not replace the derived-surface work
below: new skills, renames, metadata changes, and publication-bound edits still
need the full six-surface regeneration.

## The six surfaces

1. **registry.json (SKU catalog)** — `scripts/generate-registry.sh` (verify with `--check`). **The most-missed surface**: a stale `registry.json` trips `contracts-sync` ("registry.json is stale") AND `correctness(ubuntu)` ("SKU_CATALOG: DRIFT") *together*. As of ag-ekyq, `skills/skill-builder/scripts/init.sh` regenerates it automatically during scaffold; regenerate by hand for any out-of-band skill edit.
2. **skill-domain-map** — `scripts/generate-skill-domain-map.sh` (narrative `N skills` count + per-skill row; verify `--check`).
3. **context-map** — `scripts/generate-context-map.sh` (hex roles from frontmatter; CI gate `validate-context-map-drift`).
4. **skill counts** — `scripts/sync-skill-counts.sh`. **The `SKILL-TIERS.md` row must be added by hand** — `sync-skill-counts` only syncs the *counts* across PRODUCT/ARCHITECTURE/SKILLS; it never adds the row.
5. **codex twin** — `scripts/register-new-codex-skill.sh <name> --treatment parity_only|bespoke --reason "…"` (manifest entry + override-catalog + `.agentops-generated.json` marker, atomic + idempotent). Then **hand-author `skills-codex/<name>/prompt.md`** — codex twins are MANUAL; `regen-all.sh` does NOT generate them. Re-run `scripts/regen-codex-hashes.sh` afterward (adding `prompt.md` changes the tree hash). Parity_only minimal `prompt.md` = title + description + an `## Instructions` block ("Load and follow the sibling `SKILL.md`").
6. **narrative skill counts** — `scripts/check-registry-drift.sh --fix-counts` (the `N skills` lines in `agentops-skill-domain-map.md` + `agentops-domain-evolution-bdd.md`).

## Embedded sync

If the edit touches `skills/**` content that is embedded (e.g. `using-agentops`), run `cd cli && make sync-hooks` so `cli/embedded/skills/...` stays in sync — else the `codex artifact metadata`/embedded-drift gate fails.

## See also

- [gate-hygiene.md](gate-hygiene.md) — pre-push diff-scope check + pre-existing-vs-mine red triage (the companion discipline that keeps a new-skill PR one-shot-green).
