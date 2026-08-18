---
name: add
description: 'Register a deferred decision in the debt registry. Trigger by judgment, not a marker scan, whenever a future reader would ask "why this way?": an unmade decision, stub, loosened type, bypassed check, swallowed error, a default picked "for now", or a TODO/FIXME/HACK/XXX marker. Trigger immediately whenever you defer work, or when the user invokes $add. Over-register freely; the developer drops with "drop A", "drop A,C", or "drop all".'
---

# add — register a tech-debt entry

Call the bundled `register.py` via Bash — it lives in this skill's `scripts/` directory, so reference it with the relative path below (Codex resolves it against the skill root). The helper writes the entry under the repo's detected registry dir (default `docs/debt/`), assigns a short batch letter (A, B, C…), and prints exactly one line: `+1 entry: <slug> (<letter>)`. That stdout IS the user-facing announcement — add no commentary before or after.

## The call

```bash
python3 scripts/register.py \
  --slug <slug> \
  --principal <effort, e.g. 2d, 1w, unknown> \
  --interest <ongoing cost, e.g. "+30min/incident", unknown> \
  --hotspot <path or module, e.g. pricing/engine.ts, unknown> \
  --business-capability <e.g. checkout, billing, unknown> \
  --payoff-trigger <concrete trigger, or "unknown"> \
  --quadrant <reckless-inadvertent|reckless-deliberate|prudent-inadvertent|prudent-deliberate> \
  --category <migration|documentation|testing|code_quality|dead_code|code_rot|expertise|release|infrastructure|planning> \
  --ai-authored <true|false> <<'EOF'
<body: 2-5 sentences — what the debt is, why it exists, observed symptoms>
EOF
```

The helper:
- Generates the timestamp `id` itself (no `date` call needed).
- Resolves filename collisions when two registrations land in the same second.
- Tracks the letter mapping in `~/.cache/debt-ops/cache/<repo-hash>/current-turn.txt` (override the base with `DEBT_OPS_CACHE`) so the user can drop by letter.

## Slug

1–4 word kebab-case label of what the debt is. Examples: `cancelled-promotion-callback`, `legacy-auth-shim`, `unfinished-rate-limiter`. Keep it short — the body carries the context.

## Schema notes

- **Quadrant** (Fowler): `reckless-inadvertent` (didn't know better), `reckless-deliberate` (knew, did it anyway), `prudent-inadvertent` (learned afterward), `prudent-deliberate` (deliberate, with a payoff plan).
- **Category** (Google / Jaspan-Green): pick the closest match.
- **payoff_trigger: unknown** is first-class. Don't manufacture a trigger to fill the field — `unknown` ages into stale review and that's the point.
- **ai_authored: true** is the leading behavioral signal — be honest.

## Drops

- `drop A`, `drop A,C`, `drop all` — the user types this; a UserPromptSubmit hook deletes the matching entries and surfaces a one-line confirmation. You don't act on those.
- `drop it` or `drop <slug>` — you delete it yourself: `rm <registry-dir>/<id>-<slug>.md` (the registry dir named in Discipline 3; default `docs/debt/`). Treat dropping as cheap — over-registering is the intended posture.

## Don't

- Don't ask the developer for confirmation before writing. Discipline 1 says "no permission prompt; just do it."
- Don't write the file directly with an editor tool — letter assignment depends on going through `register.py`.
- Don't echo or paraphrase the helper's output. The Bash tool result is already visible to the user.
- Don't fill `payoff_trigger` with a guess to seem certain.
